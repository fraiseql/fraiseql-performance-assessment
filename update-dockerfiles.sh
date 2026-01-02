#!/bin/bash

# Script to add TMPDIR=/data/tmp to all Dockerfiles to prevent /tmp overflow

echo "Adding TMPDIR=/data/tmp to all Dockerfiles..."

# Find all Dockerfiles in frameworks directories
find frameworks -name "Dockerfile" -type f | while read -r dockerfile; do
    # Skip vendor directories and files owned by root
    if [[ "$dockerfile" == *"vendor"* ]] || [[ $(stat -c %U "$dockerfile") == "root" ]]; then
        echo "Skipping $dockerfile (root owned or vendor)"
        continue
    fi

    echo "Updating $dockerfile..."

    # Check if TMPDIR is already set
    if grep -q "TMPDIR=/data/tmp" "$dockerfile"; then
        echo "  Already has TMPDIR set"
        continue
    fi

    # Find the FROM line and add TMPDIR after it
    sed -i '/^FROM /a \
\
# Set TMPDIR to use /data/tmp for builds to avoid /tmp filling up\
ENV TMPDIR=/data/tmp' "$dockerfile"

    echo "  Added TMPDIR environment variable"
done

echo "Done! All eligible Dockerfiles updated."