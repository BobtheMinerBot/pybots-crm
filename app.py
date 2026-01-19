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
            
            CREATE TABLE IF NOT EXISTS custom_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                field_key TEXT UNIQUE NOT NULL,
                field_type TEXT NOT NULL,
                options TEXT,
                is_required BOOLEAN DEFAULT 0,
                default_value TEXT,
                sequence INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS field_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                field_id INTEGER NOT NULL,
                value TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE,
                FOREIGN KEY (field_id) REFERENCES custom_fields (id) ON DELETE CASCADE,
                UNIQUE(lead_id, field_id)
            );
            
            CREATE TABLE IF NOT EXISTS field_visibility (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                field_id INTEGER NOT NULL,
                is_visible BOOLEAN DEFAULT 1,
                sequence INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (field_id) REFERENCES custom_fields (id) ON DELETE CASCADE,
                UNIQUE(user_id, field_id)
            );

            CREATE TABLE IF NOT EXISTS views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                default_fields TEXT DEFAULT '["email","phone","address","job_type","property_type"]',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS view_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                view_id INTEGER NOT NULL,
                field_id INTEGER NOT NULL,
                sequence INTEGER DEFAULT 0,
                FOREIGN KEY (view_id) REFERENCES views (id) ON DELETE CASCADE,
                FOREIGN KEY (field_id) REFERENCES custom_fields (id) ON DELETE CASCADE,
                UNIQUE(view_id, field_id)
            );

            CREATE TABLE IF NOT EXISTS user_view_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                current_view_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (current_view_id) REFERENCES views (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT
            );
        ''')

        # Migration: Add default_fields column to views if it doesn't exist
        try:
            db.execute("SELECT default_fields FROM views LIMIT 1")
        except:
            db.execute("ALTER TABLE views ADD COLUMN default_fields TEXT DEFAULT '[\"email\",\"phone\",\"address\",\"job_type\",\"property_type\"]'")
            print("Added default_fields column to views table")

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

# Custom field types
FIELD_TYPES = {
    'text': {'label': 'Text', 'icon': '📝'},
    'number': {'label': 'Number', 'icon': '🔢'},
    'date': {'label': 'Date', 'icon': '📅'},
    'dropdown': {'label': 'Dropdown', 'icon': '📋'},
    'multi_select': {'label': 'Multi-Select', 'icon': '☑️'},
    'checkbox': {'label': 'Checkbox', 'icon': '✓'},
    'contact': {'label': 'Contact', 'icon': '👤'},
    'duration': {'label': 'Duration', 'icon': '⏱️'},
    'auto_number': {'label': 'Auto-Number', 'icon': '#'},
    'symbol': {'label': 'Symbol', 'icon': '⭐'}
}

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
    
    # Get all custom fields for the field selector
    user_id = session.get('user_id')
    all_custom_fields = get_custom_fields()

    # Check if user has a view selected
    current_view = get_user_current_view(user_id)
    all_views = get_all_views()

    # Determine visible fields based on view or default (show all)
    import json
    if current_view:
        # Get default fields from view
        visible_default_fields = json.loads(current_view['default_fields'] or '[]')
        # Get custom field IDs from view
        view_custom_fields = get_fields_for_view(current_view['id'])
        visible_custom_field_ids = [f['id'] for f in view_custom_fields]
    else:
        # Show all fields by default
        visible_default_fields = ['email', 'phone', 'address', 'job_type', 'property_type']
        visible_custom_field_ids = [f['id'] for f in all_custom_fields]

    # Get custom field values for all leads
    all_lead_values = {}
    for status_leads in leads_by_status.values():
        for lead in status_leads:
            all_lead_values[lead['id']] = get_field_values(lead['id'])

    return render_template('leads.html',
                         leads_by_status=leads_by_status,
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         status_filter=status_filter,
                         search=search,
                         all_custom_fields=all_custom_fields,
                         visible_custom_field_ids=visible_custom_field_ids,
                         visible_default_fields=visible_default_fields,
                         field_values=all_lead_values,
                         all_views=all_views,
                         current_view=current_view)

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
        
        # Save custom field values
        save_field_values(lead_id, request.form)
        
        # Log activity
        execute_db(
            'INSERT INTO activities (lead_id, user_id, note) VALUES (?, ?, ?)',
            (lead_id, session.get('user_id'), 'Lead created')
        )
        
        flash('Lead added successfully', 'success')
        return redirect(url_for('leads'))
    
    custom_fields = get_custom_fields()
    return render_template('lead_form.html', 
                         lead=None, 
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         custom_fields=custom_fields,
                         field_values={})

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
    
    custom_fields = get_custom_fields()
    field_values = get_field_values(id)
    
    return render_template('lead_detail.html', 
                         lead=lead, 
                         activities=activities,
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         custom_fields=custom_fields,
                         field_values=field_values)

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
        
        # Save custom field values
        save_field_values(id, request.form)
        
        flash('Lead updated successfully', 'success')
        return redirect(url_for('view_lead', id=id))
    
    custom_fields = get_custom_fields()
    field_values = get_field_values(id)
    
    return render_template('lead_form.html', 
                         lead=lead, 
                         statuses=STATUSES,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         custom_fields=custom_fields,
                         field_values=field_values)

@app.route('/leads/<int:id>/delete', methods=['POST'])
@login_required
def delete_lead(id):
    execute_db('DELETE FROM field_values WHERE lead_id = ?', [id])
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

# API endpoint for fetching leads (supports API key authentication)
@app.route('/api/leads', methods=['GET'])
def api_leads():
    # Check for API key authentication
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        # Validate API key
        settings = query_db('SELECT value FROM app_settings WHERE key = ?', ['api_key'], one=True)
        if settings and settings['value'] == api_key:
            leads = query_db('SELECT * FROM leads ORDER BY created_at DESC')
            return jsonify([lead_to_dict(lead) for lead in leads])
        return jsonify({'error': 'Invalid API key'}), 401

    # Fall back to session authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    leads = query_db('SELECT * FROM leads ORDER BY created_at DESC')
    return jsonify([lead_to_dict(lead) for lead in leads])

# API endpoint for creating leads via webhook (supports API key authentication)
@app.route('/api/leads', methods=['POST'])
def api_create_lead():
    # Check for API key authentication
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        settings = query_db('SELECT value FROM app_settings WHERE key = ?', ['api_key'], one=True)
        if not settings or settings['value'] != api_key:
            return jsonify({'error': 'Invalid API key'}), 401
    elif 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}

    # Validate required field
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Create the lead
    lead_id = execute_db(
        '''INSERT INTO leads (name, email, phone, address, job_type, property_type, status, notes, created_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            name,
            data.get('email', ''),
            data.get('phone', ''),
            data.get('address', ''),
            data.get('job_type', ''),
            data.get('property_type', ''),
            data.get('status', 'New Lead'),
            data.get('notes', ''),
            None  # Created by API
        )
    )

    # Get the created lead
    lead = query_db('SELECT * FROM leads WHERE id = ?', [lead_id], one=True)

    # Send to Zapier if webhook is configured
    send_to_zapier(lead_to_dict(lead))

    return jsonify({'success': True, 'lead': lead_to_dict(lead)}), 201

