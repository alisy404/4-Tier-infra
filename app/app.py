import psycopg2
from fastapi import FastAPI
from time import sleep
from config import APP_ENV, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD
import time
import redis

app = FastAPI(title="Tier-2 Database Service")


from config import (
    APP_ENV,
    DB_HOST, DB_NAME, DB_USER, DB_PASSWORD,
    REDIS_HOST, REDIS_PORT
)

# -------------------------
# Database Connection
# -------------------------
def get_db_connection(retries=10, delay=5):
    for attempt in range(retries):
        try:
            return psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        except psycopg2.OperationalError as e:
            print(f"DB not ready (attempt {attempt+1}/{retries}), retrying...")
            time.sleep(delay)
    raise Exception("Database not available after retries")


# -------------------------
# Startup: Init DB
# -------------------------
@app.on_event("startup")
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            value TEXT NOT NULL
        )
    """
    )

    cur.execute(
        """
        INSERT INTO items (value)
        SELECT * FROM (VALUES ('alpha'), ('beta'), ('gamma')) AS v(value)
        WHERE NOT EXISTS (SELECT 1 FROM items)
    """
    )

    conn.commit()
    cur.close()
    conn.close()


# -------------------------
# Routes
# -------------------------
@app.get("/")
def root():
    return {"message": "FastAPI running on ECS", "endpoints": ["/health", "/data/{id}"]}


@app.get("/health")
def health():
    return {"status": "OK", "environment": APP_ENV}


@app.get("/data/{item_id}")
def get_data(item_id: int):
    sleep(0.1)
    cache_key = f"item:{item_id}"

    r = get_redis_client()
    if r:
        try:
            cached = r.get(cache_key)
            if cached:
                return {
                    "id": item_id,
                    "value": cached,
                    "source": "redis"
                }
        except Exception as e:
            print("Redis read failed:", e)


    # Cache miss → DB
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT value FROM items WHERE id = %s", (item_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return {"error": "item not found"}

    value = row[0]

    # Write to cache (TTL = 60s)
    if r:
        try:
            r.setex(cache_key, 60, value)
        except Exception as e:
            print("Redis write failed:", e)

    return {
        "id": item_id,
        "value": value,
        "source": "database"
    }


def get_redis_client():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        r.ping()  # 🔥 THIS is the key
        return r
    except Exception as e:
        print("Redis unavailable:", e)
        return None
