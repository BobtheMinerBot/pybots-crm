# Construction CRM

A simple, self-hosted CRM for managing leads and customers. Built specifically for construction businesses with pipeline stages like estimating, proposals, and follow-ups.

## Features

- **Grid view grouped by stage** — See all leads organized by status (like SmartSuite)
- **Lead management** — Add, edit, view, and delete leads
- **Activity tracking** — Log notes and see status change history
- **Quick status updates** — Change lead status directly from the grid
- **Search & filter** — Find leads by name, email, address, or phone
- **Zapier webhook** — Automatically send new leads to Zapier (for JobTread integration)
- **Multi-user ready** — Authentication system built in

## Pipeline Stages

1. New Lead
2. Inspection Scheduled
3. Estimating
4. Proposal Sent
5. Follow Up
6. Nurturing
7. Lost

## Default Login

- **Email:** admin@example.com
- **Password:** changeme123

⚠️ **Change this immediately after first login!**

---

## Deploying to PythonAnywhere (Free/$5 tier)

### Step 1: Create Account
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a free account (or $5/month for custom domain + more power)

### Step 2: Upload Files
1. Go to **Files** tab
2. Create a new directory: `mysite` (or any name)
3. Upload all files from this folder:
   - `app.py`
   - `requirements.txt`
   - `templates/` folder (with all .html files)

### Step 3: Create Virtual Environment
1. Go to **Consoles** tab
2. Start a **Bash** console
3. Run these commands:

```bash
cd mysite
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "from app import init_db; init_db()"
```

### Step 4: Configure Web App
1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration** → **Python 3.10**
4. Set these values:

**Source code:** `/home/yourusername/mysite`

**Virtualenv:** `/home/yourusername/mysite/venv`

5. Edit the **WSGI configuration file** and replace ALL contents with:

```python
import sys
path = '/home/yourusername/mysite'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

6. Click **Reload** (green button)

### Step 5: Set Secret Key (Important for Security!)
1. Go to **Web** tab
2. Scroll to **Environment variables**
3. Add: `SECRET_KEY` = (generate a random string, like `your-super-secret-key-here-make-it-long`)

### Step 6: Visit Your Site
Your CRM is now live at: `https://yourusername.pythonanywhere.com`

---

## Setting Up Zapier Integration

1. Log into your CRM and go to **Settings**
2. Create a new Zap in Zapier with trigger: **Webhooks by Zapier** → **Catch Hook**
3. Copy the webhook URL Zapier gives you
4. Paste it into the **Zapier Webhook URL** field in Settings
5. Now when you add a new lead, it automatically sends to Zapier

### Webhook Payload

When a lead is created, this JSON is sent:

```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "305-555-1234",
  "address": "123 Ocean Dr, Key West, FL",
  "job_type": "Spalling Repair",
  "property_type": "Residential",
  "status": "New Lead",
  "notes": "Referred by neighbor",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## Adding More Users

Currently requires editing the database directly. In a Bash console:

```bash
cd mysite
source venv/bin/activate
python3
```

Then in Python:

```python
from app import app, execute_db, get_db
from werkzeug.security import generate_password_hash

with app.app_context():
    execute_db(
        'INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)',
        ('newuser@email.com', generate_password_hash('theirpassword'), 'Their Name', 'user')
    )
    print("User created!")
```

---

## Customizing Job Types / Property Types

Edit `app.py` and find these lists near the top:

```python
JOB_TYPES = [
    'Spalling Repair',
    'Remodel',
    'Seawall Repair',
    'Pool Deck',
    'Balcony Repair',
    'Other'
]

PROPERTY_TYPES = [
    'Residential',
    'Commercial',
    'Other'
]
```

Add or remove items as needed, then reload your web app.

---

## Backing Up Your Data

Your entire database is one file: `crm.db`

Download it periodically from the **Files** tab in PythonAnywhere.

---

## Future Enhancements (Phase 4+)

- Email reminders for follow-ups (using Resend free tier)
- CSV import/export
- More detailed reporting
- Mobile-optimized views

Let me know when you're ready to add these!
