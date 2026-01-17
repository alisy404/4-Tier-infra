import os
import time
import psycopg2
import redis
from fastapi import FastAPI
from time import sleep

# -------------------------
# Environment
# -------------------------
APP_ENV = os.getenv("APP_ENV", "local")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

app = FastAPI(title="FastAPI ECS Service")

# -------------------------
# Database Connection
# -------------------------
def get_db_connection():
    if APP_ENV == "local":
        return None

    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3
        )
    except Exception as e:
        print("DB unavailable:", e)
        return None


# -------------------------
# Redis Connection
# -------------------------
def get_redis_client():
    if not REDIS_HOST:
        return None

    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        r.ping()
        return r
    except Exception as e:
        print("Redis unavailable:", e)
        return None


# -------------------------
# Startup Hook (SAFE)
# -------------------------
@app.on_event("startup")
def startup():
    """
    IMPORTANT:
    - NEVER fail startup in ECS
    - ALB health checks MUST pass
    """
    print("App starting...")
    print(f"Environment: {APP_ENV}")


# -------------------------
# Routes
# -------------------------
@app.get("/")
def root():
    return {
        "service": "fastapi-ecs",
        "status": "running",
        "env": APP_ENV
    }


@app.get("/health")
def health():
    """
    ALB HEALTH CHECK
    MUST:
    - return 200
    - return fast
    - NEVER touch DB / Redis
    """
    return {"status": "ok"}


@app.get("/data/{item_id}")
def get_data(item_id: int):
    cache_key = f"item:{item_id}"

    # Redis first
    r = get_redis_client()
    if r:
        cached = r.get(cache_key)
        if cached:
            return {"id": item_id, "value": cached, "source": "redis"}

    # DB fallback
    conn = get_db_connection()
    if not conn:
        return {"error": "database unavailable"}

    cur = conn.cursor()
    cur.execute("SELECT value FROM items WHERE id = %s", (item_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return {"error": "item not found"}

    value = row[0]

    if r:
        r.setex(cache_key, 60, value)

    return {"id": item_id, "value": value, "source": "database"}
