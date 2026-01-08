from fastapi import FastAPI
from time import sleep
from typing import Dict
from config import APP_ENV


app = FastAPI(title="Tier-1 Baseline Service")

# In-memory data store (will be replaced in Tier-2)
DATA_STORE: Dict[int, str] = {
    1: "alpha",
    2: "beta",
    3: "gamma"
}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": APP_ENV
    }
    
@app.get("/data/{item_id}")
def get_data(item_id: int):
    # Simulate processing latency
    sleep(0.1)

    value = DATA_STORE.get(item_id)
    if not value:
        return {"error": "item not found"}

    return {
        "id": item_id,
        "value": value,
        "source": "memory"
    }

@app.get("/")
def root():
    return {
        "message": "Tier-1 service running",
        "available_endpoints": ["/health", "/data/{id}"]
    }



