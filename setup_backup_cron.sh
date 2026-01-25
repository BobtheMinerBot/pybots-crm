#!/bin/bash
# Setup daily backup cron job for CRM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.py"
PYTHON_PATH=$(which python3)
ENV_FILE="$SCRIPT_DIR/.env"

# Check if backup.py exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "Error: backup.py not found at $BACKUP_SCRIPT"
    exit 1
fi

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo ""
    echo "Create a .env file with your email credentials:"
    echo "  BACKUP_EMAIL_TO='your@email.com'"
    echo "  BACKUP_EMAIL_FROM='your@email.com'"
    echo "  SMTP_USER='your@email.com'"
    echo "  SMTP_PASSWORD='your-app-password'"
    exit 1
fi

# Create the cron entry (runs at 2 AM daily)
CRON_ENTRY="0 2 * * * cd $SCRIPT_DIR && set -a && . ./.env && set +a && $PYTHON_PATH backup.py --email >> $SCRIPT_DIR/backup.log 2>&1"

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

echo "Daily backup cron job installed!"
echo ""
echo "Schedule: Every day at 2:00 AM"
echo "Credentials: Loaded from .env file"
echo ""
echo "To view your cron jobs: crontab -l"
echo "To remove this job: crontab -e (and delete the backup.py line)"
