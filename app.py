import os
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crm.db')

# Zapier webhook URL - set this in your environment or config
ZAPIER_WEBHOOK_URL = os.environ.get('ZAPIER_WEBHOOK_URL', '')

# Database helper functions
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    lastrowid = cur.lastrowid
    cur.close()
    return lastrowid

# Initialize database
def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                job_type TEXT,
                property_type TEXT,
                status TEXT DEFAULT 'New Lead',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                user_id INTEGER,
                note TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')
        
        # Create default admin if no users exist
        existing = query_db('SELECT id FROM users LIMIT 1', one=True)
        if not existing:
            execute_db(
                'INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)',
                ('admin@example.com', generate_password_hash('changeme123'), 'Admin', 'admin')
            )
            print("Default admin created: admin@example.com / changeme123")
        db.commit()

# Constants
STATUSES = [
    'New Lead',
    'Inspection Scheduled',
    'Estimating',
    'Proposal Sent',
    'Follow Up',
    'Nurturing',
    'Lost'
]

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

# Auth decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Zapier webhook function
def send_to_zapier(lead_dict):
    global ZAPIER_WEBHOOK_URL
    if ZAPIER_WEBHOOK_URL:
        try:
            import requests
            requests.post(ZAPIER_WEBHOOK_URL, json=lead_dict, timeout=5)
        except Exception as e:
            print(f"Zapier webhook error: {e}")

def lead_to_dict(lead):
    return {
        'id': lead['id'],
        'name': lead['name'],
        'email': lead['email'],
        'phone': lead['phone'],
        'address': lead['address'],
        'job_type': lead['job_type'],
        'property_type': lead['property_type'],
        'status': lead['status'],
        'notes': lead['notes'],
        'created_at': lead['created_at'],
        'updated_at': lead['updated_at']
    }

# Routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('leads'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = query_db('SELECT * FROM users WHERE email = ?', [email], one=True)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            return redirect(url_for('leads'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/leads')
@login_required
def leads():
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # Group leads by status
    leads_by_status = {}
    for status in STATUSES:
        if status_filter and status_filter != status:
            leads_by_status[status] = []
            continue
            
        query = 'SELECT * FROM leads WHERE status = ?'
        args = [status]
        
        if search:
            query += ' AND (name LIKE ? OR email LIKE ? OR address LIKE ? OR phone LIKE ?)'
            search_term = f'%{search}%'
            args.extend([search_term, search_term, search_term, search_term])
        
        query += ' ORDER BY created_at DESC'
        leads_by_status[status] = query_db(query, args)
    
    return render_template('leads.html', 
                         leads_by_status=leads_by_status, 
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         status_filter=status_filter,
                         search=search)

