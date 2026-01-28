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
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


# ------------------------------------------------------------
# DB CONNECTION (PyMySQL)
# ------------------------------------------------------------
def get_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
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
    return int(val or 0)

def calculate_health(block_rate: float):
    if block_rate < 5:
        return "LOW"
    elif block_rate < 15:
        return "MODERATE"
    return "HIGH"

# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------

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

@app.get("/projects/{project_name}/insights")
def get_project_insights(project_name: str, days: int = 30):
    """
    Advanced project insights with comprehensive security analytics
    Schema-aware version that adapts to available columns
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ===================================
        # 0. TABLE SCHEMA
        # ===================================
        # Available columns: id, project_name, user_name, timestamp, 
        # severity, status, details, suggestions, is_blocked
        has_branch = False  # branch_name column doesn't exist
        has_severity = True  # severity column exists
        has_commit_id = False  # commit_id column doesn't exist
        has_file_path = False  # file_path column doesn't exist

        insights = {
            "overview": {},
            "security_metrics": {},
            "trend_analysis": {},
            "team_analytics": {},
            "vulnerability_breakdown": {},
            "temporal_patterns": {},
            "user_activity_analysis": [],  # Changed from branch_analysis since no branch_name
            "risk_assessment": {},
            "recommendations": [],
            "alerts": [],
            "quick_stats": {}
        }

        # ===================================
        # 1. OVERVIEW METRICS
        # ===================================
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_pushes,
                SUM(is_blocked) AS blocked_pushes,
                COUNT(DISTINCT user_name) AS active_developers,
                AVG(CASE WHEN is_blocked = 1 THEN 1 ELSE 0 END) * 100 AS block_rate
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
        """, (project_name, days))
        
        overview = cursor.fetchone()
        # Convert Decimal to float/int to avoid type issues
        total_pushes = int(overview[0]) if overview[0] else 0
        blocked_pushes = int(overview[1]) if overview[1] else 0
        active_developers = int(overview[2]) if overview[2] else 0
        block_rate = float(overview[3]) if overview[3] else 0.0
        
        insights["overview"] = {
            "total_pushes": total_pushes,
            "blocked_pushes": blocked_pushes,
            "allowed_pushes": total_pushes - blocked_pushes,
            "active_developers": active_developers,
            "block_rate": round(block_rate, 2),
            "health_score": calculate_health(block_rate),
            "period_days": days
        }

        # ===================================
        # 2. SECURITY METRICS (Using severity column)
        # ===================================
        cursor.execute("""
            SELECT 
                COALESCE(severity, 'Unknown') AS severity,
                COUNT(*) AS count,
                SUM(is_blocked) AS blocked
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
            GROUP BY severity
        """, (project_name, days))
        
        severity_data = cursor.fetchall()
        severity_breakdown = {}
        for sev, cnt, blk in severity_data:
            # Convert to int to avoid Decimal issues
            count = int(cnt) if cnt else 0
            blocked = int(blk) if blk else 0
            
            severity_breakdown[sev] = {
                "total": count,
                "blocked": blocked,
                "allowed": count - blocked
            }
        
        insights["security_metrics"] = {
            "severity_breakdown": severity_breakdown,
            "critical_count": severity_breakdown.get("Critical", {}).get("total", 0),
            "high_count": severity_breakdown.get("High", {}).get("total", 0),
            "medium_count": severity_breakdown.get("Medium", {}).get("total", 0),
            "low_count": severity_breakdown.get("Low", {}).get("total", 0),
            "unknown_count": severity_breakdown.get("Unknown", {}).get("total", 0)
        }

        # ===================================
        # 3. VULNERABILITY BREAKDOWN (Using status and severity)
        # ===================================
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) AS occurrences,
                SUM(is_blocked) AS blocked,
                AVG(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) * 100 AS critical_rate
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
            GROUP BY status
            ORDER BY occurrences DESC
        """, (project_name, days))
        
        vuln_data = cursor.fetchall()
        vulnerability_types = []
        for status, occ, blk, crit_rate in vuln_data:
            # Convert to int/float to avoid Decimal issues
            occurrences = int(occ) if occ else 0
            blocked = int(blk) if blk else 0
            critical_rate = float(crit_rate) if crit_rate else 0.0
            
            vulnerability_types.append({
                "type": status,
                "occurrences": occurrences,
                "blocked": blocked,
                "block_rate": round((blocked / occurrences * 100), 2) if occurrences > 0 else 0.0,
                "critical_rate": round(critical_rate, 2)
            })
        
        insights["vulnerability_breakdown"] = {
            "types": vulnerability_types,
            "most_common": vulnerability_types[0]["type"] if vulnerability_types else "None",
            "total_types": len(vulnerability_types)
        }

        # ===================================
        # 4. TREND ANALYSIS (Weekly Comparison)
        # ===================================
        cursor.execute("""
            SELECT 
                WEEK(timestamp) AS week_num,
                COUNT(*) AS total,
                SUM(is_blocked) AS blocked,
                COUNT(DISTINCT user_name) AS developers
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
            GROUP BY WEEK(timestamp)
            ORDER BY week_num DESC
        """, (project_name, days))
        
        weekly_data = cursor.fetchall()
        weekly_trends = []
        for week, total, blocked, devs in weekly_data:
            # Convert to int/float to avoid Decimal type issues
            total = int(total) if total else 0
            blocked = int(blocked) if blocked else 0
            devs = int(devs) if devs else 0
            
            weekly_trends.append({
                "week": int(week) if week else 0,
                "total_pushes": total,
                "blocked": blocked,
                "block_rate": round((blocked / total * 100), 2) if total > 0 else 0.0,
                "developers": devs
            })
        
        # Calculate trend direction
        trend_direction = "stable"
        trend_percentage = 0.0
        if len(weekly_trends) >= 2:
            current_rate = float(weekly_trends[0]["block_rate"])
            previous_rate = float(weekly_trends[1]["block_rate"])
            if previous_rate > 0:
                trend_percentage = round(((current_rate - previous_rate) / previous_rate) * 100, 2)
                if trend_percentage > 15:
                    trend_direction = "increasing"
                elif trend_percentage < -15:
                    trend_direction = "decreasing"
        
        insights["trend_analysis"] = {
            "weekly_trends": weekly_trends,
            "direction": trend_direction,
            "percentage_change": trend_percentage,
            "is_improving": trend_direction == "decreasing"
        }

        # ===================================
        # 5. TEAM ANALYTICS
        # ===================================
        cursor.execute("""
            SELECT 
                user_name,
                COUNT(*) AS total_pushes,
                SUM(is_blocked) AS blocked,
                COUNT(DISTINCT status) AS violation_types,
                MAX(timestamp) AS last_activity
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
            GROUP BY user_name
            ORDER BY blocked DESC
        """, (project_name, days))
        
        team_data = cursor.fetchall()
        developer_stats = []
        total_team_blocks = 0
        
        for user, total, blocked, types, last_activity in team_data:
            # Convert to int to avoid Decimal issues
            total_pushes = int(total) if total else 0
            blocked_count = int(blocked) if blocked else 0
            violation_types = int(types) if types else 0
            
            total_team_blocks += blocked_count
            
            block_rate = round((blocked_count / total_pushes * 100), 2) if total_pushes > 0 else 0.0
            developer_stats.append({
                "developer": user,
                "total_pushes": total_pushes,
                "blocked": blocked_count,
                "block_rate": block_rate,
                "violation_types": violation_types,
                "last_activity": str(last_activity),
                "risk_level": "high" if block_rate > 20 else "medium" if block_rate > 10 else "low"
            })
        
        # Calculate team concentration
        top_3_blocks = sum(dev["blocked"] for dev in developer_stats[:3])
        concentration = round((top_3_blocks / total_team_blocks * 100), 2) if total_team_blocks > 0 else 0
        
        insights["team_analytics"] = {
            "developer_stats": developer_stats,
            "high_risk_developers": [d["developer"] for d in developer_stats if d["risk_level"] == "high"],
            "top_3_concentration": concentration,
            "needs_training": concentration > 70
        }

        # ===================================
        # 6. TEMPORAL PATTERNS
        # ===================================
        cursor.execute("""
            SELECT 
                DAYOFWEEK(timestamp) AS day_of_week,
                HOUR(timestamp) AS hour_of_day,
                COUNT(*) AS push_count,
                SUM(is_blocked) AS blocked_count
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
            GROUP BY DAYOFWEEK(timestamp), HOUR(timestamp)
            ORDER BY blocked_count DESC
            LIMIT 5
        """, (project_name, days))
        
        temporal_data = cursor.fetchall()
        high_risk_times = []
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for dow, hour, pushes, blocked in temporal_data:
            # Convert to int to avoid Decimal issues
            day_of_week = int(dow) if dow else 0
            hour_of_day = int(hour) if hour else 0
            push_count = int(pushes) if pushes else 0
            blocked_count = int(blocked) if blocked else 0
            
            high_risk_times.append({
                "day": day_names[day_of_week - 1] if day_of_week >= 1 and day_of_week <= 7 else "Unknown",
                "hour": hour_of_day,
                "pushes": push_count,
                "blocked": blocked_count,
                "block_rate": round((blocked_count / push_count * 100), 2) if push_count > 0 else 0.0
            })
        
        insights["temporal_patterns"] = {
            "high_risk_times": high_risk_times,
            "pattern_detected": len(high_risk_times) > 0
        }

        # ===================================
        # 7. USER ACTIVITY ANALYSIS (No branch_name column)
        # ===================================
        cursor.execute("""
            SELECT 
                user_name,
                COUNT(*) AS violations,
                SUM(is_blocked) AS blocked,
                COUNT(DISTINCT DATE(timestamp)) AS active_days,
                COUNT(DISTINCT status) AS violation_types
            FROM ai_git_guard_logs
            WHERE project_name = %s
              AND timestamp >= NOW() - INTERVAL %s DAY
              AND is_blocked = 1
            GROUP BY user_name
            ORDER BY violations DESC
            LIMIT 10
        """, (project_name, days))
        
        user_data = cursor.fetchall()
        insights["user_activity_analysis"] = []
        
        for user, viol, blk, active_days, types in user_data:
            # Convert to int to avoid Decimal issues
            violations = int(viol) if viol else 0
            blocked = int(blk) if blk else 0
            days = int(active_days) if active_days else 0
            violation_types = int(types) if types else 0
            
            insights["user_activity_analysis"].append({
                "user": user,
                "violations": violations,
                "blocked": blocked,
                "active_days": days,
                "violation_types": violation_types,
                "avg_violations_per_day": round(violations / days, 2) if days > 0 else 0.0
            })

        # ===================================
        # 8. RISK ASSESSMENT
        # ===================================
        risk_score = 0
        risk_factors = []
        
        # Factor 1: High block rate
        if insights["overview"]["block_rate"] > 15:
            risk_score += 30
            risk_factors.append("High block rate detected")
        elif insights["overview"]["block_rate"] > 10:
            risk_score += 15
            risk_factors.append("Elevated block rate")
        
        # Factor 2: Critical/High severity issues
        critical_high = (insights["security_metrics"]["critical_count"] + 
                        insights["security_metrics"]["high_count"])
        if critical_high > 10:
            risk_score += 35
            risk_factors.append("Multiple critical/high severity issues")
        elif critical_high > 5:
            risk_score += 20
            risk_factors.append("Several high severity issues present")
        
        # Factor 3: Increasing trend
        if insights["trend_analysis"]["direction"] == "increasing":
            risk_score += 25
            risk_factors.append("Increasing trend in violations")
        
        # Factor 4: Team concentration
        if insights["team_analytics"]["needs_training"]:
            risk_score += 10
            risk_factors.append("Violations concentrated in few developers")
        
        risk_level = "critical" if risk_score >= 70 else "high" if risk_score >= 50 else "medium" if risk_score >= 30 else "low"
        
        insights["risk_assessment"] = {
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "requires_immediate_action": risk_level in ["critical", "high"]
        }

        # ===================================
        # 9. INTELLIGENT RECOMMENDATIONS
        # ===================================
        recommendations = []
        
        # Secret management
        secret_issues = sum(1 for v in vulnerability_types if "secret" in v["type"].lower() or "credential" in v["type"].lower())
        if secret_issues > 0:
            recommendations.append({
                "priority": "high",
                "category": "Secret Management",
                "action": "Implement secret scanning in pre-commit hooks",
                "impact": "Prevent credential leaks before they reach the repository"
            })
            recommendations.append({
                "priority": "high",
                "category": "Secret Management",
                "action": "Migrate to HashiCorp Vault or AWS Secrets Manager",
                "impact": "Centralized secret management and rotation"
            })
        
        # Training needs
        if insights["overview"]["block_rate"] > 12:
            recommendations.append({
                "priority": "high",
                "category": "Training",
                "action": "Conduct secure coding workshop for all developers",
                "impact": "Reduce overall violation rate by 40-60%"
            })
        
        if len(insights["team_analytics"]["high_risk_developers"]) > 0:
            recommendations.append({
                "priority": "medium",
                "category": "Training",
                "action": f"Provide targeted training to: {', '.join(insights['team_analytics']['high_risk_developers'][:3])}",
                "impact": "Address concentrated risk areas"
            })
        
        # Code review process
        if insights["security_metrics"]["critical_count"] > 5:
            recommendations.append({
                "priority": "critical",
                "category": "Process",
                "action": "Implement mandatory security review for all PRs",
                "impact": "Catch critical issues before merge"
            })
        
        # Tool enhancement
        sql_injection = sum(1 for v in vulnerability_types if "sql" in v["type"].lower())
        if sql_injection > 0:
            recommendations.append({
                "priority": "high",
                "category": "Prevention",
                "action": "Enable automated SQL injection detection in IDE",
                "impact": "Real-time feedback during development"
            })
        
        # Branch protection (not available without branch_name)
        # Skipping branch-specific recommendations
        
        # Positive reinforcement
        if insights["overview"]["block_rate"] < 5 and insights["trend_analysis"]["is_improving"]:
            recommendations.append({
                "priority": "low",
                "category": "Recognition",
                "action": "Acknowledge team's excellent security practices",
                "impact": "Maintain and reinforce positive behavior"
            })
        
        insights["recommendations"] = sorted(recommendations, key=lambda x: 
            {"critical": 0, "high": 1, "medium": 2, "low": 3}[x["priority"]])

        # ===================================
        # 10. ALERTS (Critical Issues)
        # ===================================
        alerts = []
        
        if insights["security_metrics"]["critical_count"] > 0:
            alerts.append({
                "level": "critical",
                "message": f"{insights['security_metrics']['critical_count']} critical severity issues detected",
                "action_required": "Immediate review and remediation needed"
            })
        
        if insights["trend_analysis"]["direction"] == "increasing" and abs(insights["trend_analysis"]["percentage_change"]) > 50:
            alerts.append({
                "level": "warning",
                "message": f"Violations increased by {abs(insights['trend_analysis']['percentage_change'])}% recently",
                "action_required": "Investigate root cause"
            })
        
        if insights["overview"]["block_rate"] > 20:
            alerts.append({
                "level": "warning",
                "message": "Block rate exceeds 20% threshold",
                "action_required": "Review development practices and tooling"
            })
        
        insights["alerts"] = alerts

        # ===================================
        # 11. QUICK STATS FOR DASHBOARD
        # ===================================
        total_pushes = insights["overview"]["total_pushes"]
        blocked_pushes = insights["overview"]["blocked_pushes"]
        allowed_pushes = insights["overview"]["allowed_pushes"]
        active_developers = insights["overview"]["active_developers"]
        
        insights["quick_stats"] = {
            "total_violations": blocked_pushes,
            "resolution_rate": round((allowed_pushes / total_pushes * 100), 2) if total_pushes > 0 else 0.0,
            "avg_violations_per_developer": round(blocked_pushes / active_developers, 2) if active_developers > 0 else 0.0,
            "high_risk_users": len([u for u in insights["user_activity_analysis"] if u["violations"] > 5])
        }

        cursor.close()
        conn.close()

        return insights

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