# Settings page for Zapier webhook
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    global ZAPIER_WEBHOOK_URL
    if request.method == 'POST':
        if 'zapier_webhook' in request.form:
            ZAPIER_WEBHOOK_URL = request.form.get('zapier_webhook', '')
            flash('Webhook settings saved', 'success')

    # Get current user info
    user = query_db('SELECT * FROM users WHERE id = ?', [session.get('user_id')], one=True)
    # Get all users for user management
    users = query_db('SELECT id, email, name, role, created_at FROM users ORDER BY name')
    # Get API key
    api_key_setting = query_db('SELECT value FROM app_settings WHERE key = ?', ['api_key'], one=True)
    api_key = api_key_setting['value'] if api_key_setting else None

    return render_template('settings.html',
                          zapier_webhook=ZAPIER_WEBHOOK_URL,
                          user=user,
                          users=users,
                          api_key=api_key)

@app.route('/settings/generate-api-key', methods=['POST'])
@login_required
def generate_api_key():
    import secrets
    new_key = secrets.token_urlsafe(32)

    # Upsert the API key
    existing = query_db('SELECT id FROM app_settings WHERE key = ?', ['api_key'], one=True)
    if existing:
        execute_db('UPDATE app_settings SET value = ? WHERE key = ?', [new_key, 'api_key'])
    else:
        execute_db('INSERT INTO app_settings (key, value) VALUES (?, ?)', ['api_key', new_key])

    flash('New API key generated', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/revoke-api-key', methods=['POST'])
@login_required
def revoke_api_key():
    execute_db('DELETE FROM app_settings WHERE key = ?', ['api_key'])
    flash('API key revoked', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_password or not new_password:
        flash('All password fields are required', 'error')
        return redirect(url_for('settings'))

    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('settings'))

    if len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('settings'))

    # Verify current password
    user = query_db('SELECT * FROM users WHERE id = ?', [session.get('user_id')], one=True)
    if not check_password_hash(user['password_hash'], current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('settings'))

    # Update password
    execute_db('UPDATE users SET password_hash = ? WHERE id = ?',
               [generate_password_hash(new_password), session.get('user_id')])
    flash('Password changed successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/change-email', methods=['POST'])