@app.route('/leads/add', methods=['GET', 'POST'])
@login_required
def add_lead():
    if request.method == 'POST':
        lead_id = execute_db(
            '''INSERT INTO leads (name, email, phone, address, job_type, property_type, status, notes, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                request.form.get('name'),
                request.form.get('email'),
                request.form.get('phone'),
                request.form.get('address'),
                request.form.get('job_type'),
                request.form.get('property_type'),
                request.form.get('status', 'New Lead'),
                request.form.get('notes'),
                session.get('user_id')
            )
        )
        
        # Get the created lead for webhook
        lead = query_db('SELECT * FROM leads WHERE id = ?', [lead_id], one=True)
        
        # Send to Zapier
        send_to_zapier(lead_to_dict(lead))
        
        # Log activity
        execute_db(
            'INSERT INTO activities (lead_id, user_id, note) VALUES (?, ?, ?)',
            (lead_id, session.get('user_id'), 'Lead created')
        )
        
        flash('Lead added successfully', 'success')
        return redirect(url_for('leads'))
    
    return render_template('lead_form.html', 
                         lead=None, 
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES)

@app.route('/leads/<int:id>')
@login_required
def view_lead(id):
    lead = query_db('SELECT * FROM leads WHERE id = ?', [id], one=True)
    if not lead:
        flash('Lead not found', 'error')
        return redirect(url_for('leads'))
    
    activities = query_db(
        'SELECT * FROM activities WHERE lead_id = ? ORDER BY created_at DESC',
        [id]
    )
    
    return render_template('lead_detail.html', 
                         lead=lead, 
                         activities=activities,
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES)

@app.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = query_db('SELECT * FROM leads WHERE id = ?', [id], one=True)
    if not lead:
        flash('Lead not found', 'error')
        return redirect(url_for('leads'))
    
    if request.method == 'POST':
        old_status = lead['status']
        new_status = request.form.get('status')
        
        execute_db(
            '''UPDATE leads SET name=?, email=?, phone=?, address=?, job_type=?, 
               property_type=?, status=?, notes=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?''',
            (
                request.form.get('name'),
                request.form.get('email'),
                request.form.get('phone'),
                request.form.get('address'),
                request.form.get('job_type'),
                request.form.get('property_type'),
                new_status,
                request.form.get('notes'),
                id
            )
        )
        
        # Log status change
        if old_status != new_status:
            execute_db(
                'INSERT INTO activities (lead_id, user_id, note) VALUES (?, ?, ?)',
                (id, session.get('user_id'), f'Status changed from "{old_status}" to "{new_status}"')
            )
        
        flash('Lead updated successfully', 'success')
        return redirect(url_for('view_lead', id=id))
    
    return render_template('lead_form.html', 
                         lead=lead, 
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES)

@app.route('/leads/<int:id>/delete', methods=['POST'])
@login_required
def delete_lead(id):
    execute_db('DELETE FROM activities WHERE lead_id = ?', [id])
    execute_db('DELETE FROM leads WHERE id = ?', [id])
    flash('Lead deleted successfully', 'success')
    return redirect(url_for('leads'))

@app.route('/leads/<int:id>/activity', methods=['POST'])
@login_required
def add_activity(id):
    note = request.form.get('note')
    
    if note:
        execute_db(
            'INSERT INTO activities (lead_id, user_id, note) VALUES (?, ?, ?)',
            (id, session.get('user_id'), note)
        )
        flash('Activity added', 'success')
    
    return redirect(url_for('view_lead', id=id))

@app.route('/leads/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    lead = query_db('SELECT * FROM leads WHERE id = ?', [id], one=True)
    if not lead:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Lead not found'}), 404
        flash('Lead not found', 'error')
        return redirect(url_for('leads'))
    
    new_status = request.form.get('status')
    
    if new_status in STATUSES:
        old_status = lead['status']
        execute_db('UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                   [new_status, id])
        
        execute_db(
            'INSERT INTO activities (lead_id, user_id, note) VALUES (?, ?, ?)',
            (id, session.get('user_id'), f'Status changed from "{old_status}" to "{new_status}"')
        )
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    return redirect(url_for('leads'))

# API endpoint for Zapier testing
@app.route('/api/leads', methods=['GET'])
@login_required
def api_leads():
    leads = query_db('SELECT * FROM leads ORDER BY created_at DESC')
    return jsonify([lead_to_dict(lead) for lead in leads])

# Settings page for Zapier webhook
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    global ZAPIER_WEBHOOK_URL
    if request.method == 'POST':
        ZAPIER_WEBHOOK_URL = request.form.get('zapier_webhook', '')
        flash('Settings saved', 'success')
    return render_template('settings.html', zapier_webhook=ZAPIER_WEBHOOK_URL)

# Template filters
@app.template_filter('strftime')
def strftime_filter(value, fmt='%b %d, %Y'):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    return value.strftime(fmt) if value else ''


# GitHub webhook for auto-deploy
DEPLOY_SECRET = os.environ.get('DEPLOY_SECRET', 'pybots-deploy-secret-2024')

@app.route('/api/deploy', methods=['POST'])
def github_deploy():
    import subprocess
    # Run deploy script
    try:
        subprocess.Popen(['/home/Pybots/deploy.sh'])
        return jsonify({'status': 'Deployment started'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
