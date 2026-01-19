#!/bin/bash
# Setup daily backup cron job for CRM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.py"
PYTHON_PATH=$(which python3)

# Check if backup.py exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "Error: backup.py not found at $BACKUP_SCRIPT"
    exit 1
fi

# Create the cron entry (runs at 2 AM daily)
CRON_ENTRY="0 2 * * * cd $SCRIPT_DIR && $PYTHON_PATH backup.py --email >> $SCRIPT_DIR/backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup.py"; then
    echo "Backup cron job already exists:"
    crontab -l | grep "backup.py"
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    # Remove existing backup cron entry
    crontab -l | grep -v "backup.py" | crontab -
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✓ Daily backup cron job installed!"
echo ""
echo "Schedule: Every day at 2:00 AM"
echo "Command: $CRON_ENTRY"
echo ""
echo "To view your cron jobs: crontab -l"
echo "To remove this job: crontab -e (and delete the backup.py line)"
echo ""
echo "Note: Set these environment variables for email delivery:"
echo "  export BACKUP_EMAIL_TO='your-email@example.com'"
echo "  export BACKUP_EMAIL_FROM='sender@example.com'"
echo "  export SMTP_USER='smtp-username'"
echo "  export SMTP_PASSWORD='smtp-password'"
