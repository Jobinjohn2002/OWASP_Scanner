import os
import traceback
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

missing = [k for k, v in (("DB_HOST", DB_HOST), ("DB_USER", DB_USER), ("DB_PASSWORD", DB_PASSWORD), ("DB_NAME", DB_NAME)) if not v and k != "DB_PASSWORD"]
if missing:
    logger.error("Missing required env vars: %s. Place a .env file next to main.py with DB_HOST, DB_USER, DB_NAME (DB_PASSWORD optional).", missing)
else:
    logger.info("Loaded DB config: host=%s user=%s db=%s", DB_HOST, DB_USER, DB_NAME)


def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),  
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            connection_timeout=5 
        )
        logger.info("DB connected.")
        return conn
    except Exception as e:
        logger.error("DB connection failed: %s", e)
        raise


@app.middleware("http")
async def log_exceptions(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception("Unhandled error while processing request")
        return JSONResponse(status_code=500, content={"error": "Internal server error", "details": str(e)})


@app.get("/")
def root():
    return {"message": "API is running"}


@app.get("/test")
def test():
    """DB-free endpoint to check the app is up."""
    return {"message": "test OK"}


@app.get("/projects")
def get_unique_projects():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT project_name FROM ai_git_guard_logs")
        rows = cursor.fetchall()
        projects = [row[0] for row in rows if row and row[0] is not None]
        return {"projects": projects}
    except Exception as e:
        logger.exception("Error in /projects")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                logger.debug("Error closing cursor", exc_info=True)
        if conn:
            try:
                conn.close()
            except Exception:
                logger.debug("Error closing connection", exc_info=True)


@app.get("/projects/{project_name}/developers")
def get_developers_count(project_name: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT COUNT(DISTINCT user_name) AS dev_count
            FROM ai_git_guard_logs
            WHERE project_name = %s
        """
        cursor.execute(query, (project_name,))
        row = cursor.fetchone()
        count = row[0] if row and row[0] is not None else 0
        return {"project_name": project_name, "developers_count": int(count)}
    except Exception as e:
        logger.exception("Error in /projects/{project_name}/developers")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/projects/{project_name}/total-pushes")
def get_total_pushes(project_name: str):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM ai_git_guard_logs WHERE project_name = %s"
        cursor.execute(query, (project_name,))
        row = cursor.fetchone()
        total = row[0] if row and row[0] is not None else 0
        return {"project_name": project_name, "total_pushes": int(total)}
    except Exception as e:
        logger.exception("Error in /projects/{project_name}/total-pushes")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.get("/projects/{project_name}/blocked-pushes")
def get_blocked_pushes(project_name: str):
    """
    Robust blocked count: works if your table uses status='blocked' OR boolean is_blocked column.
    If your schema uses only one of these, the query still works.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT COUNT(*) FROM ai_git_guard_logs
            WHERE project_name = %s
            AND is_bloceked = 1
        """
        cursor.execute(query, (project_name,))
        row = cursor.fetchone()
        blocked = row[0] if row and row[0] is not None else 0
        return {"project_name": project_name, "blocked_pushes": int(blocked)}
    except Exception as e:
        logger.exception("Error in /projects/{project_name}/blocked-pushes")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
