"""
JobTread API Integration for ISLA CRM Dashboard
"""
import os
import json
import requests
from datetime import datetime, timedelta
from functools import lru_cache
import time

# Configuration
JOBTREAD_API_URL = "https://api.jobtread.com/pave"
JOBTREAD_ORG_ID = "22NiF3LC97Ff"
JOBTREAD_API_KEY = os.environ.get('JOBTREAD_API_KEY', '')

# Cache timeout (5 minutes)
_cache = {}
_cache_timeout = 300  # seconds


def _get_api_key():
    """Get API key from env or file"""
    if JOBTREAD_API_KEY:
        return JOBTREAD_API_KEY
    
    # Try loading from file
    env_path = os.path.expanduser('~/.config/jobtread/.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('JOBTREAD_API_KEY='):
                    return line.strip().split('=', 1)[1]
    return ''


def _make_request(query_body):
    """Make authenticated request to JobTread API"""
    api_key = _get_api_key()
    if not api_key:
        return {'error': 'No API key configured'}
    
    # Add auth to query
    if '$' not in query_body.get('query', {}):
        query_body['query']['$'] = {}
    query_body['query']['$']['grantKey'] = api_key
    query_body['query']['$']['timeZone'] = 'America/New_York'
    
    try:
        response = requests.post(
            JOBTREAD_API_URL,
            headers={'Content-Type': 'application/json'},
            json=query_body,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {'error': str(e)}


def _cached_request(cache_key, query_body):
    """Make a cached API request"""
    now = time.time()
    
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if now - timestamp < _cache_timeout:
            return data
    
    result = _make_request(query_body)
    if 'error' not in result:
        _cache[cache_key] = (result, now)
    return result


def get_active_jobs(limit=20):
    """Get active (non-closed) jobs"""
    query = {
        "query": {
            "organization": {
                "$": {"id": JOBTREAD_ORG_ID},
                "jobs": {
                    "$": {
                        "where": ["closedOn", "=", None],
                        "size": limit,
                        "sortBy": [{"field": "createdAt", "order": "desc"}]
                    },
                    "nodes": {
                        "id": {},
                        "name": {},
                        "number": {},
                        "createdAt": {},
                        "location": {
                            "name": {},
                            "address": {},
                            "account": {
                                "name": {}
                            }
                        }
                    }
                }
            }
        }
    }
    
    result = _cached_request('active_jobs', query)
    if 'error' in result:
        return []
    
    try:
        jobs = result.get('organization', {}).get('jobs', {}).get('nodes', [])
        return jobs
    except (KeyError, TypeError):
        return []


def get_job_stats():
    """Get job statistics - active count, total revenue, etc."""
    # Get all jobs for stats
    query = {
        "query": {
            "organization": {
                "$": {"id": JOBTREAD_ORG_ID},
                "jobs": {
                    "$": {"size": 200},
                    "nodes": {
                        "id": {},
                        "name": {},
                        "closedOn": {},
                        "createdAt": {}
                    }
                }
            }
        }
    }
    
    result = _cached_request('job_stats', query)
    if 'error' in result:
        return {
            'active_jobs': 0,
            'closed_jobs': 0,
            'total_jobs': 0,
            'jobs_this_month': 0
        }
    
    try:
        jobs = result.get('organization', {}).get('jobs', {}).get('nodes', [])
        
        active = sum(1 for j in jobs if not j.get('closedOn'))
        closed = sum(1 for j in jobs if j.get('closedOn'))
        
        # Jobs created this month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()
        this_month = sum(1 for j in jobs if j.get('createdAt', '') >= month_start)
        
        return {
            'active_jobs': active,
            'closed_jobs': closed,
            'total_jobs': len(jobs),
            'jobs_this_month': this_month
        }
    except (KeyError, TypeError):
        return {
            'active_jobs': 0,
            'closed_jobs': 0,
            'total_jobs': 0,
            'jobs_this_month': 0
        }


def get_recent_documents(doc_type='proposal', limit=10):
    """
    Get recent documents (proposals, invoices, etc.)
    doc_type: proposal, invoice, bill, purchase_order
    """
    query = {
        "query": {
            "organization": {
                "$": {"id": JOBTREAD_ORG_ID},
                "documents": {
                    "$": {
                        "where": ["type", "=", doc_type],
                        "size": limit,
                        "sortBy": [{"field": "createdAt", "order": "desc"}]
                    },
                    "nodes": {
                        "id": {},
                        "number": {},
                        "type": {},
                        "status": {},
                        "total": {},
                        "createdAt": {},
                        "job": {
                            "name": {},
                            "number": {}
                        }
                    }
                }
            }
        }
    }
    
    result = _cached_request(f'documents_{doc_type}', query)
    if 'error' in result:
        return []
    
    try:
        docs = result.get('organization', {}).get('documents', {}).get('nodes', [])
        return docs
    except (KeyError, TypeError):
        return []


def get_financial_summary():
    """Get financial summary - proposal totals, invoice totals, etc."""
    # Get proposals
    proposals_query = {
        "query": {
            "organization": {
                "$": {"id": JOBTREAD_ORG_ID},
                "documents": {
                    "$": {
                        "where": ["type", "=", "proposal"],
                        "size": 100
                    },
                    "nodes": {
                        "id": {},
                        "status": {},
                        "total": {}
                    }
                }
            }
        }
    }
    
    invoices_query = {
        "query": {
            "organization": {
                "$": {"id": JOBTREAD_ORG_ID},
                "documents": {
                    "$": {
                        "where": ["type", "=", "invoice"],
                        "size": 100
                    },
                    "nodes": {
                        "id": {},
                        "status": {},
                        "total": {}
                    }
                }
            }
        }
    }
    
    proposals_result = _cached_request('financial_proposals', proposals_query)
    invoices_result = _cached_request('financial_invoices', invoices_query)
    
    summary = {
        'proposals_pending': 0,
        'proposals_pending_value': 0,
        'proposals_approved': 0,
        'proposals_approved_value': 0,
        'invoices_outstanding': 0,
        'invoices_outstanding_value': 0,
        'invoices_paid': 0,
        'invoices_paid_value': 0
    }
    
    try:
        proposals = proposals_result.get('organization', {}).get('documents', {}).get('nodes', [])
        for p in proposals:
            total = float(p.get('total', 0) or 0)
            status = (p.get('status') or '').lower()
            if status in ['pending', 'sent', 'draft']:
                summary['proposals_pending'] += 1
                summary['proposals_pending_value'] += total
            elif status in ['approved', 'accepted']:
                summary['proposals_approved'] += 1
                summary['proposals_approved_value'] += total
    except (KeyError, TypeError):
        pass
    
    try:
        invoices = invoices_result.get('organization', {}).get('documents', {}).get('nodes', [])
        for i in invoices:
            total = float(i.get('total', 0) or 0)
            status = (i.get('status') or '').lower()
            if status in ['sent', 'pending', 'overdue']:
                summary['invoices_outstanding'] += 1
                summary['invoices_outstanding_value'] += total
            elif status in ['paid', 'complete']:
                summary['invoices_paid'] += 1
                summary['invoices_paid_value'] += total
    except (KeyError, TypeError):
        pass
    
    return summary


def get_upcoming_tasks(limit=10):
    """Get upcoming tasks across all jobs"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    query = {
        "query": {
            "organization": {
                "$": {"id": JOBTREAD_ORG_ID},
                "tasks": {
                    "$": {
                        "where": {
                            "and": [
                                ["startDate", ">=", today],
                                ["completedAt", "=", None]
                            ]
                        },
                        "size": limit,
                        "sortBy": [{"field": "startDate", "order": "asc"}]
                    },
                    "nodes": {
                        "id": {},
                        "name": {},
                        "startDate": {},
                        "endDate": {},
                        "job": {
                            "name": {},
                            "number": {}
                        }
                    }
                }
            }
        }
    }
    
    result = _cached_request('upcoming_tasks', query)
    if 'error' in result:
        return []
    
    try:
        tasks = result.get('organization', {}).get('tasks', {}).get('nodes', [])
        return tasks
    except (KeyError, TypeError):
        return []


def clear_cache():
    """Clear the API cache"""
    global _cache
    _cache = {}


# Combined dashboard data function
def get_dashboard_data():
    """Get all JobTread data needed for dashboard in one call"""
    return {
        'job_stats': get_job_stats(),
        'active_jobs': get_active_jobs(limit=5),
        'financial_summary': get_financial_summary(),
        'recent_proposals': get_recent_documents('proposal', limit=5),
        'upcoming_tasks': get_upcoming_tasks(limit=5)
    }
