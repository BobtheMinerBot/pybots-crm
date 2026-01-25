import os
import json
import sqlite3
import csv
import io
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
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activity_type TEXT DEFAULT 'note',
                metadata TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS custom_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                field_key TEXT UNIQUE NOT NULL,
                field_type TEXT NOT NULL,
                options TEXT,
                option_colors TEXT,
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

            CREATE TABLE IF NOT EXISTS user_field_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                is_visible BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, field_name)
            );

            CREATE TABLE IF NOT EXISTS user_group_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_level INTEGER DEFAULT 1,
                field_name TEXT NOT NULL,
                sort_direction TEXT DEFAULT 'asc',
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6b7280',
                bg_color TEXT DEFAULT '#f3f4f6',
                sequence INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS job_type_colors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6b7280',
                sequence INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS property_type_colors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT '#6b7280',
                sequence INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                customer_id INTEGER,
                stage TEXT,
                current_stage TEXT,
                address TEXT,
                job_type TEXT,
                job_number TEXT,
                auto_number TEXT,
                budget_cost REAL,
                actual_cost REAL,
                approved_orders REAL,
                budget_variance REAL,
                permit_required BOOLEAN DEFAULT 0,
                permit_no TEXT,
                jurisdiction TEXT,
                engineering_plans_required BOOLEAN DEFAULT 0,
                first_site_visit_date TEXT,
                date_completed TEXT,
                scope_of_work TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES leads (id)
            );
        ''')

        # Migration: Add default_fields column to views if it doesn't exist
        try:
            db.execute("SELECT default_fields FROM views LIMIT 1")
        except:
            db.execute("ALTER TABLE views ADD COLUMN default_fields TEXT DEFAULT '[\"email\",\"phone\",\"address\",\"job_type\",\"property_type\"]'")
            print("Added default_fields column to views table")

        # Migration: Add deleted_at column to leads for soft deletes
        try:
            db.execute("SELECT deleted_at FROM leads LIMIT 1")
        except:
            db.execute("ALTER TABLE leads ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL")
            print("Added deleted_at column to leads table for soft deletes")

        # Migration: Add option_colors column to custom_fields
        try:
            db.execute("SELECT option_colors FROM custom_fields LIMIT 1")
        except:
            db.execute("ALTER TABLE custom_fields ADD COLUMN option_colors TEXT")
            print("Added option_colors column to custom_fields table")

        # Migration: Populate default statuses with Monday.com colors
        existing_statuses = db.execute("SELECT id FROM statuses LIMIT 1").fetchone()
        if not existing_statuses:
            default_statuses = [
                ('New Lead', '#0073EA', '#E6F4FF', 1),
                ('Inspection Scheduled', '#FDAB3D', '#FFF4E5', 2),
                ('Estimating', '#A25DDC', '#F4ECFB', 3),
                ('Proposal Sent', '#00C875', '#E5FBF3', 4),
                ('Follow Up', '#FF158A', '#FFE5F0', 5),
                ('Nurturing', '#579BFC', '#E5F0FF', 6),
                ('Lost', '#E2445C', '#FFE5E9', 7)
            ]
            for name, color, bg_color, seq in default_statuses:
                db.execute(
                    'INSERT INTO statuses (name, color, bg_color, sequence) VALUES (?, ?, ?, ?)',
                    (name, color, bg_color, seq)
                )
            print("Populated default statuses with Monday.com colors")

        # Migration: Populate default job types with colors
        existing_job_types = db.execute("SELECT id FROM job_type_colors LIMIT 1").fetchone()
        if not existing_job_types:
            default_job_types = [
                ('Spalling Repair', '#0073EA', 1),
                ('Remodel', '#00C875', 2),
                ('Seawall Repair', '#579BFC', 3),
                ('Pool Deck', '#00D2D2', 4),
                ('Balcony Repair', '#A25DDC', 5),
                ('Other', '#9AADBD', 6)
            ]
            for name, color, seq in default_job_types:
                db.execute(
                    'INSERT INTO job_type_colors (name, color, sequence) VALUES (?, ?, ?)',
                    (name, color, seq)
                )
            print("Populated default job types with colors")

        # Migration: Populate default property types with colors
        existing_property_types = db.execute("SELECT id FROM property_type_colors LIMIT 1").fetchone()
        if not existing_property_types:
            default_property_types = [
                ('Residential', '#00C875', 1),
                ('Commercial', '#0073EA', 2),
                ('Other', '#9AADBD', 3)
            ]
            for name, color, seq in default_property_types:
                db.execute(
                    'INSERT INTO property_type_colors (name, color, sequence) VALUES (?, ?, ?)',
                    (name, color, seq)
                )
            print("Populated default property types with colors")

        # Migration: Enhance activities table with activity_type and metadata
        try:
            db.execute("SELECT activity_type FROM activities LIMIT 1")
        except:
            db.execute("ALTER TABLE activities ADD COLUMN activity_type TEXT DEFAULT 'note'")
            db.execute("ALTER TABLE activities ADD COLUMN metadata TEXT")
            print("Enhanced activities table with activity_type and metadata")

        # Migration: Ensure content column exists in activities table
        try:
            db.execute("SELECT content FROM activities LIMIT 1")
        except:
            # Try to rename 'note' column to 'content' if it exists
            try:
                db.execute("ALTER TABLE activities RENAME COLUMN note TO content")
                print("Renamed activities.note to activities.content")
            except:
                # If rename fails, add content column
                db.execute("ALTER TABLE activities ADD COLUMN content TEXT NOT NULL DEFAULT ''")
                print("Added content column to activities table")

        # Migration: Add field order columns to user_view_preferences
        try:
            db.execute("SELECT default_field_order FROM user_view_preferences LIMIT 1")
        except:
            db.execute("ALTER TABLE user_view_preferences ADD COLUMN default_field_order TEXT")
            db.execute("ALTER TABLE user_view_preferences ADD COLUMN custom_field_order TEXT")
            print("Added field order columns to user_view_preferences table")

        # Create handoff_summaries table for department transitions
        db.execute('''
            CREATE TABLE IF NOT EXISTS handoff_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                from_status TEXT,
                to_status TEXT,
                summary TEXT NOT NULL,
                key_info TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')

        # Create handoff_statuses table to define which status transitions trigger handoffs
        db.execute('''
            CREATE TABLE IF NOT EXISTS handoff_triggers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_status TEXT,
                to_status TEXT NOT NULL,
                department_name TEXT,
                is_active BOOLEAN DEFAULT 1,
                UNIQUE(from_status, to_status)
            )
        ''')

        # Populate default handoff triggers
        existing_triggers = db.execute("SELECT id FROM handoff_triggers LIMIT 1").fetchone()
        if not existing_triggers:
            default_triggers = [
                (None, 'Proposal Sent', 'Sales to Estimating'),
                ('Proposal Sent', 'Won', 'Sales to Project Management'),
                (None, 'Permitting', 'Project to Permitting'),
                (None, 'In Production', 'Permitting to Production'),
            ]
            for from_s, to_s, dept in default_triggers:
                try:
                    db.execute(
                        'INSERT INTO handoff_triggers (from_status, to_status, department_name) VALUES (?, ?, ?)',
                        (from_s, to_s, dept)
                    )
                except:
                    pass
            print("Populated default handoff triggers")

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
    'currency': {'label': 'Currency', 'icon': '💰'},
    'date': {'label': 'Date', 'icon': '📅'},
    'dropdown': {'label': 'Dropdown', 'icon': '📋'},
    'multi_select': {'label': 'Multi-Select', 'icon': '☑️'},
    'checkbox': {'label': 'Checkbox', 'icon': '✓'},
    'email': {'label': 'Email', 'icon': '✉️'},
    'phone': {'label': 'Phone', 'icon': '📞'},
    'url': {'label': 'URL', 'icon': '🔗'},
    'contact': {'label': 'Contact', 'icon': '👤'},
    'duration': {'label': 'Duration', 'icon': '⏱️'},
    'auto_number': {'label': 'Auto-Number', 'icon': '#'},
    'symbol': {'label': 'Symbol', 'icon': '⭐'},
    'file': {'label': 'File Upload', 'icon': '📎'}
}

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent collisions"""
    ext = get_file_extension(original_filename)
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    return f"{unique_name}.{ext}" if ext else unique_name

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
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with pipeline metrics and activity overview"""
    from datetime import datetime, timedelta

    # Get all active leads
    all_leads = query_db('SELECT * FROM leads WHERE deleted_at IS NULL')
    total_leads = len(all_leads)

    # Get leads by status with colors
    status_counts = {}
    db_statuses = get_all_statuses()
    status_colors = get_status_colors()

    # Initialize all statuses with 0 count
    for status in db_statuses:
        status_counts[status['name']] = {
            'count': 0,
            'color': status['color'],
            'bg_color': status['bg_color'],
            'sequence': status['sequence']
        }

    # Count leads per status
    for lead in all_leads:
        status = lead['status']
        if status in status_counts:
            status_counts[status]['count'] += 1
        else:
            # Handle leads with statuses not in db
            status_counts[status] = {
                'count': 1,
                'color': '#6b7280',
                'bg_color': '#f3f4f6',
                'sequence': 999
            }

    # Sort by sequence for pipeline display
    pipeline_stages = sorted(
        [{'name': k, **v} for k, v in status_counts.items()],
        key=lambda x: x['sequence']
    )

    # Calculate percentages for pipeline bar
    for stage in pipeline_stages:
        stage['percentage'] = (stage['count'] / total_leads * 100) if total_leads > 0 else 0

    # Get leads created this week
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    new_this_week = query_db(
        'SELECT COUNT(*) as count FROM leads WHERE deleted_at IS NULL AND created_at >= ?',
        [week_ago], one=True
    )['count']

    # Get stale leads (no activity in 7+ days, excluding Lost/Won statuses)
    stale_leads = query_db('''
        SELECT l.*,
               MAX(a.created_at) as last_activity,
               julianday('now') - julianday(COALESCE(MAX(a.created_at), l.created_at)) as days_stale
        FROM leads l
        LEFT JOIN activities a ON l.id = a.lead_id
        WHERE l.deleted_at IS NULL
          AND l.status NOT IN ('Lost', 'Won', 'Completed')
        GROUP BY l.id
        HAVING days_stale >= 7
        ORDER BY days_stale DESC
        LIMIT 10
    ''')

    # Get leads needing follow-up (status = 'Follow Up')
    follow_up_leads = query_db(
        "SELECT COUNT(*) as count FROM leads WHERE deleted_at IS NULL AND status = 'Follow Up'",
        one=True
    )['count']

    # Get proposals pending (status = 'Proposal Sent')
    proposals_pending = query_db(
        "SELECT COUNT(*) as count FROM leads WHERE deleted_at IS NULL AND status = 'Proposal Sent'",
        one=True
    )['count']

    # Get recent activity across all leads (last 15 actions)
    recent_activities = query_db('''
        SELECT a.*, l.name as lead_name, l.id as lead_id, u.name as user_name
        FROM activities a
        JOIN leads l ON a.lead_id = l.id
        LEFT JOIN users u ON a.user_id = u.id
        WHERE l.deleted_at IS NULL
        ORDER BY a.created_at DESC
        LIMIT 15
    ''')

    # Get job type distribution
    job_type_counts = {}
    job_type_colors = get_job_type_colors()
    for lead in all_leads:
        jt = lead['job_type'] or 'Unspecified'
        if jt not in job_type_counts:
            job_type_counts[jt] = {'count': 0, 'color': job_type_colors.get(jt, '#9AADBD')}
        job_type_counts[jt]['count'] += 1

    # Sort job types by count
    job_type_distribution = sorted(
        [{'name': k, **v} for k, v in job_type_counts.items()],
        key=lambda x: x['count'],
        reverse=True
    )[:6]  # Top 6

    # Calculate max for chart scaling
    max_job_count = max([j['count'] for j in job_type_distribution]) if job_type_distribution else 1
    for jt in job_type_distribution:
        jt['percentage'] = (jt['count'] / max_job_count * 100) if max_job_count > 0 else 0

    return render_template('dashboard.html',
                         total_leads=total_leads,
                         new_this_week=new_this_week,
                         follow_up_count=follow_up_leads,
                         proposals_pending=proposals_pending,
                         pipeline_stages=pipeline_stages,
                         stale_leads=stale_leads,
                         recent_activities=recent_activities,
                         job_type_distribution=job_type_distribution,
                         status_colors=status_colors)

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
    user_id = session.get('user_id')

    # Get user's grouping preferences
    group_prefs = get_user_group_preferences(user_id)

    # If no group preferences, default to grouping by status
    if not group_prefs:
        group_prefs = [{'field_name': 'status', 'sort_direction': 'asc'}]

    # Build query for all leads
    query = 'SELECT * FROM leads WHERE deleted_at IS NULL'
    args = []

    if status_filter:
        query += ' AND status = ?'
        args.append(status_filter)

    if search:
        query += ' AND (name LIKE ? OR email LIKE ? OR address LIKE ? OR phone LIKE ?)'
        search_term = f'%{search}%'
        args.extend([search_term, search_term, search_term, search_term])

    query += ' ORDER BY created_at DESC'
    all_leads = query_db(query, args)

    # Get all custom fields for the field selector
    all_custom_fields = get_custom_fields()

    # Get custom field values for all leads first (needed for grouping)
    all_lead_values = {}
    for lead in all_leads:
        all_lead_values[lead['id']] = get_field_values(lead['id'])

    # Group leads using user preferences
    grouped_leads = group_leads_by_fields(all_leads, group_prefs, all_lead_values)

    # Check if user has a view selected
    current_view = get_user_current_view(user_id)
    all_views = get_all_views()

    # Default field definitions with labels (all movable, including name, created, stage)
    DEFAULT_FIELD_DEFS = [
        {'key': 'name', 'label': 'Name'},
        {'key': 'email', 'label': 'Email/Phone'},
        {'key': 'address', 'label': 'Address'},
        {'key': 'job_type', 'label': 'Job Type'},
        {'key': 'property_type', 'label': 'Property'},
        {'key': 'created', 'label': 'Created'},
        {'key': 'stage', 'label': 'Stage'}
    ]

    # Load global field order from app_settings
    global_field_config = query_db(
        'SELECT value FROM app_settings WHERE key = ?',
        ['global_field_order'], one=True
    )

    if global_field_config:
        # Use global field configuration
        config = json.loads(global_field_config['value'])
        visible_field_keys = config.get('visible_fields', [])
        hidden_field_keys = config.get('hidden_fields', [])
        full_order = config.get('full_order', [])

        # Build default field order based on global config
        default_field_order = []
        for key in full_order:
            if not key.startswith('custom_'):
                field_def = next((f for f in DEFAULT_FIELD_DEFS if f['key'] == key), None)
                if field_def:
                    default_field_order.append({**field_def, 'visible': True})

        # Add any missing default fields as hidden
        for field_def in DEFAULT_FIELD_DEFS:
            if field_def['key'] not in [f['key'] for f in default_field_order]:
                is_visible = field_def['key'] not in hidden_field_keys
                default_field_order.append({**field_def, 'visible': is_visible})

        # Build custom field order
        custom_field_order = []
        for key in full_order:
            if key.startswith('custom_'):
                cf_id = int(key.replace('custom_', ''))
                cf = next((c for c in all_custom_fields if c['id'] == cf_id), None)
                if cf:
                    custom_field_order.append({'id': cf['id'], 'name': cf['name'], 'visible': True})

        # Add any missing custom fields as hidden
        for cf in all_custom_fields:
            if cf['id'] not in [f['id'] for f in custom_field_order]:
                is_visible = f"custom_{cf['id']}" not in hidden_field_keys
                custom_field_order.append({'id': cf['id'], 'name': cf['name'], 'visible': is_visible})

        # Determine visible fields for table display
        visible_default_fields = [f['key'] for f in default_field_order if f['visible']]
        visible_custom_field_ids = [f['id'] for f in custom_field_order if f['visible']]

    elif current_view:
        # Get default fields from view (order matters)
        visible_default_fields = json.loads(current_view['default_fields'] or '[]')
        # Get custom field IDs from view (with sequence)
        view_custom_fields = get_fields_for_view(current_view['id'])
        visible_custom_field_ids = [f['id'] for f in view_custom_fields]

        # Build field order for default fields based on view
        default_field_order = []
        for key in visible_default_fields:
            field_def = next((f for f in DEFAULT_FIELD_DEFS if f['key'] == key), None)
            if field_def:
                default_field_order.append({**field_def, 'visible': True})
        # Add remaining default fields (not in view) at the end
        for field_def in DEFAULT_FIELD_DEFS:
            if field_def['key'] not in visible_default_fields:
                default_field_order.append({**field_def, 'visible': False})

        # Build custom field order based on view
        custom_field_order = []
        for vf in view_custom_fields:
            cf = next((c for c in all_custom_fields if c['id'] == vf['id']), None)
            if cf:
                custom_field_order.append({'id': cf['id'], 'name': cf['name'], 'visible': True})
        # Add remaining custom fields not in view
        for cf in all_custom_fields:
            if cf['id'] not in visible_custom_field_ids:
                custom_field_order.append({'id': cf['id'], 'name': cf['name'], 'visible': False})
    else:
        # Default: all fields visible in default order
        default_field_order = [{**f, 'visible': True} for f in DEFAULT_FIELD_DEFS]
        custom_field_order = [{'id': cf['id'], 'name': cf['name'], 'visible': True} for cf in all_custom_fields]

        # Show all fields by default
        visible_default_fields = [f['key'] for f in DEFAULT_FIELD_DEFS]
        visible_custom_field_ids = [cf['id'] for cf in all_custom_fields]

    # Combine field order for template
    field_order = {
        'default_fields': default_field_order,
        'custom_fields': custom_field_order
    }

    # Get statuses from database with colors
    db_statuses = get_all_statuses()
    status_names = [s['name'] for s in db_statuses] if db_statuses else STATUSES
    status_colors = get_status_colors()

    return render_template('leads.html',
                         grouped_leads=grouped_leads,
                         group_prefs=group_prefs,
                         all_leads=all_leads,
                         statuses=status_names,
                         status_colors=status_colors,
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         status_filter=status_filter,
                         search=search,
                         all_custom_fields=all_custom_fields,
                         visible_custom_field_ids=visible_custom_field_ids,
                         visible_default_fields=visible_default_fields,
                         field_values=all_lead_values,
                         field_order=field_order,
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
            'INSERT INTO activities (lead_id, user_id, content) VALUES (?, ?, ?)',
            (lead_id, session.get('user_id'), 'Lead created')
        )
        
        flash('Lead added successfully', 'success')
        return redirect(url_for('leads'))
    
    custom_fields = get_custom_fields()
    db_statuses = get_all_statuses()
    status_names = [s['name'] for s in db_statuses] if db_statuses else STATUSES
    return render_template('lead_form.html',
                         lead=None,
                         statuses=status_names,
                         status_colors=get_status_colors(),
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         custom_fields=custom_fields,
                         field_values={},
                         google_places_api_key=get_google_places_api_key())

