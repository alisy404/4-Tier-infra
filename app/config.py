import os

APP_ENV     = os.getenv("APP_ENV",     "local")

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_NAME     = os.getenv("DB_NAME",     "appdb")
DB_USER     = os.getenv("DB_USER",     "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppass")

REDIS_HOST = os.getenv("REDIS_HOST",   "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

print(f"Running in {APP_ENV} environment")
print("APP_ENV =", APP_ENV)
