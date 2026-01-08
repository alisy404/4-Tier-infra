import os

APP_ENV = os.getenv("APP_ENV", "local")

DB_HOST = os.getenv("DB_HOST", "")
REDIS_HOST = os.getenv("REDIS_HOST", "")
QUEUE_URL = os.getenv("QUEUE_URL", "")