@app.route('/leads/<int:id>')
@login_required
def view_lead(id):
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NULL', [id], one=True)
    if not lead:
        flash('Lead not found', 'error')
        return redirect(url_for('leads'))

    activities = query_db(
        'SELECT * FROM activities WHERE lead_id = ? ORDER BY created_at DESC',
        [id]
    )

    custom_fields = get_custom_fields()
    field_values = get_field_values(id)
    db_statuses = get_all_statuses()
    status_names = [s['name'] for s in db_statuses] if db_statuses else STATUSES

    return render_template('lead_detail.html',
                         lead=lead,
                         activities=activities,
                         statuses=status_names,
                         status_colors=get_status_colors(),
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         custom_fields=custom_fields,
                         field_values=field_values)

@app.route('/leads/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_lead(id):
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NULL', [id], one=True)
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
                'INSERT INTO activities (lead_id, user_id, content) VALUES (?, ?, ?)',
                (id, session.get('user_id'), f'Status changed from "{old_status}" to "{new_status}"')
            )
        
        # Save custom field values
        save_field_values(id, request.form)
        
        flash('Lead updated successfully', 'success')
        return redirect(url_for('view_lead', id=id))
    
    custom_fields = get_custom_fields()
    field_values = get_field_values(id)
    db_statuses = get_all_statuses()
    status_names = [s['name'] for s in db_statuses] if db_statuses else STATUSES

    return render_template('lead_form.html',
                         lead=lead,
                         statuses=status_names,
                         status_colors=get_status_colors(),
                         job_types=JOB_TYPES,
                         property_types=PROPERTY_TYPES,
                         custom_fields=custom_fields,
                         field_values=field_values,
                         google_places_api_key=get_google_places_api_key())

