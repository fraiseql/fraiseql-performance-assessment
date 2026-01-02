#!/usr/bin/env python3
import psycopg
import random
from datetime import datetime, timedelta

conn = psycopg.connect(
    host="localhost", port=5434, user="benchmark",
    password="benchmark123", dbname="fraiseql_benchmark"
)
cursor = conn.cursor()

# Get all users
cursor.execute("SELECT pk_user FROM benchmark.tb_user ORDER BY pk_user")
users = [row[0] for row in cursor.fetchall()]

print(f"Found {len(users)} users. Generating posts...")

# Generate posts (3-10 per user)
posts = []
post_id = 1
titles = [
    "My First Post", "Learning GraphQL", "Database Design Patterns",
    "Performance Tips", "Cloud Architecture", "Team Success Story",
    "Technical Deep Dive", "Project Updates", "Best Practices",
    "Challenges and Solutions"
]

contents = [
    "Just started exploring new technologies today.",
    "This framework is incredible for building APIs.",
    "Had a great discussion about scalability today.",
    "Excited to share what we've been working on.",
    "Learned something new about distributed systems.",
    "Our team shipped a major feature this week.",
    "Thoughts on the latest industry trends.",
    "Tips for writing better code.",
    "Celebrating our team's accomplishments.",
    "Looking forward to more innovations."
]

base_date = datetime.now() - timedelta(days=30)

for user_pk in users:
    num_posts = random.randint(3, 10)
    for i in range(num_posts):
        title = random.choice(titles)
        content = random.choice(contents)
        created = base_date + timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23)
        )
        published = random.choice([True, False])
        posts.append((
            post_id,
            f"post_{post_id}",
            user_pk,
            title,
            content,
            published,
            created,
            created
        ))
        post_id += 1

# Insert posts in batches
cursor.executemany(
    """INSERT INTO benchmark.tb_post
       (pk_post, identifier, fk_author, title, content, published, created_at, updated_at)
       OVERRIDING SYSTEM VALUE
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
    posts
)
conn.commit()
print(f"✓ Generated {len(posts)} posts")

# Generate follow relationships
print(f"Generating follow relationships...")

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
print("\n✅ Data generation completed successfully!")