@login_required
def change_email():
    new_email = request.form.get('new_email', '').strip().lower()
    password = request.form.get('password_for_email', '')

    if not new_email or not password:
        flash('Email and password are required', 'error')
        return redirect(url_for('settings'))

    # Verify password
    user = query_db('SELECT * FROM users WHERE id = ?', [session.get('user_id')], one=True)
    if not check_password_hash(user['password_hash'], password):
        flash('Password is incorrect', 'error')
        return redirect(url_for('settings'))

    # Check if email already exists
    existing = query_db('SELECT id FROM users WHERE email = ? AND id != ?',
                        [new_email, session.get('user_id')], one=True)
    if existing:
        flash('Email already in use by another account', 'error')
        return redirect(url_for('settings'))

    # Update email
    execute_db('UPDATE users SET email = ? WHERE id = ?', [new_email, session.get('user_id')])
    flash('Email changed successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/change-name', methods=['POST'])
@login_required
def change_name():
    new_name = request.form.get('new_name', '').strip()

    if not new_name:
        flash('Name is required', 'error')
        return redirect(url_for('settings'))

    execute_db('UPDATE users SET name = ? WHERE id = ?', [new_name, session.get('user_id')])
    session['user_name'] = new_name
    flash('Name changed successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/users/add', methods=['POST'])
@login_required
def add_user():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    role = request.form.get('role', 'user')

    if not name or not email or not password:
        flash('Name, email, and password are required', 'error')
        return redirect(url_for('settings'))

    if len(password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('settings'))

    # Check if email already exists
    existing = query_db('SELECT id FROM users WHERE email = ?', [email], one=True)
    if existing:
        flash('A user with this email already exists', 'error')
        return redirect(url_for('settings'))

    execute_db('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
               [name, email, generate_password_hash(password), role])
    flash(f'User {name} added successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    # Don't allow deleting yourself
    if id == session.get('user_id'):
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('settings'))

    # Don't allow deleting the last user
    user_count = query_db('SELECT COUNT(*) as count FROM users', one=True)['count']
    if user_count <= 1:
        flash('Cannot delete the last user', 'error')
        return redirect(url_for('settings'))

    execute_db('DELETE FROM users WHERE id = ?', [id])
    flash('User deleted successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/users/<int:id>/reset-password', methods=['POST'])
@login_required
def reset_user_password(id):
    new_password = request.form.get('new_password', '')

    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters', 'error')
        return redirect(url_for('settings'))

    execute_db('UPDATE users SET password_hash = ? WHERE id = ?',
               [generate_password_hash(new_password), id])

    user = query_db('SELECT name FROM users WHERE id = ?', [id], one=True)
    flash(f'Password reset for {user["name"]}', 'success')
    return redirect(url_for('settings'))

# ==================== CUSTOM FIELDS ====================

def slugify(text):
    """Convert text to a URL-safe slug"""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text

def get_custom_fields():
    """Get all custom fields ordered by sequence"""
    return query_db('SELECT * FROM custom_fields ORDER BY sequence, id')