@app.route('/leads/<int:id>/delete', methods=['POST'])
@login_required
def delete_lead(id):
    # Soft delete - just set deleted_at timestamp
    execute_db('UPDATE leads SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?', [id])

    # Log the deletion in activities
    execute_db(
        'INSERT INTO activities (lead_id, user_id, content) VALUES (?, ?, ?)',
        (id, session.get('user_id'), 'Lead moved to trash')
    )

    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('Lead moved to trash', 'success')
    return redirect(url_for('leads'))

# Trash routes for soft-deleted leads
@app.route('/trash')
@login_required
def trash():
    deleted_leads = query_db(
        'SELECT * FROM leads WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC'
    )
    return render_template('trash.html', leads=deleted_leads)

@app.route('/trash/<int:id>/restore', methods=['POST'])
@login_required
def restore_lead(id):
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NOT NULL', [id], one=True)
    if not lead:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Lead not found in trash'}), 404
        flash('Lead not found in trash', 'error')
        return redirect(url_for('trash'))

    # Restore the lead by clearing deleted_at
    execute_db('UPDATE leads SET deleted_at = NULL WHERE id = ?', [id])

    # Log the restoration
    execute_db(
        'INSERT INTO activities (lead_id, user_id, content) VALUES (?, ?, ?)',
        (id, session.get('user_id'), 'Lead restored from trash')
    )

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash(f'"{lead["name"]}" has been restored', 'success')
    return redirect(url_for('trash'))

@app.route('/trash/<int:id>/permanent-delete', methods=['POST'])
@login_required
def permanent_delete_lead(id):
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NOT NULL', [id], one=True)
    if not lead:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Lead not found in trash'}), 404
        flash('Lead not found in trash', 'error')
        return redirect(url_for('trash'))

    # Permanently delete all associated data
    execute_db('DELETE FROM field_values WHERE lead_id = ?', [id])
    execute_db('DELETE FROM activities WHERE lead_id = ?', [id])
    execute_db('DELETE FROM leads WHERE id = ?', [id])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash(f'"{lead["name"]}" has been permanently deleted', 'success')
    return redirect(url_for('trash'))

