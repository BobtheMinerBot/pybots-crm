# ISLA CRM — PythonAnywhere Deployment Guide

This guide covers deploying the ISLA Dashboard and updating the existing CRM app to use the unified design system.

---

## Prerequisites

- PythonAnywhere account (free tier works for testing)
- JobTread API key (stored in `~/.config/jobtread/.env`)
- Files from `/Users/jb/clawd/projects/isla-crm/dashboard/`

---

## Part 1: Deploy the Dashboard

### Step 1: Upload Files

**Option A: Git (Recommended)**

1. Log into PythonAnywhere
2. Open a **Bash console**
3. Clone or pull from your repo:
   ```bash
   cd ~
   git clone https://github.com/YOUR_REPO/isla-crm.git
   # Or if already exists:
   cd isla-crm && git pull
   ```

**Option B: Manual Upload**

1. Go to **Files** tab in PythonAnywhere
2. Navigate to `/home/YOUR_USERNAME/`
3. Create folder: `isla-crm/dashboard/`
4. Upload these files:
   ```
   dashboard/
   ├── app.py
   ├── requirements.txt
   ├── templates/
   │   └── dashboard.html
   └── static/
       ├── css/
       │   └── style.css
       └── js/
           └── app.js
   ```

### Step 2: Set Up Virtual Environment

In a **Bash console**:

```bash
cd ~/isla-crm/dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a file for the JobTread API key:

```bash
mkdir -p ~/.config/jobtread
nano ~/.config/jobtread/.env
```

Add this line (replace with your actual key):
```
JOBTREAD_API_KEY=your_api_key_here
```

Save and exit (Ctrl+X, Y, Enter).

### Step 4: Create Web App

1. Go to **Web** tab in PythonAnywhere
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Flask)
4. Select **Python 3.10** (or latest)

### Step 5: Configure WSGI

1. In the Web tab, click on the **WSGI configuration file** link
2. Delete all contents and replace with:

```python
import sys
import os

# Add your project directory to the path
project_home = '/home/YOUR_USERNAME/isla-crm/dashboard'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['JOBTREAD_API_KEY'] = 'your_api_key_here'

# Import the Flask app
from app import app as application
```

**Replace `YOUR_USERNAME` with your PythonAnywhere username.**

### Step 6: Set Virtual Environment Path

In the **Web** tab, find **Virtualenv** section:
- Enter: `/home/YOUR_USERNAME/isla-crm/dashboard/venv`

### Step 7: Configure Static Files

In the **Web** tab, under **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/isla-crm/dashboard/static` |

### Step 8: Reload and Test

1. Click the green **Reload** button
2. Visit: `https://YOUR_USERNAME.pythonanywhere.com/`
3. You should see the ISLA Dashboard!

---

## Part 2: Update Existing CRM UI

If you have an existing CRM app on PythonAnywhere, update its styling to match.

### Step 1: Copy the Design System

Copy the CSS file to your existing CRM:

```bash
cp ~/isla-crm/dashboard/static/css/style.css ~/YOUR_EXISTING_CRM/static/css/isla-design.css
```

### Step 2: Update HTML Templates

In your existing CRM templates, add the design system CSS:

```html
<head>
  <!-- Add Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- Add ISLA Design System -->
  <link rel="stylesheet" href="{{ url_for('static', filename='css/isla-design.css') }}">
</head>
```

### Step 3: Update HTML Structure

Use these class names for consistent styling:

**Layout:**
```html
<div class="dashboard">
  <aside class="sidebar">...</aside>
  <main class="main">...</main>
</div>
```

**Cards:**
```html
<div class="card">
  <div class="card-header">
    <span class="card-title">Title</span>
    <a href="#" class="card-action">Action →</a>
  </div>
  <!-- Content -->
</div>
```

**Metrics:**
```html
<div class="metric-card">
  <div class="metric-label">Label</div>
  <div class="metric-value">123</div>
  <div class="metric-trend up">+12%</div>
</div>
```

**Tables:**
```html
<table>
  <thead>
    <tr><th>Column</th></tr>
  </thead>
  <tbody>
    <tr><td>Data</td></tr>
  </tbody>
</table>
```

**Badges:**
```html
<span class="badge new">New</span>
<span class="badge pending">Pending</span>
<span class="badge accepted">Accepted</span>
```

**Buttons:**
```html
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
```

---

## Part 3: Combine Into Single App (Recommended)

Instead of running two separate apps, merge them:

### Project Structure

```
isla-crm/
├── app.py                 # Main Flask app
├── requirements.txt
├── templates/
│   ├── base.html          # Shared layout with sidebar
│   ├── dashboard.html     # Dashboard page
│   ├── leads.html         # Leads management
│   ├── proposals.html     # Proposals list
│   ├── jobs.html          # Active jobs
│   └── settings.html      # Settings
├── static/
│   ├── css/
│   │   └── style.css      # Design system
│   └── js/
│       └── app.js         # Frontend JS
└── api/
    ├── jobtread.py        # JobTread API helpers
    └── crm.py             # CRM data helpers
```

### Base Template (templates/base.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}ISLA Builders{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  {% block head %}{% endblock %}
</head>
<body>
  <div class="dashboard">
    <aside class="sidebar">
      <!-- Sidebar content (same as dashboard.html) -->
      {% include 'partials/sidebar.html' %}
    </aside>
    
    <main class="main">
      {% block content %}{% endblock %}
    </main>
  </div>
  
  <script src="{{ url_for('static', filename='js/app.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

---

## Troubleshooting

### "Internal Server Error"

1. Check the **Error log** in PythonAnywhere Web tab
2. Common issues:
   - Missing environment variable
   - Import errors (check virtual environment)
   - File path issues

### "Static files not loading"

1. Verify the static files mapping in Web tab
2. Check file paths are correct
3. Reload the web app

### "API errors"

1. Verify JOBTREAD_API_KEY is set correctly
2. Check the API key hasn't expired
3. Test API directly: `curl https://api.jobtread.com/pave ...`

### Changes not showing

1. **Always click Reload** after making changes
2. Clear browser cache (Cmd+Shift+R)
3. Check you're editing the right files

---

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Reload app | Web tab → Green "Reload" button |
| View logs | Web tab → Error log / Access log |
| Edit files | Files tab → Navigate → Edit |
| Run console | Consoles tab → Bash |
| Check venv | `source ~/isla-crm/dashboard/venv/bin/activate` |

---

## Security Notes

- Never commit API keys to git
- Use environment variables for secrets
- PythonAnywhere free tier is HTTP only (consider paid for HTTPS)
- Restrict access if needed (add authentication)

---

*Built with the ISLA Design System. Craft & Consistency.* 🏗️
