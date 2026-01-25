#!/usr/bin/env python3
"""
CRM Database Backup Script

Usage:
    python backup.py                    # Create local backup only
    python backup.py --email            # Create backup and email it

Environment variables for email:
    BACKUP_EMAIL_TO       - Email address to send backup to
    BACKUP_EMAIL_FROM     - Sender email address
    SMTP_HOST             - SMTP server (default: smtp.gmail.com)
    SMTP_PORT             - SMTP port (default: 587)
    SMTP_USER             - SMTP username
    SMTP_PASSWORD         - SMTP password (for Gmail, use App Password)

To set up automatic daily backups, add this cron job:
    0 2 * * * cd /path/to/crm && python backup.py --email >> backup.log 2>&1
"""

import os
import sys
import shutil
import smtplib
import sqlite3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(SCRIPT_DIR, 'crm.db')
BACKUP_DIR = os.path.join(SCRIPT_DIR, 'backups')
MAX_BACKUPS = 30  # Keep last 30 backups

def create_backup():
    """Create a timestamped backup of the database"""
    # Ensure backup directory exists
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'crm_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    # Check if database exists
    if not os.path.exists(DATABASE):
        print(f"Error: Database not found at {DATABASE}")
        return None

    # Create backup using SQLite's backup API for consistency
    try:
        source = sqlite3.connect(DATABASE)
        dest = sqlite3.connect(backup_path)
        source.backup(dest)
        source.close()
        dest.close()

        # Get file size
        size = os.path.getsize(backup_path)
        size_str = format_size(size)

        print(f"Backup created: {backup_filename} ({size_str})")

        # Clean up old backups
        cleanup_old_backups()

        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def cleanup_old_backups():
    """Remove old backups, keeping only MAX_BACKUPS most recent"""
    try:
        backups = sorted([
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith('crm_backup_') and f.endswith('.db')
        ])

        while len(backups) > MAX_BACKUPS:
            old_backup = backups.pop(0)
            old_path = os.path.join(BACKUP_DIR, old_backup)
            os.remove(old_path)
            print(f"Removed old backup: {old_backup}")
    except Exception as e:
        print(f"Error cleaning up old backups: {e}")

def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def get_lead_count():
    """Get count of active leads for email summary"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def send_email_backup(backup_path):
    """Send the backup file via email"""
    # Get email configuration from environment
    email_to = os.environ.get('BACKUP_EMAIL_TO')
    email_from = os.environ.get('BACKUP_EMAIL_FROM')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')

    # Check required settings
    if not all([email_to, email_from, smtp_user, smtp_password]):
        print("Error: Email configuration incomplete")
        print("Required environment variables:")
        print("  BACKUP_EMAIL_TO, BACKUP_EMAIL_FROM, SMTP_USER, SMTP_PASSWORD")
        return False

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = f"CRM Backup - {datetime.now().strftime('%B %d, %Y')}"

        # Get stats for email body
        lead_count = get_lead_count()
        backup_size = format_size(os.path.getsize(backup_path))

        body = f"""CRM Database Backup

Backup Date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
Active Leads: {lead_count}
Backup Size: {backup_size}

The database backup is attached to this email.

To restore from this backup:
1. Stop the CRM application
2. Replace crm.db with the attached backup file
3. Restart the application

This is an automated backup email.
"""
        msg.attach(MIMEText(body, 'plain'))

        # Attach backup file
        with open(backup_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{os.path.basename(backup_path)}"'
            )
            msg.attach(part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f"Backup email sent to {email_to}")
        return True

    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    print(f"CRM Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 40)

    # Create backup
    backup_path = create_backup()
    if not backup_path:
        sys.exit(1)

    # Send email if requested
    if '--email' in sys.argv:
        if not send_email_backup(backup_path):
            print("Warning: Backup created but email failed")
            sys.exit(1)

    print("-" * 40)
    print("Backup complete!")

if __name__ == '__main__':
    main()