@app.route('/trash/empty', methods=['POST'])
@login_required
def empty_trash():
    # Get all deleted leads
    deleted_leads = query_db('SELECT id FROM leads WHERE deleted_at IS NOT NULL')

    # Permanently delete all
    for lead in deleted_leads:
        execute_db('DELETE FROM field_values WHERE lead_id = ?', [lead['id']])
        execute_db('DELETE FROM activities WHERE lead_id = ?', [lead['id']])
        execute_db('DELETE FROM leads WHERE id = ?', [lead['id']])

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'count': len(deleted_leads)})

    flash(f'{len(deleted_leads)} lead(s) permanently deleted', 'success')
    return redirect(url_for('trash'))

@app.route('/leads/<int:id>/activity', methods=['POST'])
@login_required
def add_activity(id):
    note = request.form.get('note')
    
    if note:
        execute_db(
            'INSERT INTO activities (lead_id, user_id, content) VALUES (?, ?, ?)',
            (id, session.get('user_id'), note)
        )
        flash('Activity added', 'success')
    
    return redirect(url_for('view_lead', id=id))

@app.route('/leads/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NULL', [id], one=True)
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
            'INSERT INTO activities (lead_id, user_id, content) VALUES (?, ?, ?)',
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
            leads = query_db('SELECT * FROM leads WHERE deleted_at IS NULL ORDER BY created_at DESC')
            return jsonify([lead_to_dict(lead) for lead in leads])
        return jsonify({'error': 'Invalid API key'}), 401

    # Fall back to session authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    leads = query_db('SELECT * FROM leads WHERE deleted_at IS NULL ORDER BY created_at DESC')
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

    # Get backup settings
    last_backup_setting = query_db('SELECT value FROM app_settings WHERE key = ?', ['last_backup'], one=True)
    last_backup = last_backup_setting['value'] if last_backup_setting else None
    backup_email_setting = query_db('SELECT value FROM app_settings WHERE key = ?', ['backup_email'], one=True)
    backup_email = backup_email_setting['value'] if backup_email_setting else ''

    # Get backup count
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    backup_count = 0
    if os.path.exists(backup_dir):
        backup_count = len([f for f in os.listdir(backup_dir) if f.startswith('crm_backup_') and f.endswith('.db')])

    # Get trash count
    trash_count = query_db('SELECT COUNT(*) as count FROM leads WHERE deleted_at IS NOT NULL', one=True)['count']

    return render_template('settings.html',
                          zapier_webhook=ZAPIER_WEBHOOK_URL,
                          user=user,
                          users=users,
                          api_key=api_key,
                          last_backup=last_backup,
                          backup_email=backup_email,
                          backup_count=backup_count,
                          trash_count=trash_count,
                          status_colors=get_status_colors(),
                          google_places_api_key=get_google_places_api_key())

@app.route('/settings/save-google-places-key', methods=['POST'])
@login_required
def save_google_places_key():
    if request.form.get('remove_key'):
        execute_db('DELETE FROM app_settings WHERE key = ?', ['google_places_api_key'])
        flash('Google Places API key removed', 'success')
    else:
        api_key = request.form.get('google_places_api_key', '').strip()
        if api_key:
            existing = query_db('SELECT id FROM app_settings WHERE key = ?', ['google_places_api_key'], one=True)
            if existing:
                execute_db('UPDATE app_settings SET value = ? WHERE key = ?', [api_key, 'google_places_api_key'])
            else:
                execute_db('INSERT INTO app_settings (key, value) VALUES (?, ?)', ['google_places_api_key', api_key])
            flash('Google Places API key saved. Address autocomplete is now enabled.', 'success')
        else:
            flash('Please enter a valid API key', 'error')
    return redirect(url_for('settings') + '#integrations')

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
    rows = query_db('SELECT * FROM custom_fields ORDER BY sequence, id')
    return [dict(row) for row in rows] if rows else []

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

# Status and Color Helper Functions
def get_all_statuses():
    """Get all active statuses with colors, ordered by sequence"""
    statuses = query_db('SELECT * FROM statuses WHERE is_active = 1 ORDER BY sequence')
    return [dict(s) for s in statuses] if statuses else []

def get_status_colors():
    """Get status colors as dict for CSS injection"""
    statuses = get_all_statuses()
    return {s['name']: {'color': s['color'], 'bg': s['bg_color']} for s in statuses}

def get_google_places_api_key():
    """Get Google Places API key from app_settings"""
    setting = query_db('SELECT value FROM app_settings WHERE key = ?', ['google_places_api_key'], one=True)
    return setting['value'] if setting else None

def get_status_names():
    """Get list of status names (for dropdown compatibility)"""
    statuses = get_all_statuses()
    return [s['name'] for s in statuses]

def get_job_types_with_colors():
    """Get all active job types with colors"""
    types = query_db('SELECT * FROM job_type_colors WHERE is_active = 1 ORDER BY sequence')
    return [dict(t) for t in types] if types else []

def get_job_type_colors():
    """Get job type colors as dict"""
    types = get_job_types_with_colors()
    return {t['name']: t['color'] for t in types}

def get_property_types_with_colors():
    """Get all active property types with colors"""
    types = query_db('SELECT * FROM property_type_colors WHERE is_active = 1 ORDER BY sequence')
    return [dict(t) for t in types] if types else []

def get_property_type_colors():
    """Get property type colors as dict"""
    types = get_property_types_with_colors()
    return {t['name']: t['color'] for t in types}

# Activity & Timeline Helper Functions
ACTIVITY_TYPES = {
    'note': {'label': 'Note', 'icon': '📝', 'color': '#6b7280'},
    'status_change': {'label': 'Status Change', 'icon': '🔄', 'color': '#0073EA'},
    'field_update': {'label': 'Field Updated', 'icon': '✏️', 'color': '#A25DDC'},
    'handoff': {'label': 'Handoff', 'icon': '🤝', 'color': '#00C875'},
    'call': {'label': 'Call', 'icon': '📞', 'color': '#FDAB3D'},
    'email': {'label': 'Email', 'icon': '📧', 'color': '#579BFC'},
    'meeting': {'label': 'Meeting', 'icon': '📅', 'color': '#FF158A'},
    'created': {'label': 'Created', 'icon': '✨', 'color': '#00D2D2'},
}

