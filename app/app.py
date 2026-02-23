import os
import json
import time
import psycopg2
import redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

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
# Models
# -------------------------
class ItemCreate(BaseModel):
    id: int
    value: str


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
# DB Table Init (with retry)
# -------------------------
_table_ready = False

def ensure_table():
    """Lazily create the items table if not already done."""
    global _table_ready
    if _table_ready:
        return

    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        cur.execute("SELECT COUNT(*) FROM items;")
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO items (id, value) VALUES
                (1, 'Hello from PostgreSQL!'),
                (2, 'Multi-tier architecture works!'),
                (3, 'ECS Fargate is awesome!')
                ON CONFLICT DO NOTHING;
            """)
        conn.commit()
        cur.close()
        conn.close()
        _table_ready = True
        print("DB table 'items' ready with demo data.")
    except Exception as e:
        print(f"DB table setup error: {e}")


# -------------------------
# Startup: Retry DB init
# -------------------------
@app.on_event("startup")
def startup():
    print("App starting...")
    print(f"Environment: {APP_ENV}")

    # Retry DB setup (Docker DB may take a few seconds to start)
    for attempt in range(5):
        conn = get_db_connection()
        if conn:
            conn.close()
            ensure_table()
            return
        print(f"DB not ready, retrying ({attempt + 1}/5)...")
        time.sleep(3)

    print("DB not available at startup - tables will be created on first request.")


# -------------------------
# Status API (for live dashboard refresh)
# -------------------------
@app.get("/status")
def live_status():
    result = {
        "app": {"status": "ok", "env": APP_ENV},
        "db": {"status": "disconnected", "detail": ""},
        "redis": {"status": "disconnected", "detail": ""}
    }

    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM items;")
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            result["db"] = {
                "status": "connected",
                "detail": ver[:60],
                "items_count": count
            }
        elif APP_ENV == "local":
            result["db"] = {"status": "skipped", "detail": "Local mode"}
    except Exception as e:
        result["db"]["detail"] = str(e)[:80]

    try:
        r = get_redis_client()
        if r:
            info = r.info("server")
            keys = r.dbsize()
            result["redis"] = {
                "status": "connected",
                "detail": f"Redis {info.get('redis_version', '?')}",
                "cached_keys": keys
            }
        elif not REDIS_HOST:
            result["redis"] = {"status": "not_configured", "detail": "REDIS_HOST not set"}
    except Exception as e:
        result["redis"]["detail"] = str(e)[:80]

    return result


# -------------------------
# Dashboard UI
# -------------------------
@app.get("/", response_class=HTMLResponse)
def root():
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>4-Tier AWS Architecture | Live Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: #0a0a1a;
            color: #e0e0ff;
            min-height: 100vh;
            overflow-x: hidden;
        }}

        body::before {{
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background:
                radial-gradient(ellipse at 20% 50%, rgba(88, 60, 255, 0.12) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(0, 200, 255, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 80%, rgba(200, 50, 255, 0.06) 0%, transparent 50%);
            z-index: 0;
            animation: bgPulse 8s ease-in-out infinite alternate;
        }}

        @keyframes bgPulse {{
            0% {{ opacity: 0.8; }}
            100% {{ opacity: 1; }}
        }}

        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
        }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 48px;
        }}

        .badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(88, 60, 255, 0.15);
            border: 1px solid rgba(88, 60, 255, 0.3);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #a78bfa;
            margin-bottom: 20px;
        }}

        .badge .dot {{
            width: 8px; height: 8px;
            background: #22c55e;
            border-radius: 50%;
            animation: pulse 2s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }}
            50% {{ opacity: 0.8; box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }}
        }}

        h1 {{
            font-size: 42px;
            font-weight: 800;
            background: linear-gradient(135deg, #fff 0%, #a78bfa 50%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
            margin-bottom: 12px;
        }}

        .subtitle {{
            font-size: 16px;
            color: #8888aa;
            font-weight: 400;
        }}

        /* Environment Banner */
        .env-banner {{
            display: flex;
            justify-content: center;
            gap: 24px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}

        .env-chip {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 8px 20px;
            border-radius: 10px;
            font-size: 13px;
            color: #aaa;
        }}

        .env-chip strong {{ color: #e0e0ff; }}

        /* Section */
        .arch-section {{ margin-bottom: 40px; }}

        .section-title {{
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #6366f1;
            margin-bottom: 20px;
            padding-left: 4px;
        }}

        /* Architecture Flow */
        .arch-flow {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }}

        .tier-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 24px 20px;
            text-align: center;
            transition: all 0.3s ease;
            overflow: hidden;
            position: relative;
        }}

        .tier-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            border-radius: 16px 16px 0 0;
        }}

        .tier-card:nth-child(1)::before {{ background: linear-gradient(90deg, #f59e0b, #f97316); }}
        .tier-card:nth-child(2)::before {{ background: linear-gradient(90deg, #6366f1, #8b5cf6); }}
        .tier-card:nth-child(3)::before {{ background: linear-gradient(90deg, #3b82f6, #06b6d4); }}
        .tier-card:nth-child(4)::before {{ background: linear-gradient(90deg, #ef4444, #ec4899); }}

        .tier-card:hover {{
            border-color: rgba(255,255,255,0.15);
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.3);
        }}

        .tier-icon {{ font-size: 32px; margin-bottom: 12px; }}
        .tier-label {{ font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #666; margin-bottom: 4px; }}
        .tier-name {{ font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px; }}
        .tier-service {{ font-size: 12px; color: #888; }}

        .tier-card:not(:last-child)::after {{
            content: '→';
            position: absolute;
            right: -18px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 20px;
            color: #333;
            z-index: 2;
        }}

        /* Status Grid */
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}

        .status-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 24px;
            transition: all 0.3s ease;
        }}

        .status-card:hover {{ border-color: rgba(255,255,255,0.12); }}

        .status-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}

        .status-name {{ font-size: 14px; font-weight: 600; color: #ccc; }}
        .status-indicator {{ font-size: 18px; }}
        .status-value {{ font-size: 12px; color: #666; font-family: 'JetBrains Mono', monospace; word-break: break-all; }}
        .status-extra {{ font-size: 11px; color: #555; margin-top: 4px; }}

        /* API Console */
        .console-box {{
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            overflow: hidden;
        }}

        .console-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 14px 20px;
            background: rgba(255,255,255,0.03);
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}

        .console-dot {{
            width: 12px; height: 12px;
            border-radius: 50%;
        }}

        .console-dot.red {{ background: #ef4444; }}
        .console-dot.yellow {{ background: #f59e0b; }}
        .console-dot.green {{ background: #22c55e; }}

        .console-title {{
            font-size: 13px;
            color: #888;
            font-family: 'JetBrains Mono', monospace;
            margin-left: 8px;
        }}

        .console-body {{ padding: 20px; }}

        /* Quick Action Buttons */
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}

        .action-btn {{
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.25s ease;
            text-align: left;
        }}

        .action-btn:hover {{
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
        }}

        .action-btn:active {{ transform: translateY(0); }}

        .action-btn .btn-method {{
            font-size: 10px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 1px;
            padding: 3px 8px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 8px;
        }}

        .action-btn .btn-method.get {{
            background: rgba(34, 197, 94, 0.15);
            color: #22c55e;
        }}

        .action-btn .btn-method.post {{
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
        }}

        .action-btn .btn-path {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: #e0e0ff;
            margin-bottom: 4px;
        }}

        .action-btn .btn-desc {{
            font-size: 11px;
            color: #666;
        }}

        /* Custom Query Input */
        .query-row {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}

        .query-input {{
            flex: 1;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 12px 16px;
            color: #e0e0ff;
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}

        .query-input:focus {{
            border-color: rgba(99, 102, 241, 0.5);
        }}

        .query-input::placeholder {{ color: #444; }}

        .send-btn {{
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            color: #fff;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }}

        .send-btn:hover {{
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
            transform: translateY(-1px);
        }}

        .send-btn:disabled {{
            opacity: 0.5;
            cursor: default;
            transform: none;
        }}

        /* Response Area */
        .response-area {{
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            padding: 16px;
            min-height: 120px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #8888aa;
            position: relative;
            overflow: auto;
            max-height: 300px;
        }}

        .response-area .res-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }}

        .res-status {{
            font-weight: 600;
            font-size: 12px;
        }}

        .res-status.ok {{ color: #22c55e; }}
        .res-status.error {{ color: #ef4444; }}

        .res-time {{
            font-size: 11px;
            color: #555;
        }}

        .res-body {{
            white-space: pre-wrap;
            word-break: break-all;
        }}

        .res-body .json-key {{ color: #a78bfa; }}
        .res-body .json-string {{ color: #22c55e; }}
        .res-body .json-number {{ color: #f59e0b; }}
        .res-body .json-bool {{ color: #ef4444; }}

        /* Log History */
        .log-entry {{
            padding: 10px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .log-entry:last-child {{ border-bottom: none; }}

        .log-method {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 3px;
            min-width: 36px;
            text-align: center;
        }}

        .log-method.get {{ background: rgba(34,197,94,0.1); color: #22c55e; }}
        .log-method.post {{ background: rgba(59,130,246,0.1); color: #60a5fa; }}

        .log-path {{
            font-family: 'JetBrains Mono', monospace;
            color: #aaa;
            flex: 1;
        }}

        .log-status {{ font-weight: 600; }}
        .log-time {{ color: #555; font-size: 11px; }}

        /* Spinner */
        .spinner {{
            display: inline-block;
            width: 16px; height: 16px;
            border: 2px solid rgba(255,255,255,0.1);
            border-top-color: #6366f1;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* Footer */
        .footer {{
            text-align: center;
            color: #444;
            font-size: 12px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.04);
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .arch-flow {{ grid-template-columns: repeat(2, 1fr); }}
            .status-grid {{ grid-template-columns: 1fr; }}
            .action-grid {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 28px; }}
            .tier-card:not(:last-child)::after {{ display: none; }}
            .query-row {{ flex-direction: column; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="badge"><span class="dot"></span> SYSTEM ONLINE</div>
            <h1>4-Tier AWS Infrastructure</h1>
            <p class="subtitle">Production-grade cloud architecture powered by Terraform & ECS Fargate</p>
        </div>

        <!-- Environment -->
        <div class="env-banner">
            <div class="env-chip">🌍 Environment: <strong>{APP_ENV.upper()}</strong></div>
            <div class="env-chip">☁️ Region: <strong>us-east-1</strong></div>
            <div class="env-chip">🐳 Runtime: <strong>ECS Fargate</strong></div>
        </div>

        <!-- Architecture Flow -->
        <div class="arch-section">
            <div class="section-title">Architecture Flow</div>
            <div class="arch-flow">
                <div class="tier-card">
                    <div class="tier-icon">🌐</div>
                    <div class="tier-label">Tier 1</div>
                    <div class="tier-name">Load Balancer</div>
                    <div class="tier-service">AWS ALB</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">⚡</div>
                    <div class="tier-label">Tier 2</div>
                    <div class="tier-name">Application</div>
                    <div class="tier-service">ECS Fargate + FastAPI</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">🗄️</div>
                    <div class="tier-label">Tier 3</div>
                    <div class="tier-name">Database</div>
                    <div class="tier-service">Amazon RDS (PostgreSQL)</div>
                </div>
                <div class="tier-card">
                    <div class="tier-icon">⚡</div>
                    <div class="tier-label">Tier 4</div>
                    <div class="tier-name">Cache</div>
                    <div class="tier-service">Amazon ElastiCache (Redis)</div>
                </div>
            </div>
        </div>

        <!-- Live Status (auto-refreshing) -->
        <div class="arch-section">
            <div class="section-title">Live Service Status <span id="refresh-indicator" style="color:#444;font-size:10px;letter-spacing:0;text-transform:none;font-weight:400;margin-left:8px;">auto-refreshes every 10s</span></div>
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-header">
                        <span class="status-name">FastAPI Server</span>
                        <span class="status-indicator" id="app-status">⏳</span>
                    </div>
                    <div class="status-value" id="app-detail">Checking...</div>
                </div>
                <div class="status-card">
                    <div class="status-header">
                        <span class="status-name">PostgreSQL (RDS)</span>
                        <span class="status-indicator" id="db-status">⏳</span>
                    </div>
                    <div class="status-value" id="db-detail">Checking...</div>
                    <div class="status-extra" id="db-extra"></div>
                </div>
                <div class="status-card">
                    <div class="status-header">
                        <span class="status-name">Redis (ElastiCache)</span>
                        <span class="status-indicator" id="redis-status">⏳</span>
                    </div>
                    <div class="status-value" id="redis-detail">Checking...</div>
                    <div class="status-extra" id="redis-extra"></div>
                </div>
            </div>
        </div>

        <!-- Interactive API Console -->
        <div class="arch-section">
            <div class="section-title">🔥 Interactive API Console</div>
            <div class="console-box">
                <div class="console-header">
                    <span class="console-dot red"></span>
                    <span class="console-dot yellow"></span>
                    <span class="console-dot green"></span>
                    <span class="console-title">api-console — click a button or type a custom endpoint</span>
                </div>
                <div class="console-body">
                    <!-- Quick Actions -->
                    <div class="action-grid">
                        <div class="action-btn" onclick="runQuery('GET', '/health')">
                            <span class="btn-method get">GET</span>
                            <div class="btn-path">/health</div>
                            <div class="btn-desc">ALB health check endpoint</div>
                        </div>
                        <div class="action-btn" onclick="runQuery('GET', '/api')">
                            <span class="btn-method get">GET</span>
                            <div class="btn-path">/api</div>
                            <div class="btn-desc">JSON service status</div>
                        </div>
                        <div class="action-btn" onclick="runQuery('GET', '/data/1')">
                            <span class="btn-method get">GET</span>
                            <div class="btn-path">/data/1</div>
                            <div class="btn-desc">Fetch item 1 — Redis → DB flow</div>
                        </div>
                        <div class="action-btn" onclick="runQuery('GET', '/status')">
                            <span class="btn-method get">GET</span>
                            <div class="btn-path">/status</div>
                            <div class="btn-desc">Full service connectivity check</div>
                        </div>
                        <div class="action-btn" onclick="runQuery('GET', '/data/2')">
                            <span class="btn-method get">GET</span>
                            <div class="btn-path">/data/2</div>
                            <div class="btn-desc">Fetch item 2 — try twice to see Redis cache!</div>
                        </div>
                        <div class="action-btn" onclick="postDemo()">
                            <span class="btn-method post">POST</span>
                            <div class="btn-path">/data</div>
                            <div class="btn-desc">Write new item to DB, then fetch it</div>
                        </div>
                    </div>

                    <!-- Custom Query -->
                    <div class="query-row">
                        <input type="text" class="query-input" id="custom-path" placeholder="Type endpoint, e.g. /data/3  or  /health" value="/health">
                        <button class="send-btn" id="send-btn" onclick="runCustom()">▶ Send</button>
                    </div>

                    <!-- Response -->
                    <div class="response-area" id="response-area">
                        <span style="color:#555;">👆 Click a button above or type a custom endpoint to see live API responses here.</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Request History -->
        <div class="arch-section">
            <div class="section-title">📜 Request History</div>
            <div class="console-box">
                <div id="history" style="max-height: 200px; overflow-y: auto;">
                    <div class="log-entry" style="color:#555; padding: 20px; text-align: center;">
                        No requests yet — try the console above!
                    </div>
                </div>
            </div>
        </div>

        <!-- Tech Stack -->
        <div class="arch-section">
            <div class="section-title">Infrastructure Stack</div>
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-header"><span class="status-name">🏗️ IaC</span></div>
                    <div class="status-value">Terraform with S3 backend</div>
                </div>
                <div class="status-card">
                    <div class="status-header"><span class="status-name">🐳 Container</span></div>
                    <div class="status-value">Docker → ECR → ECS Fargate</div>
                </div>
                <div class="status-card">
                    <div class="status-header"><span class="status-name">🔒 Networking</span></div>
                    <div class="status-value">VPC · Public/Private Subnets · NAT · SGs</div>
                </div>
            </div>
        </div>

        <div class="footer">
            Multi-AWS 4-Tier Infrastructure &nbsp;·&nbsp; Built with Terraform & FastAPI
        </div>
    </div>

    <script>
        // ---- Auto-refresh service status ----
        async function refreshStatus() {{
            try {{
                const res = await fetch('/status');
                const data = await res.json();

                // App
                document.getElementById('app-status').textContent = '🟢';
                document.getElementById('app-detail').textContent = 'Healthy — Port 80 — ' + data.app.env;

                // DB
                const dbIcon = data.db.status === 'connected' ? '🟢' : data.db.status === 'skipped' ? '⚪' : '🔴';
                document.getElementById('db-status').textContent = dbIcon;
                document.getElementById('db-detail').textContent = data.db.detail || data.db.status;
                document.getElementById('db-extra').textContent = data.db.items_count !== undefined ? data.db.items_count + ' items in DB' : '';

                // Redis
                const redisIcon = data.redis.status === 'connected' ? '🟢' : data.redis.status === 'not_configured' ? '⚪' : '🔴';
                document.getElementById('redis-status').textContent = redisIcon;
                document.getElementById('redis-detail').textContent = data.redis.detail || data.redis.status;
                document.getElementById('redis-extra').textContent = data.redis.cached_keys !== undefined ? data.redis.cached_keys + ' cached keys' : '';
            }} catch (e) {{
                document.getElementById('app-status').textContent = '🔴';
                document.getElementById('app-detail').textContent = 'Cannot reach server';
            }}
        }}

        refreshStatus();
        setInterval(refreshStatus, 10000);

        // ---- Syntax highlight JSON ----
        function highlightJSON(obj) {{
            const str = JSON.stringify(obj, null, 2);
            return str.replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
                       .replace(/: "([^"]*)",?/g, (m, v) => ': <span class="json-string">"' + v + '"</span>' + (m.endsWith(',') ? ',' : ''))
                       .replace(/: (\\d+\\.?\\d*)/g, ': <span class="json-number">$1</span>')
                       .replace(/: (true|false|null)/g, ': <span class="json-bool">$1</span>');
        }}

        // ---- History tracking ----
        let historyEntries = [];

        function addHistory(method, path, status, timeMs) {{
            historyEntries.unshift({{ method, path, status, timeMs, ts: new Date() }});
            if (historyEntries.length > 20) historyEntries.pop();

            const container = document.getElementById('history');
            container.innerHTML = historyEntries.map(e => `
                <div class="log-entry">
                    <span class="log-method ${{e.method.toLowerCase()}}">${{e.method}}</span>
                    <span class="log-path">${{e.path}}</span>
                    <span class="log-status" style="color:${{e.status < 400 ? '#22c55e' : '#ef4444'}}">${{e.status}}</span>
                    <span class="log-time">${{e.timeMs}}ms</span>
                    <span class="log-time">${{e.ts.toLocaleTimeString()}}</span>
                </div>
            `).join('');
        }}

        // ---- Run API query ----
        async function runQuery(method, path, body = null) {{
            const area = document.getElementById('response-area');
            const btn = document.getElementById('send-btn');
            btn.disabled = true;

            area.innerHTML = '<div class="spinner"></div> <span style="color:#888;margin-left:8px;">Fetching ' + path + '...</span>';

            const start = performance.now();
            try {{
                const opts = {{ method }};
                if (body) {{
                    opts.headers = {{ 'Content-Type': 'application/json' }};
                    opts.body = JSON.stringify(body);
                }}
                const res = await fetch(path, opts);
                const elapsed = Math.round(performance.now() - start);
                const data = await res.json();

                const statusClass = res.ok ? 'ok' : 'error';
                area.innerHTML = `
                    <div class="res-header">
                        <span class="res-status ${{statusClass}}">${{method}} ${{path}} — ${{res.status}} ${{res.statusText}}</span>
                        <span class="res-time">${{elapsed}}ms</span>
                    </div>
                    <div class="res-body">${{highlightJSON(data)}}</div>
                `;

                addHistory(method, path, res.status, elapsed);
            }} catch (err) {{
                const elapsed = Math.round(performance.now() - start);
                area.innerHTML = `
                    <div class="res-header">
                        <span class="res-status error">ERROR — ${{path}}</span>
                        <span class="res-time">${{elapsed}}ms</span>
                    </div>
                    <div class="res-body" style="color:#ef4444;">${{err.message}}</div>
                `;
                addHistory(method, path, 0, elapsed);
            }}

            btn.disabled = false;
        }}

        function runCustom() {{
            const path = document.getElementById('custom-path').value.trim();
            if (path) runQuery('GET', path.startsWith('/') ? path : '/' + path);
        }}

        // Enter key support
        document.getElementById('custom-path').addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') runCustom();
        }});

        // POST demo
        async function postDemo() {{
            const randomId = Math.floor(Math.random() * 9000) + 1000;
            const body = {{ id: randomId, value: "Demo item #" + randomId + " created at " + new Date().toLocaleTimeString() }};
            await runQuery('POST', '/data', body);
            // Then fetch it back to show the cache flow
            setTimeout(() => runQuery('GET', '/data/' + randomId), 1000);
        }}
    </script>
</body>
</html>
"""


@app.get("/api")
def api_status():
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


@app.post("/data")
def create_data(item: ItemCreate):
    """Write a new item to DB"""
    ensure_table()
    conn = get_db_connection()
    if not conn:
        return JSONResponse(
            status_code=503,
            content={"error": "database unavailable", "hint": "This works on AWS with RDS connected"}
        )

    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (id, value) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET value = %s RETURNING id, value;",
            (item.id, item.value, item.value)
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        # Also cache it in Redis
        r = get_redis_client()
        if r:
            r.setex(f"item:{item.id}", 60, item.value)

        return {"id": row[0], "value": row[1], "source": "database", "action": "created"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/data/{item_id}")
def get_data(item_id: int):
    ensure_table()
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
