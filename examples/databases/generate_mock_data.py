import random

import mysql.connector
import psycopg2
import redis
from faker import Faker

fake = Faker()

MYSQL_CONFIG = {
    "host": "localhost",
    "port": "3306",
    "user": "root",
    "password": "mysql",
    "database": "mydatabase",
}

POSTGRES_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres",
    "database": "postgres",
}

REDIS_CONFIG = {"host": "localhost", "port": 6379, "password": "redis", "db": 0}


def generate_mysql_data():
    """Generate and insert mock data into MySQL database"""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
        )
        cursor = conn.cursor()

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        cursor.execute(f"USE {MYSQL_CONFIG['database']}")

        tables = {
            "customers": """
                CREATE TABLE IF NOT EXISTS customers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    address VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "products": """
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    description TEXT,
                    price DECIMAL(10, 2),
                    category VARCHAR(50),
                    in_stock BOOLEAN
                )
            """,
            "orders": """
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT,
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount DECIMAL(10, 2),
                    status VARCHAR(20)
                )
            """,
            "employees": """
                CREATE TABLE IF NOT EXISTS employees (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    position VARCHAR(100),
                    department VARCHAR(50),
                    salary DECIMAL(10, 2),
                    hire_date DATE
                )
            """,
            "inventory": """
                CREATE TABLE IF NOT EXISTS inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT,
                    quantity INT,
                    warehouse VARCHAR(50),
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
        }

        for table_name, create_query in tables.items():
            cursor.execute(create_query)
            print(f"MySQL: Created table {table_name}")

        for _ in range(100):
            cursor.execute(
                "INSERT INTO customers (name, email, phone, address) VALUES (%s, %s, %s, %s)",
                (fake.name(), fake.email(), fake.phone_number()[:20], fake.address()),
            )

        categories = ["Electronics", "Clothing", "Food", "Books", "Home"]
        for _ in range(100):
            cursor.execute(
                "INSERT INTO products (name, description, price, category, in_stock) VALUES (%s, %s, %s, %s, %s)",
                (
                    fake.catch_phrase(),
                    fake.text(max_nb_chars=200),
                    round(random.uniform(10, 1000), 2),
                    random.choice(categories),
                    random.choice([True, False]),
                ),
            )

        positions = ["Manager", "Developer", "Designer", "Analyst", "HR", "Sales"]
        departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
        for _ in range(100):
            cursor.execute(
                "INSERT INTO employees (name, position, department, salary, hire_date) VALUES (%s, %s, %s, %s, %s)",
                (
                    fake.name(),
                    random.choice(positions),
                    random.choice(departments),
                    round(random.uniform(30000, 150000), 2),
                    fake.date_between(start_date="-5y", end_date="today"),
                ),
            )

        statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
        for _ in range(100):
            cursor.execute(
                "INSERT INTO orders (customer_id, total_amount, status) VALUES (%s, %s, %s)",
                (
                    random.randint(1, 100),
                    round(random.uniform(50, 5000), 2),
                    random.choice(statuses),
                ),
            )

        warehouses = ["North", "South", "East", "West", "Central"]
        for _ in range(100):
            cursor.execute(
                "INSERT INTO inventory (product_id, quantity, warehouse) VALUES (%s, %s, %s)",
                (
                    random.randint(1, 100),
                    random.randint(0, 1000),
                    random.choice(warehouses),
                ),
            )

        conn.commit()
        print("MySQL: Successfully inserted mock data")

    except mysql.connector.Error as e:
        print(f"MySQL Error: {e}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


def generate_postgres_data():
    """Generate and insert mock data into PostgreSQL database"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        conn.autocommit = True

        tables = {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50),
                    email VARCHAR(100),
                    password_hash VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN
                )
            """,
            "posts": """
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER,
                    title VARCHAR(200),
                    content TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    views INTEGER DEFAULT 0
                )
            """,
            "comments": """
                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER,
                    user_id INTEGER,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "categories": """
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50),
                    description TEXT
                )
            """,
            "tags": """
                CREATE TABLE IF NOT EXISTS tags (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(30),
                    color VARCHAR(7)
                )
            """,
        }

        for table_name, create_query in tables.items():
            cursor.execute(create_query)
            print(f"PostgreSQL: Created table {table_name}")

        for _ in range(100):
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, is_active) VALUES (%s, %s, %s, %s)",
                (
                    fake.user_name(),
                    fake.email(),
                    fake.sha256(),
                    random.choice([True, False]),
                ),
            )

        for _ in range(100):
            cursor.execute(
                "INSERT INTO posts (user_id, title, content, views) VALUES (%s, %s, %s, %s)",
                (
                    random.randint(1, 100),
                    fake.sentence(),
                    fake.text(max_nb_chars=500),
                    random.randint(0, 10000),
                ),
            )

        for _ in range(100):
            cursor.execute(
                "INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)",
                (random.randint(1, 100), random.randint(1, 100), fake.paragraph()),
            )

        category_names = [
            "Technology",
            "Health",
            "Sports",
            "Entertainment",
            "Business",
            "Science",
            "Politics",
        ]
        for category in category_names:
            cursor.execute(
                "INSERT INTO categories (name, description) VALUES (%s, %s)",
                (category, fake.text(max_nb_chars=200)),
            )

        colors = [
            "#FF5733",
            "#33FF57",
            "#3357FF",
            "#F3FF33",
            "#FF33F3",
            "#33FFF3",
            "#F333FF",
        ]
        tag_names = [
            "trending",
            "popular",
            "new",
            "featured",
            "hot",
            "recommended",
            "sponsored",
        ]
        for i, tag in enumerate(tag_names):
            cursor.execute(
                "INSERT INTO tags (name, color) VALUES (%s, %s)",
                (tag, colors[i % len(colors)]),
            )

        print("PostgreSQL: Successfully inserted mock data")

    except psycopg2.Error as e:
        print(f"PostgreSQL Error: {e}")
    finally:
        cursor.close()
        conn.close()


def generate_redis_data():
    """Generate and insert mock data into Redis database"""
    try:
        r = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            password=REDIS_CONFIG["password"],
            db=REDIS_CONFIG["db"],
        )

        for i in range(1, 101):
            user_key = f"user:{i}"
            user_data = {
                "username": fake.user_name(),
                "email": fake.email(),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "created_at": fake.iso8601(),
                "login_count": str(random.randint(1, 100)),
            }
            r.hset(user_key, mapping=user_data)

        for i in range(1, 101):
            session_key = f"session:{fake.uuid4()}"
            r.hset(
                session_key,
                mapping={
                    "user_id": str(random.randint(1, 100)),
                    "ip": fake.ipv4(),
                    "user_agent": fake.user_agent(),
                    "created_at": fake.iso8601(),
                    "expires_at": fake.future_datetime().isoformat(),
                },
            )
            r.expire(session_key, random.randint(3600, 86400))

        for i in range(1, 101):
            cache_key = f"cache:{fake.md5()}"
            r.set(cache_key, fake.text())
            r.expire(cache_key, random.randint(300, 3600))

        counters = ["page_views", "api_calls", "logins", "signups", "errors"]
        for counter in counters:
            r.set(f"counter:{counter}", random.randint(1000, 1000000))

        activity_key = "recent_activities"
        for _ in range(100):
            r.lpush(
                activity_key,
                f"{fake.name()} {random.choice(['logged in', 'posted a comment', 'updated profile', 'made a purchase', 'viewed a page'])}",
            )
        r.ltrim(activity_key, 0, 99)

        print("Redis: Successfully inserted mock data")

    except redis.RedisError as e:
        print(f"Redis Error: {e}")


def drop_databases():
    """Drop all databases before regenerating data"""
    print("Dropping existing databases...")

    # Drop MySQL database
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG["host"],
            port=MYSQL_CONFIG["port"],
            user=MYSQL_CONFIG["user"],
            password=MYSQL_CONFIG["password"],
        )
        cursor = conn.cursor()

        cursor.execute(f"DROP DATABASE IF EXISTS {MYSQL_CONFIG['database']}")
        cursor.execute(f"CREATE DATABASE {MYSQL_CONFIG['database']}")
        print(f"MySQL: Reset database {MYSQL_CONFIG['database']}")

    except mysql.connector.Error as e:
        print(f"MySQL Error when dropping database: {e}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()

    # For PostgreSQL, instead of dropping the database, we'll drop all tables
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()

        # Drop all tables in the current database
        cursor.execute("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print(
            f"PostgreSQL: Dropped all tables in database {POSTGRES_CONFIG['database']}"
        )

    except psycopg2.Error as e:
        print(f"PostgreSQL Error when dropping tables: {e}")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "conn" in locals():
            conn.close()

    # Clear Redis database - using DEL instead of FLUSHDB
    try:
        r = redis.Redis(
            host=REDIS_CONFIG["host"],
            port=REDIS_CONFIG["port"],
            password=REDIS_CONFIG["password"],
            db=REDIS_CONFIG["db"],
        )

        # Get all keys and delete them
        all_keys = r.keys("*")
        if all_keys:
            r.delete(*all_keys)
        print(f"Redis: Cleared all keys in database {REDIS_CONFIG['db']}")

    except redis.RedisError as e:
        print(f"Redis Error when clearing database: {e}")


if __name__ == "__main__":
    print("Generating mock data for databases...")

    drop_databases()  # Drop databases before generating new data

    generate_mysql_data()
    generate_postgres_data()
    generate_redis_data()

    print("Mock data generation complete!")