def get_visible_fields(user_id):
    """Get fields visible to a specific user with their visibility settings"""
    fields = query_db('''
        SELECT cf.*, 
               COALESCE(fv.is_visible, 1) as is_visible,
               COALESCE(fv.sequence, cf.sequence) as user_sequence
        FROM custom_fields cf
        LEFT JOIN field_visibility fv ON cf.id = fv.field_id AND fv.user_id = ?
        ORDER BY COALESCE(fv.sequence, cf.sequence), cf.id
    ''', [user_id])
    return fields

def get_field_values(lead_id):
    """Get all custom field values for a lead as a dictionary"""
    values = query_db('''
        SELECT cf.field_key, fv.value, cf.field_type
        FROM field_values fv
        JOIN custom_fields cf ON fv.field_id = cf.id
        WHERE fv.lead_id = ?
    ''', [lead_id])
    return {v['field_key']: {'value': v['value'], 'type': v['field_type']} for v in values}

def save_field_values(lead_id, form_data):
    """Save custom field values from form submission"""
    fields = get_custom_fields()
    for field in fields:
        field_key = f"custom_{field['field_key']}"
        value = form_data.get(field_key, '')
        
        # Handle multi-select (comes as list)
        if field['field_type'] == 'multi_select':
            values = form_data.getlist(field_key)
            value = json.dumps(values) if values else ''
        
        # Handle checkbox
        if field['field_type'] == 'checkbox':
            value = '1' if value else '0'
        
        # Upsert the value
        existing = query_db(
            'SELECT id FROM field_values WHERE lead_id = ? AND field_id = ?',
            [lead_id, field['id']], one=True
        )
        
        if existing:
            execute_db(
                'UPDATE field_values SET value = ? WHERE lead_id = ? AND field_id = ?',
                [value, lead_id, field['id']]
            )
        else:
            execute_db(
                'INSERT INTO field_values (lead_id, field_id, value) VALUES (?, ?, ?)',
                [lead_id, field['id'], value]
            )

# Views Helper Functions
def get_all_views():
    """Get all views ordered by name"""
    return query_db('SELECT * FROM views ORDER BY name')

def get_view_by_id(view_id):
    """Get a single view by ID"""
    return query_db('SELECT * FROM views WHERE id = ?', [view_id], one=True)

def get_fields_for_view(view_id):
    """Get all fields associated with a view, ordered by sequence"""
    return query_db('''
        SELECT cf.*, vf.sequence as view_sequence
        FROM custom_fields cf
        JOIN view_fields vf ON cf.id = vf.field_id
        WHERE vf.view_id = ?
        ORDER BY vf.sequence, cf.id
    ''', [view_id])

def get_user_current_view(user_id):
    """Get the user's currently selected view"""
    pref = query_db('''
        SELECT v.* FROM views v
        JOIN user_view_preferences uvp ON v.id = uvp.current_view_id
        WHERE uvp.user_id = ?
    ''', [user_id], one=True)
    return pref

def set_user_current_view(user_id, view_id):
    """Set the user's current view preference"""
    existing = query_db(
        'SELECT id FROM user_view_preferences WHERE user_id = ?',
        [user_id], one=True
    )
    if existing:
        execute_db(
            'UPDATE user_view_preferences SET current_view_id = ? WHERE user_id = ?',
            [view_id, user_id]
        )
    else:
        execute_db(
            'INSERT INTO user_view_preferences (user_id, current_view_id) VALUES (?, ?)',
            [user_id, view_id]
        )

# Custom Fields Management Routes
@app.route('/fields')
@login_required
def list_fields():
    fields = get_custom_fields()
    return render_template('fields.html', fields=fields, field_types=FIELD_TYPES)

