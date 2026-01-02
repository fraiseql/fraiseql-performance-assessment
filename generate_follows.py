#!/usr/bin/env python3
import psycopg
import random

conn = psycopg.connect(
    host="localhost", port=5434, user="benchmark",
    password="benchmark123", dbname="fraiseql_benchmark"
)
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT pk_user FROM benchmark.tb_user ORDER BY pk_user")
users = [row[0] for row in cursor.fetchall()]

print(f"Found {len(users)} users. Generating follow relationships...")

follows = []

# Each user follows 5-20 other random users
for user_pk in users:
    num_follows = random.randint(5, 20)
    followed = random.sample(
        [u for u in users if u != user_pk],
        min(num_follows, len(users) - 1)
    )
    for followed_user in followed:
        follows.append((user_pk, followed_user))

cursor.executemany(
    """INSERT INTO benchmark.tb_user_follows
       (fk_follower, fk_following)
       VALUES (%s, %s)""",
    follows
)
conn.commit()
print(f"✓ Generated {len(follows)} follow relationships")

cursor.close()
conn.close()
print("\n✅ Follow relationships generation completed successfully!")
