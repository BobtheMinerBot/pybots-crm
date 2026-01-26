#!/bin/bash
# Lead Notifier - Checks for new CRM leads and sends iMessage notification
# Run via cron every 2 minutes

CRM_API="https://pybots-crm-production.up.railway.app/api/leads"
API_KEY="${CRM_API_KEY:-}"
NOTIFY_PHONE="+13053048540"
STATE_FILE="/tmp/last_lead_check.txt"

# Get timestamp from 2 minutes ago
TWO_MIN_AGO=$(date -v-2M '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -d '2 minutes ago' '+%Y-%m-%d %H:%M:%S')

# Get latest leads
LEADS=$(curl -s "$CRM_API?limit=5" -H "X-API-Key: $API_KEY")

# Check each lead's created_at timestamp
echo "$LEADS" | jq -c '.[]' | while read -r lead; do
    LEAD_ID=$(echo "$lead" | jq -r '.id')
    CREATED=$(echo "$lead" | jq -r '.created_at')
    NAME=$(echo "$lead" | jq -r '.name')
    PHONE=$(echo "$lead" | jq -r '.phone // "No phone"')
    JOB_TYPE=$(echo "$lead" | jq -r '.job_type // "General"')
    ADDRESS=$(echo "$lead" | jq -r '.address // "No address"')
    
    # Check if we already notified for this lead
    if [ -f "$STATE_FILE" ]; then
        LAST_ID=$(cat "$STATE_FILE")
        if [ "$LEAD_ID" -le "$LAST_ID" ]; then
            continue
        fi
    fi
    
    # Check if lead is recent (created in last 2 minutes)
    LEAD_TS=$(date -j -f '%Y-%m-%d %H:%M:%S' "$CREATED" '+%s' 2>/dev/null || date -d "$CREATED" '+%s')
    NOW_TS=$(date '+%s')
    AGE=$((NOW_TS - LEAD_TS))
    
    # If lead is less than 2 minutes old, notify
    if [ "$AGE" -lt 120 ]; then
        MSG="🔔 New Lead!

📋 $NAME
📞 $PHONE
🔧 $JOB_TYPE
📍 $ADDRESS"
        
        # Send iMessage
        imsg send --to "$NOTIFY_PHONE" --text "$MSG"
        
        # Update state file
        echo "$LEAD_ID" > "$STATE_FILE"
        
        echo "Notified: $NAME (Lead #$LEAD_ID)"
    fi
done