@app.route('/fields/add', methods=['GET', 'POST'])
@login_required
def add_field():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        field_type = request.form.get('field_type', 'text')
        options = request.form.get('options', '')
        is_required = 1 if request.form.get('is_required') else 0
        default_value = request.form.get('default_value', '')
        
        if not name:
            flash('Field name is required', 'error')
            return redirect(url_for('add_field'))
        
        field_key = slugify(name)
        
        # Check for duplicate key
        existing = query_db('SELECT id FROM custom_fields WHERE field_key = ?', [field_key], one=True)
        if existing:
            flash('A field with this name already exists', 'error')
            return redirect(url_for('add_field'))
        
        # Get next sequence number
        max_seq = query_db('SELECT MAX(sequence) as max_seq FROM custom_fields', one=True)
        next_seq = (max_seq['max_seq'] or 0) + 1
        
        execute_db('''
            INSERT INTO custom_fields (name, field_key, field_type, options, is_required, default_value, sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [name, field_key, field_type, options, is_required, default_value, next_seq])
        
        flash(f'Field "{name}" created successfully', 'success')
        return redirect(url_for('list_fields'))
    
    return render_template('field_form.html', field=None, field_types=FIELD_TYPES)

@app.route('/fields/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_field(id):
    field = query_db('SELECT * FROM custom_fields WHERE id = ?', [id], one=True)
    if not field:
        flash('Field not found', 'error')
        return redirect(url_for('list_fields'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        options = request.form.get('options', '')
        is_required = 1 if request.form.get('is_required') else 0
        default_value = request.form.get('default_value', '')
        
        if not name:
            flash('Field name is required', 'error')
            return redirect(url_for('edit_field', id=id))
        
        execute_db('''
            UPDATE custom_fields 
            SET name = ?, options = ?, is_required = ?, default_value = ?
            WHERE id = ?
        ''', [name, options, is_required, default_value, id])
        
        flash('Field updated successfully', 'success')
        return redirect(url_for('list_fields'))
    
    return render_template('field_form.html', field=field, field_types=FIELD_TYPES)

@app.route('/fields/<int:id>/delete', methods=['POST'])
@login_required
def delete_field(id):
    execute_db('DELETE FROM field_values WHERE field_id = ?', [id])
    execute_db('DELETE FROM field_visibility WHERE field_id = ?', [id])
    execute_db('DELETE FROM custom_fields WHERE id = ?', [id])
    flash('Field deleted successfully', 'success')
    return redirect(url_for('list_fields'))

# Field Visibility Routes
@app.route('/fields/visibility', methods=['GET', 'POST'])
@login_required
def field_visibility():
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        fields = get_custom_fields()
        for field in fields:
            is_visible = 1 if request.form.get(f'visible_{field["id"]}') else 0
            sequence = int(request.form.get(f'sequence_{field["id"]}', field['sequence']))
            
            # Upsert visibility setting
            existing = query_db(
                'SELECT id FROM field_visibility WHERE user_id = ? AND field_id = ?',
                [user_id, field['id']], one=True
            )
            
            if existing:
                execute_db('''
                    UPDATE field_visibility SET is_visible = ?, sequence = ?
                    WHERE user_id = ? AND field_id = ?
                ''', [is_visible, sequence, user_id, field['id']])
            else:
                execute_db('''
                    INSERT INTO field_visibility (user_id, field_id, is_visible, sequence)
                    VALUES (?, ?, ?, ?)
                ''', [user_id, field['id'], is_visible, sequence])
        
        flash('Field visibility settings saved', 'success')
        return redirect(url_for('leads'))
    
    fields = get_visible_fields(user_id)
    return render_template('field_visibility.html', fields=fields)

@app.route('/api/fields/reorder', methods=['POST'])
@login_required
def reorder_fields():
    user_id = session.get('user_id')
    data = request.get_json()
    
    if not data or 'order' not in data:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    
    for idx, field_id in enumerate(data['order']):
        existing = query_db(
            'SELECT id FROM field_visibility WHERE user_id = ? AND field_id = ?',
            [user_id, field_id], one=True
        )
        
        if existing:
            execute_db(
                'UPDATE field_visibility SET sequence = ? WHERE user_id = ? AND field_id = ?',
                [idx, user_id, field_id]
            )
        else:
            execute_db(
                'INSERT INTO field_visibility (user_id, field_id, is_visible, sequence) VALUES (?, ?, 1, ?)',
                [user_id, field_id, idx]
            )
    
    return jsonify({'success': True})

@app.route('/api/fields/add', methods=['POST'])
@login_required
def api_add_field():
    """AJAX endpoint for adding a new field from the leads page"""
    data = request.get_json()

    name = data.get('name', '').strip()
    field_type = data.get('field_type', 'text')
    options = data.get('options', '')
    is_required = data.get('is_required', 0)
    default_value = data.get('default_value', '')
    insert_after = data.get('insert_after')  # Field ID to insert after, or None for end

    if not name:
        return jsonify({'success': False, 'error': 'Field name is required'})

    # Generate field_key from name
    field_key = slugify(name)

    # Check for duplicate field_key
    existing = query_db('SELECT id FROM custom_fields WHERE field_key = ?', [field_key], one=True)
    if existing:
        return jsonify({'success': False, 'error': 'A field with this name already exists'})

    # Calculate sequence number
    if insert_after:
        # Get the sequence of the field we're inserting after
        after_field = query_db('SELECT sequence FROM custom_fields WHERE id = ?', [insert_after], one=True)
        if after_field:
            new_sequence = after_field['sequence'] + 1
            # Shift all fields after this position
            execute_db('UPDATE custom_fields SET sequence = sequence + 1 WHERE sequence >= ?', [new_sequence])
        else:
            # Fallback to end
            max_seq = query_db('SELECT MAX(sequence) as max_seq FROM custom_fields', one=True)
            new_sequence = (max_seq['max_seq'] or 0) + 1
    else:
        # Add to end
        max_seq = query_db('SELECT MAX(sequence) as max_seq FROM custom_fields', one=True)
        new_sequence = (max_seq['max_seq'] or 0) + 1

    # Insert the new field
    field_id = execute_db('''
        INSERT INTO custom_fields (name, field_key, field_type, options, is_required, default_value, sequence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [name, field_key, field_type, options, is_required, default_value, new_sequence])

    return jsonify({'success': True, 'field_id': field_id})

@app.route('/api/fields/<int:id>/delete', methods=['POST'])
@login_required
def api_delete_field(id):
    """AJAX endpoint for deleting a field"""
    # Delete associated data first
    execute_db('DELETE FROM field_values WHERE field_id = ?', [id])
    execute_db('DELETE FROM field_visibility WHERE field_id = ?', [id])
    execute_db('DELETE FROM view_fields WHERE field_id = ?', [id])
    # Delete the field
    execute_db('DELETE FROM custom_fields WHERE id = ?', [id])

    return jsonify({'success': True})

@app.route('/api/leads/<int:lead_id>/fields/<int:field_id>', methods=['POST'])
@login_required
def api_update_field_value(lead_id, field_id):
    """AJAX endpoint for inline editing of custom field values"""
    data = request.get_json()
    value = data.get('value', '')

    # Get field info to handle special types
    field = query_db('SELECT * FROM custom_fields WHERE id = ?', [field_id], one=True)
    if not field:
        return jsonify({'success': False, 'error': 'Field not found'}), 404

    # Handle multi_select (expects array, store as JSON)
    if field['field_type'] == 'multi_select' and isinstance(value, list):
        import json
        value = json.dumps(value) if value else ''

    # Handle checkbox
    if field['field_type'] == 'checkbox':
        value = '1' if value in [True, 'true', '1', 1] else '0'

    # Upsert the value
    existing = query_db(
        'SELECT id FROM field_values WHERE lead_id = ? AND field_id = ?',
        [lead_id, field_id], one=True
    )

    if existing:
        execute_db(
            'UPDATE field_values SET value = ? WHERE lead_id = ? AND field_id = ?',
            [value, lead_id, field_id]
        )
    else:
        execute_db(
            'INSERT INTO field_values (lead_id, field_id, value) VALUES (?, ?, ?)',
            [lead_id, field_id, value]
        )

    # Return formatted display value
    display_value = value
    if field['field_type'] == 'checkbox':
        display_value = '✓' if value == '1' else '-'
    elif field['field_type'] == 'multi_select' and value:
        display_value = value.replace('[', '').replace(']', '').replace('"', '')

    return jsonify({'success': True, 'display_value': display_value})

@app.route('/api/leads/<int:lead_id>/update', methods=['POST'])
@login_required
def api_update_lead_field(lead_id):
    """AJAX endpoint for inline editing of default lead fields (email, phone, address, job_type, property_type)"""
    lead = query_db('SELECT * FROM leads WHERE id = ?', [lead_id], one=True)
    if not lead:
        return jsonify({'success': False, 'error': 'Lead not found'}), 404

    data = request.get_json()
    field_name = data.get('field')
    value = data.get('value', '')

    # Only allow updating specific fields
    allowed_fields = ['email', 'phone', 'address', 'job_type', 'property_type']
    if field_name not in allowed_fields:
        return jsonify({'success': False, 'error': 'Invalid field'}), 400

    # Update the lead field
    execute_db(f'UPDATE leads SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
               [value, lead_id])

    return jsonify({'success': True, 'display_value': value or '-'})

# Views Management API Routes
@app.route('/api/views/save', methods=['POST'])
@login_required
def api_save_view():
    """Save current field selection as a new view"""
    data = request.get_json()
    name = data.get('name', '').strip()
    default_fields = data.get('default_fields', [])  # List of default field keys
    custom_field_ids = data.get('custom_field_ids', [])  # List of custom field IDs

    if not name:
        return jsonify({'success': False, 'error': 'View name is required'}), 400

    # Check for duplicate name
    existing = query_db('SELECT id FROM views WHERE name = ?', [name], one=True)
    if existing:
        return jsonify({'success': False, 'error': 'A view with this name already exists'}), 400

    # Insert view with default_fields as JSON
    import json
    view_id = execute_db('''
        INSERT INTO views (name, default_fields, created_by)
        VALUES (?, ?, ?)
    ''', [name, json.dumps(default_fields), session.get('user_id')])

    # Insert custom field associations
    for idx, field_id in enumerate(custom_field_ids):
        execute_db('''
            INSERT INTO view_fields (view_id, field_id, sequence)
            VALUES (?, ?, ?)
        ''', [view_id, field_id, idx])

    # Set this view as current for the user
    set_user_current_view(session.get('user_id'), view_id)

    return jsonify({'success': True, 'view_id': view_id})

@app.route('/api/views/<int:id>/update', methods=['POST'])
@login_required
def api_update_view(id):
    """Update an existing view's field selection"""
    view = get_view_by_id(id)
    if not view:
        return jsonify({'success': False, 'error': 'View not found'}), 404

    data = request.get_json()
    default_fields = data.get('default_fields', [])
    custom_field_ids = data.get('custom_field_ids', [])

    import json
    # Update view's default_fields
    execute_db('''
        UPDATE views SET default_fields = ?
        WHERE id = ?
    ''', [json.dumps(default_fields), id])

    # Delete existing custom field associations and re-insert
    execute_db('DELETE FROM view_fields WHERE view_id = ?', [id])

    for idx, field_id in enumerate(custom_field_ids):
        execute_db('''
            INSERT INTO view_fields (view_id, field_id, sequence)
            VALUES (?, ?, ?)
        ''', [id, field_id, idx])

    return jsonify({'success': True})

@app.route('/api/views/<int:id>/delete', methods=['POST'])
@login_required
def api_delete_view(id):
    """Delete a view"""
    execute_db('DELETE FROM views WHERE id = ?', [id])
    execute_db('UPDATE user_view_preferences SET current_view_id = NULL WHERE current_view_id = ?', [id])
    return jsonify({'success': True})

@app.route('/api/views/select', methods=['POST'])
@login_required
def select_view():
    """Select a view (or clear selection for 'All Fields')"""
    user_id = session.get('user_id')
    data = request.get_json()
    view_id = data.get('view_id')

    # Convert empty string to None
    if view_id == '' or view_id is None:
        view_id = None

    set_user_current_view(user_id, view_id)

    # Return view data if a view was selected
    if view_id:
        view = get_view_by_id(view_id)
        if view:
            import json
            default_fields = json.loads(view['default_fields'] or '[]')
            custom_fields = get_fields_for_view(view_id)
            custom_field_ids = [f['id'] for f in custom_fields]
            return jsonify({
                'success': True,
                'view': {
                    'id': view['id'],
                    'name': view['name'],
                    'default_fields': default_fields,
                    'custom_field_ids': custom_field_ids
                }
            })

    return jsonify({'success': True, 'view': None})

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