def log_activity(lead_id, activity_type, content, user_id=None, metadata=None):
    """Log an activity for a lead"""
    import json
    meta_json = json.dumps(metadata) if metadata else None
    execute_db('''
        INSERT INTO activities (lead_id, user_id, activity_type, content, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', [lead_id, user_id, activity_type, content, meta_json])

def get_lead_activities(lead_id, limit=50):
    """Get activities for a lead, most recent first"""
    import json
    activities = query_db('''
        SELECT a.*, u.name as user_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.lead_id = ?
        ORDER BY a.created_at DESC
        LIMIT ?
    ''', [lead_id, limit])

    result = []
    for act in activities:
        a = dict(act)
        # Parse metadata JSON
        if a.get('metadata'):
            try:
                a['metadata'] = json.loads(a['metadata'])
            except:
                a['metadata'] = {}
        else:
            a['metadata'] = {}
        # Add activity type info
        a['type_info'] = ACTIVITY_TYPES.get(a.get('activity_type', 'note'), ACTIVITY_TYPES['note'])
        result.append(a)
    return result

def check_handoff_trigger(from_status, to_status):
    """Check if a status transition should trigger a handoff"""
    trigger = query_db('''
        SELECT * FROM handoff_triggers
        WHERE (from_status = ? OR from_status IS NULL) AND to_status = ? AND is_active = 1
    ''', [from_status, to_status], one=True)
    return dict(trigger) if trigger else None

def generate_handoff_summary(lead_id):
    """Generate a handoff summary for a lead"""
    import json

    # Get lead details
    lead = query_db('SELECT * FROM leads WHERE id = ?', [lead_id], one=True)
    if not lead:
        return None
    lead = dict(lead)

    # Get custom field values
    field_values = query_db('''
        SELECT cf.name, cf.field_type, fv.value
        FROM field_values fv
        JOIN custom_fields cf ON fv.field_id = cf.id
        WHERE fv.lead_id = ?
    ''', [lead_id])

    # Get recent activities (last 10)
    activities = query_db('''
        SELECT a.*, u.name as user_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.lead_id = ?
        ORDER BY a.created_at DESC
        LIMIT 10
    ''', [lead_id])

    # Get notes (last 5 note-type activities)
    notes = query_db('''
        SELECT a.content, a.created_at, u.name as user_name
        FROM activities a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.lead_id = ? AND a.activity_type = 'note'
        ORDER BY a.created_at DESC
        LIMIT 5
    ''', [lead_id])

    # Build summary
    summary_parts = []

    # Lead info
    summary_parts.append(f"**Lead:** {lead['name']}")
    if lead.get('email'):
        summary_parts.append(f"**Email:** {lead['email']}")
    if lead.get('phone'):
        summary_parts.append(f"**Phone:** {lead['phone']}")
    if lead.get('address'):
        summary_parts.append(f"**Address:** {lead['address']}")
    if lead.get('job_type'):
        summary_parts.append(f"**Job Type:** {lead['job_type']}")
    if lead.get('property_type'):
        summary_parts.append(f"**Property Type:** {lead['property_type']}")

    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("")

    # Custom fields
    if field_values:
        summary_parts.append("**Custom Fields:**")
        for fv in field_values:
            if fv['value']:
                summary_parts.append(f"- {fv['name']}: {fv['value']}")
        summary_parts.append("")

    # Recent notes
    if notes:
        summary_parts.append("**Recent Notes:**")
        for note in notes:
            date_str = note['created_at'][:10] if note['created_at'] else ''
            user = note['user_name'] or 'System'
            summary_parts.append(f"- [{date_str}] {user}: {note['content'][:200]}")
        summary_parts.append("")

    # Key info extraction (dates, values, etc.)
    key_info = {
        'lead_created': lead.get('created_at'),
        'current_status': lead.get('status'),
        'custom_fields': {fv['name']: fv['value'] for fv in field_values if fv['value']} if field_values else {},
        'notes_count': len(notes) if notes else 0,
        'activities_count': len(activities) if activities else 0
    }

    return {
        'summary': '\n'.join(summary_parts),
        'key_info': json.dumps(key_info),
        'lead': lead
    }

def save_handoff(lead_id, from_status, to_status, summary, key_info, user_id):
    """Save a handoff summary"""
    execute_db('''
        INSERT INTO handoff_summaries (lead_id, from_status, to_status, summary, key_info, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [lead_id, from_status, to_status, summary, key_info, user_id])

    # Also log as an activity
    log_activity(
        lead_id,
        'handoff',
        f"Project handed off from '{from_status}' to '{to_status}'",
        user_id,
        {'from_status': from_status, 'to_status': to_status}
    )

def get_lead_handoffs(lead_id):
    """Get all handoff summaries for a lead"""
    handoffs = query_db('''
        SELECT h.*, u.name as created_by_name
        FROM handoff_summaries h
        LEFT JOIN users u ON h.created_by = u.id
        WHERE h.lead_id = ?
        ORDER BY h.created_at DESC
    ''', [lead_id])
    return [dict(h) for h in handoffs] if handoffs else []

# Grouping Helper Functions
def get_user_group_preferences(user_id):
    """Get user's grouping preferences"""
    prefs = query_db('''
        SELECT group_level, field_name, sort_direction
        FROM user_group_preferences
        WHERE user_id = ?
        ORDER BY group_level
    ''', [user_id])
    return [dict(p) for p in prefs] if prefs else []

def group_leads_by_fields(leads, group_prefs, all_field_values):
    """
    Groups leads recursively by user's group preferences.
    Returns a nested structure for template rendering.
    """
    if not group_prefs or not group_prefs[0].get('field_name'):
        # No grouping - return flat list
        return {'__flat__': list(leads)}

    def get_group_value(lead, field_name):
        """Get the value for a field from a lead"""
        if field_name.startswith('custom_'):
            # Custom field - look up in field_values
            field_id = int(field_name.replace('custom_', ''))
            # Find the custom field
            cf = query_db('SELECT field_key FROM custom_fields WHERE id = ?', [field_id], one=True)
            if cf:
                values = all_field_values.get(lead['id'], {})
                val = values.get(cf['field_key'], {}).get('value', '')
                return val if val else 'Uncategorized'
            return 'Uncategorized'
        else:
            # Default field - sqlite3.Row doesn't have .get()
            try:
                val = lead[field_name]
            except (KeyError, IndexError):
                val = ''
            return val if val else 'Uncategorized'

    def recursive_group(leads_list, level):
        if level >= len(group_prefs):
            return list(leads_list)

        pref = group_prefs[level]
        field_name = pref['field_name']
        sort_dir = pref.get('sort_direction', 'asc')

        # Group by field value
        groups = {}
        for lead in leads_list:
            key = get_group_value(lead, field_name)
            if key not in groups:
                groups[key] = []
            groups[key].append(lead)

        # Sort group keys
        sorted_keys = sorted(groups.keys(), reverse=(sort_dir == 'desc'))

        # Build result with recursive children
        result = []
        for key in sorted_keys:
            result.append({
                'label': key,
                'field': field_name,
                'level': level + 1,
                'count': len(groups[key]),
                'children': recursive_group(groups[key], level + 1)
            })

        return result

    return recursive_group(list(leads), 0)

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
        option_colors = request.form.get('option_colors', '{}')
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
            INSERT INTO custom_fields (name, field_key, field_type, options, option_colors, is_required, default_value, sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [name, field_key, field_type, options, option_colors, is_required, default_value, next_seq])

        flash(f'Field "{name}" created successfully', 'success')
        return redirect(url_for('list_fields'))

    return render_template('field_form.html', field=None, field_types=FIELD_TYPES, status_colors=get_status_colors())

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
        option_colors = request.form.get('option_colors', '{}')
        is_required = 1 if request.form.get('is_required') else 0
        default_value = request.form.get('default_value', '')

        if not name:
            flash('Field name is required', 'error')
            return redirect(url_for('edit_field', id=id))

        execute_db('''
            UPDATE custom_fields
            SET name = ?, options = ?, option_colors = ?, is_required = ?, default_value = ?
            WHERE id = ?
        ''', [name, options, option_colors, is_required, default_value, id])

        flash('Field updated successfully', 'success')
        return redirect(url_for('list_fields'))

    return render_template('field_form.html', field=field, field_types=FIELD_TYPES, status_colors=get_status_colors())

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


@app.route('/api/leads/<int:lead_id>/fields/<int:field_id>/upload', methods=['POST'])
@login_required
def api_upload_file(lead_id, field_id):
    """Handle file upload for file-type custom fields"""
    from werkzeug.utils import secure_filename
    
    # Verify lead exists
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NULL', [lead_id], one=True)
    if not lead:
        return jsonify({'success': False, 'error': 'Lead not found'}), 404
    
    # Verify field exists and is a file type
    field = query_db('SELECT * FROM custom_fields WHERE id = ?', [field_id], one=True)
    if not field:
        return jsonify({'success': False, 'error': 'Field not found'}), 404
    if field['field_type'] != 'file':
        return jsonify({'success': False, 'error': 'Field is not a file type'}), 400
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Seek back to start
    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'error': f'File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
    
    # Generate unique filename and save
    original_filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(original_filename)
    
    # Create lead-specific folder
    lead_folder = os.path.join(UPLOAD_FOLDER, str(lead_id))
    os.makedirs(lead_folder, exist_ok=True)
    
    file_path = os.path.join(lead_folder, unique_filename)
    file.save(file_path)
    
    # Store file info as JSON in field_values
    file_info = json.dumps({
        'filename': unique_filename,
        'original_name': original_filename,
        'size': file_size,
        'uploaded_at': datetime.now().isoformat(),
        'path': f'/static/uploads/{lead_id}/{unique_filename}'
    })
    
    # Delete old file if exists
    existing = query_db(
        'SELECT value FROM field_values WHERE lead_id = ? AND field_id = ?',
        [lead_id, field_id], one=True
    )
    if existing and existing['value']:
        try:
            old_info = json.loads(existing['value'])
            old_path = os.path.join(UPLOAD_FOLDER, str(lead_id), old_info.get('filename', ''))
            if os.path.exists(old_path):
                os.remove(old_path)
        except:
            pass
    
    # Upsert the value
    if existing:
        execute_db(
            'UPDATE field_values SET value = ? WHERE lead_id = ? AND field_id = ?',
            [file_info, lead_id, field_id]
        )
    else:
        execute_db(
            'INSERT INTO field_values (lead_id, field_id, value) VALUES (?, ?, ?)',
            [lead_id, field_id, file_info]
        )
    
    return jsonify({
        'success': True,
        'file_info': json.loads(file_info),
        'display_value': original_filename
    })


@app.route('/api/leads/<int:lead_id>/fields/<int:field_id>/delete-file', methods=['POST'])
@login_required
def api_delete_file(lead_id, field_id):
    """Delete an uploaded file"""
    # Get existing file info
    existing = query_db(
        'SELECT value FROM field_values WHERE lead_id = ? AND field_id = ?',
        [lead_id, field_id], one=True
    )
    
    if existing and existing['value']:
        try:
            file_info = json.loads(existing['value'])
            file_path = os.path.join(UPLOAD_FOLDER, str(lead_id), file_info.get('filename', ''))
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
    
    # Clear the field value
    execute_db(
        'UPDATE field_values SET value = NULL WHERE lead_id = ? AND field_id = ?',
        [lead_id, field_id]
    )
    
    return jsonify({'success': True})


@app.route('/api/leads/<int:lead_id>/update', methods=['POST'])
@login_required
def api_update_lead_field(lead_id):
    """AJAX endpoint for inline editing of default lead fields (email, phone, address, job_type, property_type)"""
    lead = query_db('SELECT * FROM leads WHERE id = ? AND deleted_at IS NULL', [lead_id], one=True)
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

@app.route('/api/fields/order', methods=['POST'])
@login_required
def api_save_field_order():
    """Save field order globally (shared across all users)"""
    import json
    data = request.get_json()

    # New format: full_order contains the complete visible field order
    full_order = data.get('full_order', [])
    visible_fields = data.get('visible_fields', [])
    hidden_fields = data.get('hidden_fields', [])

    # Legacy format support
    default_field_order = data.get('default_fields', [])
    custom_field_order = data.get('custom_fields', [])

    # Save globally to app_settings
    field_config = {
        'full_order': full_order,
        'visible_fields': visible_fields,
        'hidden_fields': hidden_fields,
        'default_fields': default_field_order,
        'custom_fields': custom_field_order
    }

    existing = query_db('SELECT id FROM app_settings WHERE key = ?', ['global_field_order'], one=True)
    if existing:
        execute_db('''
            UPDATE app_settings SET value = ? WHERE key = ?
        ''', [json.dumps(field_config), 'global_field_order'])
    else:
        execute_db('''
            INSERT INTO app_settings (key, value) VALUES (?, ?)
        ''', ['global_field_order', json.dumps(field_config)])

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

@app.route('/api/user/field-preferences', methods=['GET', 'POST'])
@login_required
def api_field_preferences():
    """Get or save user's field display preferences"""
    user_id = session.get('user_id')

    if request.method == 'GET':
        prefs = query_db('''
            SELECT field_name, display_order, is_visible
            FROM user_field_preferences
            WHERE user_id = ?
            ORDER BY display_order
        ''', [user_id])

        return jsonify({
            'success': True,
            'preferences': [dict(p) for p in prefs]
        })

    else:  # POST
        data = request.get_json()
        fields = data.get('fields', [])

        # Clear existing preferences
        execute_db('DELETE FROM user_field_preferences WHERE user_id = ?', [user_id])

        # Insert new preferences
        for field in fields:
            execute_db('''
                INSERT INTO user_field_preferences (user_id, field_name, display_order, is_visible)
                VALUES (?, ?, ?, ?)
            ''', [
                user_id,
                field['field_name'],
                field['display_order'],
                1 if field['is_visible'] else 0
            ])

        return jsonify({'success': True})

@app.route('/api/user/group-preferences', methods=['GET', 'POST'])
@login_required
def api_group_preferences():
    """Get or save user's grouping preferences"""
    user_id = session.get('user_id')

    if request.method == 'GET':
        prefs = query_db('''
            SELECT group_level, field_name, sort_direction
            FROM user_group_preferences
            WHERE user_id = ?
            ORDER BY group_level
        ''', [user_id])

        return jsonify({
            'success': True,
            'preferences': [dict(p) for p in prefs]
        })

    else:  # POST
        data = request.get_json()
        groups = data.get('groups', [])

        # Clear existing preferences
        execute_db('DELETE FROM user_group_preferences WHERE user_id = ?', [user_id])

        # Insert new preferences
        for i, group in enumerate(groups):
            if group.get('field_name'):
                execute_db('''
                    INSERT INTO user_group_preferences
                    (user_id, group_level, field_name, sort_direction)
                    VALUES (?, ?, ?, ?)
                ''', [
                    user_id,
                    i + 1,
                    group['field_name'],
                    group.get('sort_direction', 'asc')
                ])

        return jsonify({'success': True})

# Status Management API Endpoints
@app.route('/api/statuses', methods=['GET'])
@login_required
def api_get_statuses():
    """Get all statuses with colors"""
    statuses = get_all_statuses()
    return jsonify(statuses)

@app.route('/api/statuses', methods=['POST'])
@login_required
def api_add_status():
    """Add a new status"""
    data = request.get_json()
    name = data.get('name', '').strip()
    color = data.get('color', '#6b7280')
    bg_color = data.get('bg_color', '#f3f4f6')

    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    # Get next sequence
    max_seq = query_db('SELECT MAX(sequence) as m FROM statuses', one=True)
    seq = (max_seq['m'] or 0) + 1

    try:
        status_id = execute_db(
            'INSERT INTO statuses (name, color, bg_color, sequence) VALUES (?, ?, ?, ?)',
            [name, color, bg_color, seq]
        )
        return jsonify({'success': True, 'id': status_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/statuses/<int:id>/color', methods=['POST'])
@login_required
def api_update_status_color(id):
    """Update status colors"""
    data = request.get_json()
    color = data.get('color')
    bg_color = data.get('bg_color')

    updates = []
    params = []
    if color:
        updates.append('color = ?')
        params.append(color)
    if bg_color:
        updates.append('bg_color = ?')
        params.append(bg_color)

    if updates:
        params.append(id)
        execute_db(f'UPDATE statuses SET {", ".join(updates)} WHERE id = ?', params)

    return jsonify({'success': True})

@app.route('/api/statuses/<int:id>', methods=['DELETE'])
@login_required
def api_delete_status(id):
    """Delete a status (soft delete by setting is_active=0)"""
    execute_db('UPDATE statuses SET is_active = 0 WHERE id = ?', [id])
    return jsonify({'success': True})

@app.route('/api/statuses/reorder', methods=['POST'])
@login_required
def api_reorder_statuses():
    """Reorder statuses"""
    data = request.get_json()
    order = data.get('order', [])

    for idx, status_id in enumerate(order):
        execute_db('UPDATE statuses SET sequence = ? WHERE id = ?', [idx, status_id])

    return jsonify({'success': True})

# Job Type Color API Endpoints
@app.route('/api/job-types', methods=['GET'])
@login_required
def api_get_job_types():
    """Get all job types with colors"""
    types = get_job_types_with_colors()
    return jsonify(types)

@app.route('/api/job-types/<int:id>/color', methods=['POST'])
@login_required
def api_update_job_type_color(id):
    """Update job type color"""
    data = request.get_json()
    color = data.get('color')
    if color:
        execute_db('UPDATE job_type_colors SET color = ? WHERE id = ?', [color, id])
    return jsonify({'success': True})

# Property Type Color API Endpoints
@app.route('/api/property-types', methods=['GET'])
@login_required
def api_get_property_types():
    """Get all property types with colors"""
    types = get_property_types_with_colors()
    return jsonify(types)

@app.route('/api/property-types/<int:id>/color', methods=['POST'])
@login_required
def api_update_property_type_color(id):
    """Update property type color"""
    data = request.get_json()
    color = data.get('color')
    if color:
        execute_db('UPDATE property_type_colors SET color = ? WHERE id = ?', [color, id])
    return jsonify({'success': True})

# Custom Field Option Colors API
@app.route('/api/fields/<int:id>/option-colors', methods=['POST'])
@login_required
def api_update_field_option_colors(id):
    """Update custom field option colors"""
    data = request.get_json()
    colors = json.dumps(data.get('colors', {}))
    execute_db('UPDATE custom_fields SET option_colors = ? WHERE id = ?', [colors, id])
    return jsonify({'success': True})

# Activity Timeline API
@app.route('/api/leads/<int:lead_id>/activities', methods=['GET'])
@login_required
def api_get_activities(lead_id):
    """Get activities for a lead"""
    activities = get_lead_activities(lead_id)
    return jsonify(activities)

@app.route('/api/leads/<int:lead_id>/activities', methods=['POST'])
@login_required
def api_add_activity(lead_id):
    """Add a new activity/note to a lead"""
    data = request.get_json()
    content = data.get('content', '').strip()
    activity_type = data.get('activity_type', 'note')

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    log_activity(
        lead_id,
        activity_type,
        content,
        session.get('user_id'),
        data.get('metadata')
    )

    return jsonify({'success': True})

@app.route('/api/leads/<int:lead_id>/activities/<int:activity_id>', methods=['DELETE'])
@login_required
def api_delete_activity(lead_id, activity_id):
    """Delete an activity"""
    execute_db('DELETE FROM activities WHERE id = ? AND lead_id = ?', [activity_id, lead_id])
    return jsonify({'success': True})

# Handoff API
@app.route('/api/leads/<int:lead_id>/handoff/check', methods=['POST'])
@login_required
def api_check_handoff(lead_id):
    """Check if a status change should trigger a handoff"""
    data = request.get_json()
    from_status = data.get('from_status')
    to_status = data.get('to_status')

    trigger = check_handoff_trigger(from_status, to_status)
    if trigger:
        return jsonify({
            'trigger': True,
            'department_name': trigger.get('department_name'),
            'from_status': from_status,
            'to_status': to_status
        })
    return jsonify({'trigger': False})

@app.route('/api/leads/<int:lead_id>/handoff/generate', methods=['GET'])
@login_required
def api_generate_handoff(lead_id):
    """Generate a handoff summary for a lead"""
    summary_data = generate_handoff_summary(lead_id)
    if not summary_data:
        return jsonify({'error': 'Lead not found'}), 404
    return jsonify({
        'summary': summary_data['summary'],
        'key_info': summary_data['key_info'],
        'lead_name': summary_data['lead']['name']
    })

@app.route('/api/leads/<int:lead_id>/handoff', methods=['POST'])
@login_required
def api_save_handoff(lead_id):
    """Save a handoff summary"""
    data = request.get_json()
    from_status = data.get('from_status')
    to_status = data.get('to_status')
    summary = data.get('summary', '').strip()
    key_info = data.get('key_info', '{}')

    if not summary:
        return jsonify({'error': 'Summary is required'}), 400

    save_handoff(lead_id, from_status, to_status, summary, key_info, session.get('user_id'))
    return jsonify({'success': True})

@app.route('/api/leads/<int:lead_id>/handoffs', methods=['GET'])
@login_required
def api_get_handoffs(lead_id):
    """Get all handoffs for a lead"""
    handoffs = get_lead_handoffs(lead_id)
    return jsonify(handoffs)

# Template filters
@app.template_filter('strftime')
def strftime_filter(value, fmt='%b %d, %Y'):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    return value.strftime(fmt) if value else ''


@app.template_filter('fromjson')
def fromjson_filter(value):
    """Parse JSON string to dict"""
    if not value:
        return {}
    try:
        return json.loads(value)
    except:
        return {}


# Backup routes
@app.route('/settings/backup', methods=['POST'])
@login_required
def manual_backup():
    """Trigger a manual database backup"""
    import subprocess

    backup_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup.py')

    try:
        # Run backup script
        result = subprocess.run(
            ['python', backup_script],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(backup_script)
        )

        if result.returncode == 0:
            # Store last backup time
            execute_db(
                '''INSERT OR REPLACE INTO app_settings (key, value)
                   VALUES ('last_backup', ?)''',
                [datetime.now().isoformat()]
            )
            flash('Backup created successfully', 'success')
        else:
            flash(f'Backup failed: {result.stderr}', 'error')
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'error')

    return redirect(url_for('settings'))

@app.route('/settings/backup-email', methods=['POST'])
@login_required
def save_backup_email():
    """Save backup email settings"""
    backup_email = request.form.get('backup_email', '').strip()

    # Store in app_settings
    existing = query_db('SELECT id FROM app_settings WHERE key = ?', ['backup_email'], one=True)
    if existing:
        execute_db('UPDATE app_settings SET value = ? WHERE key = ?', [backup_email, 'backup_email'])
    else:
        execute_db('INSERT INTO app_settings (key, value) VALUES (?, ?)', ['backup_email', backup_email])

    if backup_email:
        flash('Backup email saved', 'success')
    else:
        flash('Backup email cleared', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/backup-download')
@login_required
def download_backup():
    """Download the most recent backup"""
    from flask import send_file

    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')

    if not os.path.exists(backup_dir):
        flash('No backups found', 'error')
        return redirect(url_for('settings'))

    # Get most recent backup
    backups = sorted([
        f for f in os.listdir(backup_dir)
        if f.startswith('crm_backup_') and f.endswith('.db')
    ], reverse=True)

    if not backups:
        flash('No backups found', 'error')
        return redirect(url_for('settings'))

    backup_path = os.path.join(backup_dir, backups[0])
    return send_file(
        backup_path,
        as_attachment=True,
        download_name=backups[0]
    )

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

# ==================== CSV IMPORT ====================

# Default column mappings for Customer CSV
CUSTOMER_CSV_MAPPINGS = {
    'Customer Name': 'name',
    'Customer Email': 'email',
    'Customer Phone': 'phone',
    'Customer Address': 'address',
    'Property Type': 'property_type',
    'Customer Stage': 'status',
    'Job Scope': 'notes'
}


@app.route('/leads/import', methods=['GET', 'POST'])
@login_required
def import_leads():
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'error')
            return redirect(request.url)
        
        try:
            # Read CSV content
            stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
            reader = csv.DictReader(stream)
            rows = list(reader)
            
            if not rows:
                flash('CSV file is empty', 'error')
                return redirect(request.url)
            
            # Get column mappings from form
            mappings = {}
            for csv_col in reader.fieldnames:
                mapped_field = request.form.get(f'mapping_{csv_col}')
                if mapped_field and mapped_field != 'skip':
                    mappings[csv_col] = mapped_field
            
            # If no mappings provided, use defaults
            if not mappings:
                mappings = {k: v for k, v in CUSTOMER_CSV_MAPPINGS.items() if k in reader.fieldnames}
            
            # Import settings
            duplicate_action = request.form.get('duplicate_action', 'skip')
            
            imported = 0
            skipped = 0
            updated = 0
            
            for row in rows:
                # Build lead data from mappings
                lead_data = {}
                for csv_col, db_field in mappings.items():
                    if csv_col in row:
                        lead_data[db_field] = row[csv_col].strip() if row[csv_col] else ''
                
                # Require at least a name
                if not lead_data.get('name'):
                    skipped += 1
                    continue
                
                # Check for duplicates by email or name
                existing = None
                if lead_data.get('email'):
                    existing = query_db(
                        'SELECT id FROM leads WHERE email = ? AND deleted_at IS NULL',
                        [lead_data['email']], one=True
                    )
                if not existing and lead_data.get('name'):
                    existing = query_db(
                        'SELECT id FROM leads WHERE name = ? AND deleted_at IS NULL',
                        [lead_data['name']], one=True
                    )
                
                if existing:
                    if duplicate_action == 'skip':
                        skipped += 1
                        continue
                    elif duplicate_action == 'update':
                        # Update existing record
                        update_fields = []
                        update_values = []
                        for field, value in lead_data.items():
                            if value:  # Only update non-empty values
                                update_fields.append(f'{field} = ?')
                                update_values.append(value)
                        if update_fields:
                            update_values.append(existing['id'])
                            execute_db(
                                f'UPDATE leads SET {", ".join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                                update_values
                            )
                            updated += 1
                        continue
                
                # Insert new lead
                execute_db(
                    '''INSERT INTO leads (name, email, phone, address, job_type, property_type, status, notes, created_by)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        lead_data.get('name', ''),
                        lead_data.get('email', ''),
                        lead_data.get('phone', ''),
                        lead_data.get('address', ''),
                        lead_data.get('job_type', ''),
                        lead_data.get('property_type', ''),
                        lead_data.get('status', 'New Lead'),
                        lead_data.get('notes', ''),
                        session.get('user_id')
                    )
                )
                imported += 1
            
            flash(f'Import complete: {imported} added, {updated} updated, {skipped} skipped', 'success')
            return redirect(url_for('leads'))
            
        except Exception as e:
            flash(f'Error processing CSV: {str(e)}', 'error')
            return redirect(request.url)
    
    # GET request - show import form
    return render_template('import_leads.html',
                         default_mappings=CUSTOMER_CSV_MAPPINGS,
                         lead_fields=['name', 'email', 'phone', 'address', 'job_type', 'property_type', 'status', 'notes'])

@app.route('/leads/import/preview', methods=['POST'])
@login_required
def preview_import():
    """AJAX endpoint to preview CSV data before import"""
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        return jsonify({'error': 'Invalid file'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        rows = list(reader)
        
        # Return headers and first 5 rows for preview
        preview_rows = rows[:5]
        
        # Auto-detect mappings
        auto_mappings = {}
        for csv_col in reader.fieldnames:
            if csv_col in CUSTOMER_CSV_MAPPINGS:
                auto_mappings[csv_col] = CUSTOMER_CSV_MAPPINGS[csv_col]
        
        return jsonify({
            'headers': reader.fieldnames,
            'preview': preview_rows,
            'total_rows': len(rows),
            'auto_mappings': auto_mappings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# DEPLOY WEBHOOK - Auto-deploy from GitHub
# =============================================================================
DEPLOY_SECRET = os.environ.get('DEPLOY_SECRET', '')

@app.route('/deploy', methods=['POST'])
def deploy_webhook():
    """Webhook endpoint for auto-deployment from GitHub Actions"""
    # Check secret token
    token = request.headers.get('X-Deploy-Token') or request.args.get('token')
    if not DEPLOY_SECRET or token != DEPLOY_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import subprocess
        # Get the directory where app.py lives
        app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run git pull
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Touch WSGI file to trigger PythonAnywhere reload
        wsgi_file = '/var/www/pybots_pythonanywhere_com_wsgi.py'
        reload_msg = ''
        if os.path.exists(wsgi_file):
            import pathlib
            pathlib.Path(wsgi_file).touch()
            reload_msg = 'App reload triggered'
        
        return jsonify({
            'success': True,
            'output': result.stdout,
            'errors': result.stderr,
            'return_code': result.returncode,
            'reload': reload_msg
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Git pull timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Bulk sync endpoint for custom fields and statuses (API key protected)
@app.route('/api/sync/custom-fields', methods=['POST'])
def api_sync_custom_fields():
    # Check for API key authentication
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    settings = query_db('SELECT value FROM app_settings WHERE key = ?', ['api_key'], one=True)
    if not settings or settings['value'] != api_key:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json() or {}
    fields = data.get('fields', [])
    
    created = 0
    updated = 0
    
    for field in fields:
        existing = query_db('SELECT id FROM custom_fields WHERE field_key = ?', [field['field_key']], one=True)
        if existing:
            execute_db('''
                UPDATE custom_fields SET name=?, field_type=?, options=?, option_colors=?, 
                is_required=?, default_value=?, sequence=? WHERE field_key=?
            ''', [field['name'], field['field_type'], field.get('options', ''), 
                  field.get('option_colors', ''), field.get('is_required', 0),
                  field.get('default_value', ''), field.get('sequence', 0), field['field_key']])
            updated += 1
        else:
            execute_db('''
                INSERT INTO custom_fields (name, field_key, field_type, options, option_colors, is_required, default_value, sequence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [field['name'], field['field_key'], field['field_type'], field.get('options', ''),
                  field.get('option_colors', ''), field.get('is_required', 0),
                  field.get('default_value', ''), field.get('sequence', 0)])
            created += 1
    
    return jsonify({'success': True, 'created': created, 'updated': updated})

@app.route('/api/sync/statuses', methods=['POST'])
def api_sync_statuses():
    # Check for API key authentication
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    settings = query_db('SELECT value FROM app_settings WHERE key = ?', ['api_key'], one=True)
    if not settings or settings['value'] != api_key:
        return jsonify({'error': 'Invalid API key'}), 401

    data = request.get_json() or {}
    statuses = data.get('statuses', [])
    
    created = 0
    updated = 0
    
    for status in statuses:
        existing = query_db('SELECT id FROM statuses WHERE name = ?', [status['name']], one=True)
        if existing:
            execute_db('''
                UPDATE statuses SET color=?, bg_color=?, sequence=?, is_active=? WHERE name=?
            ''', [status.get('color', '#6b7280'), status.get('bg_color', '#f3f4f6'),
                  status.get('sequence', 0), status.get('is_active', 1), status['name']])
            updated += 1
        else:
            execute_db('''
                INSERT INTO statuses (name, color, bg_color, sequence, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', [status['name'], status.get('color', '#6b7280'), status.get('bg_color', '#f3f4f6'),
                  status.get('sequence', 0), status.get('is_active', 1)])
            created += 1
    
    return jsonify({'success': True, 'created': created, 'updated': updated})

# Auto-run database migrations on startup (works on both local and WSGI)
# This ensures tables are always in sync with the code
init_db()

if __name__ == '__main__':
    app.run(debug=True)
