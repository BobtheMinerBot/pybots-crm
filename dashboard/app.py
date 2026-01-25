"""
ISLA Builders Dashboard
Flask application for project management and business overview
"""

import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify
from pathlib import Path

app = Flask(__name__)

# Configuration
JOBTREAD_API = "https://api.jobtread.com/pave"
JOBTREAD_ORG_ID = "22NiF3LC97Ff"
CRM_DATA_PATH = Path(__file__).parent.parent / "data"

def get_jobtread_key():
    """Load JobTread API key from environment file"""
    env_path = Path.home() / ".config" / "jobtread" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("JOBTREAD_API_KEY="):
                    return line.strip().split("=", 1)[1].strip('"\'')
    return os.environ.get("JOBTREAD_API_KEY")

def jobtread_query(query):
    """Execute a JobTread GraphQL-style query"""
    api_key = get_jobtread_key()
    if not api_key:
        return {"error": "No API key configured"}
    
    query["$"] = {"grantKey": api_key}
    
    try:
        response = requests.post(
            JOBTREAD_API,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def load_crm_data(filename):
    """Load data from CRM JSON files"""
    filepath = CRM_DATA_PATH / filename
    if filepath.exists():
        with open(filepath) as f:
            return json.load(f)
    return {}

# Routes
@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template("dashboard.html", active_page="dashboard")

@app.route("/leads")
def leads():
    """Leads management page"""
    return render_template("leads.html", active_page="leads")

@app.route("/proposals")
def proposals():
    """Proposals page"""
    return render_template("proposals.html", active_page="proposals")

@app.route("/jobs")
def jobs():
    """Active jobs page"""
    return render_template("jobs.html", active_page="jobs")

@app.route("/schedule")
def schedule():
    """Schedule page"""
    return render_template("schedule.html", active_page="schedule")

@app.route("/invoices")
def invoices():
    """Invoices page"""
    return render_template("invoices.html", active_page="invoices")

@app.route("/reports")
def reports():
    """Reports page"""
    return render_template("reports.html", active_page="reports")

@app.route("/settings")
def settings():
    """Settings page"""
    return render_template("settings.html", active_page="settings")

@app.route("/api/overview")
def api_overview():
    """Get business overview metrics"""
    # Load CRM leads
    leads_data = load_crm_data("leads.json")
    leads = leads_data.get("leads", [])
    
    # Count by status
    status_counts = {}
    for lead in leads:
        status = lead.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # This month's metrics (placeholder - will connect to JobTread)
    today = datetime.now()
    month_start = today.replace(day=1)
    
    return jsonify({
        "leads": {
            "total": len(leads),
            "by_status": status_counts,
            "new_this_week": sum(1 for l in leads if l.get("status") == "new")
        },
        "pipeline": {
            "active_leads": status_counts.get("new", 0) + status_counts.get("contacted", 0),
            "site_visits_scheduled": status_counts.get("site_scheduled", 0),
            "estimates_pending": status_counts.get("estimate_sent", 0)
        },
        "updated_at": datetime.now().isoformat()
    })

@app.route("/api/jobs")
def api_jobs():
    """Get active (open) jobs from JobTread - jobs where closedOn is null"""
    query = {
        "organization": {
            "$": {"id": JOBTREAD_ORG_ID},
            "jobs": {
                "$": {
                    "where": {"and": [["closedOn", "=", None]]},
                    "size": 100
                },
                "nodes": {
                    "id": {},
                    "name": {},
                    "number": {},
                    "createdAt": {},
                    "closedOn": {},
                    "status": {},
                    "location": {
                        "address": {},
                        "account": {
                            "name": {}
                        }
                    }
                }
            }
        }
    }
    
    result = jobtread_query(query)
    
    if "error" in result:
        return jsonify({"error": result["error"], "jobs": [], "count": 0})
    
    jobs = result.get("organization", {}).get("jobs", {}).get("nodes", [])
    
    # Process jobs for display (sort by createdAt in Python since Pave doesn't support sort)
    processed = []
    for job in jobs:
        location = job.get("location", {}) or {}
        account = location.get("account", {}) or {}
        processed.append({
            "id": job.get("id"),
            "number": job.get("number"),
            "name": job.get("name"),
            "client": account.get("name", "Unknown"),
            "address": location.get("address", "No address"),
            "status": job.get("status", "unknown"),
            "created": job.get("createdAt"),
            "closed": job.get("closedOn")
        })
    
    # Sort by created date descending
    processed.sort(key=lambda x: x.get("created") or "", reverse=True)
    
    return jsonify({"jobs": processed, "count": len(processed)})

@app.route("/api/proposals")
def api_proposals():
    """Get proposals from JobTread"""
    query = {
        "organization": {
            "$": {"id": JOBTREAD_ORG_ID},
            "documents": {
                "$": {
                    "where": {"and": [["type", "=", "customerOrder"]]},
                    "size": 50
                },
                "nodes": {
                    "id": {},
                    "name": {},
                    "number": {},
                    "status": {},
                    "createdAt": {},
                    "cost": {},
                    "price": {},
                    "job": {
                        "name": {}
                    }
                }
            }
        }
    }
    
    result = jobtread_query(query)
    
    if "error" in result:
        return jsonify({"error": result["error"], "proposals": [], "summary": {}})
    
    docs = result.get("organization", {}).get("documents", {}).get("nodes", [])
    
    # Process proposals
    processed = []
    
    # Map JobTread statuses to our display statuses
    status_map = {
        "pending": "pending",
        "approved": "accepted", 
        "denied": "declined"
    }
    
    pending_value = 0
    won_value = 0
    
    for doc in docs:
        job = doc.get("job", {}) or {}
        raw_status = doc.get("status", "unknown")
        status = status_map.get(raw_status, raw_status)
        price = doc.get("price", 0) or 0
        
        # Track values for summary
        if status == "pending":
            pending_value += price
        elif status == "accepted":
            won_value += price
        
        processed.append({
            "id": doc.get("id"),
            "number": doc.get("number"),
            "name": doc.get("name"),
            "client": job.get("name", "Unknown"),
            "status": status,
            "total": price,
            "cost": doc.get("cost", 0) or 0,
            "created": doc.get("createdAt")
        })
    
    # Sort by created date descending
    processed.sort(key=lambda x: x.get("created") or "", reverse=True)
    
    return jsonify({
        "proposals": processed,
        "summary": {
            "pending_count": sum(1 for p in processed if p["status"] == "pending"),
            "pending_value": pending_value,
            "won_count": sum(1 for p in processed if p["status"] == "accepted"),
            "won_value": won_value
        }
    })

@app.route("/api/leads")
def api_leads():
    """Get leads from CRM"""
    leads_data = load_crm_data("leads.json")
    leads = leads_data.get("leads", [])
    
    return jsonify({"leads": leads})

@app.route("/api/stats")
def api_stats():
    """Get aggregate stats from JobTread"""
    # Query for open jobs (closedOn is null) - get IDs only for counting
    # API limit is 100 per request, so we may undercount if > 100
    open_jobs_query = {
        "organization": {
            "$": {"id": JOBTREAD_ORG_ID},
            "jobs": {
                "$": {
                    "where": {"and": [["closedOn", "=", None]]},
                    "size": 100
                },
                "nodes": {"id": {}}
            }
        }
    }
    
    # Query for all jobs (for comparison)
    all_jobs_query = {
        "organization": {
            "$": {"id": JOBTREAD_ORG_ID},
            "jobs": {
                "$": {"size": 100},
                "nodes": {"id": {}}
            }
        }
    }
    
    open_result = jobtread_query(open_jobs_query)
    all_result = jobtread_query(all_jobs_query)
    
    open_count = 0
    total_count = 0
    
    if "error" not in open_result:
        open_nodes = open_result.get("organization", {}).get("jobs", {}).get("nodes", [])
        open_count = len(open_nodes)
    
    if "error" not in all_result:
        all_nodes = all_result.get("organization", {}).get("jobs", {}).get("nodes", [])
        total_count = len(all_nodes)
    
    return jsonify({
        "jobs": {
            "open": open_count,
            "total": total_count,
            "closed": total_count - open_count
        }
    })

@app.route("/api/calendar")
def api_calendar():
    """Get today's calendar events (placeholder)"""
    # This will integrate with Google Calendar via gog
    # For now, return placeholder
    return jsonify({
        "events": [],
        "message": "Calendar integration pending"
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
