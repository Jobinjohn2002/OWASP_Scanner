from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pymysql
from dotenv import load_dotenv
import os
import traceback

load_dotenv()

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

def get_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.Cursor
        )
        return conn
    except Exception as e:
        print("DATABASE ERROR:", e)
        raise e

@app.get("/")
def root():
    return {"message": "API is running"}

def safe_int(val):
    if val is None:
        return 0
    return int(val)

@app.get("/projects")
def get_unique_projects():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT project_name FROM ai_git_guard_logs")
        rows = cursor.fetchall()
        projects = [row[0] for row in rows]
        cursor.close()
        conn.close()
        return {"projects": projects}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/projects/{project_name:path}/developers")
def get_developers_count(project_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT user_name)
            FROM ai_git_guard_logs
            WHERE project_name = %s
        """, (project_name,))
        count = safe_int(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return {"project_name": project_name, "developer_count": count}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/projects/{project_name:path}/total-pushes")
def get_total_pushes(project_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM ai_git_guard_logs
            WHERE project_name = %s
        """, (project_name,))
        count = safe_int(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return {"project_name": project_name, "total_pushes": count}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/projects/{project_name:path}/blocked-pushes")
def get_blocked_pushes(project_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM ai_git_guard_logs
            WHERE project_name = %s AND is_blocked = 1
        """, (project_name,))
        count = safe_int(cursor.fetchone()[0])
        cursor.close()
        conn.close()
        return {"project_name": project_name, "blocked_pushes": count}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@app.get("/projects/{project_name:path}/blocks-per-developer")
def get_blocks_per_developer(project_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_name, COUNT(*) AS blocked_count
            FROM ai_git_guard_logs
            WHERE project_name = %s AND is_blocked = 1
            GROUP BY user_name
            ORDER BY blocked_count DESC
        """, (project_name,))

        rows = cursor.fetchall()
        result = [{"user_name": row[0], "blocked_count": row[1]} for row in rows]

        cursor.close()
        conn.close()
        return {"project_name": project_name, "blocks_per_developer": result}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/projects/{project_name:path}/status-percentage")
def get_status_percentage(project_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM ai_git_guard_logs WHERE project_name = %s
        """, (project_name,))
        total = safe_int(cursor.fetchone()[0])

        if total == 0:
            return {"project_name": project_name, "status_percentage": {}}

        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*)
            FROM ai_git_guard_logs
            WHERE project_name = %s
            GROUP BY status
        """, (project_name,))

        rows = cursor.fetchall()

        percentages = {
            row[0]: round((row[1] / total) * 100, 2)
            for row in rows
        }

        cursor.close()
        conn.close()
        return {"project_name": project_name, "status_percentage": percentages}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/projects/{project_name:path}/recent-activities")
def get_recent_activities(project_name: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_name, status, timestamp
            FROM ai_git_guard_logs
            WHERE project_name = %s
            ORDER BY timestamp DESC
            LIMIT 10
        """, (project_name,))

        rows = cursor.fetchall()

        activities = [
            {
                "user_name": row[0],
                "status": row[1],
                "timestamp": row[2]
            }
            for row in rows
        ]

        cursor.close()
        conn.close()
        return {"project_name": project_name, "recent_activities": activities}

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})