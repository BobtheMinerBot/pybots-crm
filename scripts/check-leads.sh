#!/bin/bash
# ISLA CRM Lead Monitor
# Checks for new form submissions and outputs lead data

export GOG_KEYRING_PASSWORD="${GOG_KEYRING_PASSWORD}"
ACCOUNT="jaasiel@islabuilders.com"
LEADS_FILE="/Users/jb/clawd/projects/isla-crm/data/leads.json"
SEEN_FILE="/Users/jb/clawd/projects/isla-crm/data/seen-emails.txt"

# Create seen file if it doesn't exist
touch "$SEEN_FILE"

# Search for form submissions from last 24 hours
emails=$(gog gmail search 'from:form-submission@squarespace.info newer_than:1d' --max 10 --account "$ACCOUNT" --json 2>/dev/null)

if [ -z "$emails" ]; then
    echo "No emails found or error occurred"
    exit 0
fi

# Extract thread IDs
echo "$emails" | jq -r '.threads[]?.id // empty' | while read -r msg_id; do
    # Skip if already seen
    if grep -q "^${msg_id}$" "$SEEN_FILE" 2>/dev/null; then
        continue
    fi
    
    # Get full message
    content=$(gog gmail get "$msg_id" --account "$ACCOUNT" 2>/dev/null)
    
    # Extract lead details using grep/sed
    name=$(echo "$content" | grep -A1 '<b>Name:</b>' | grep '<span>' | sed 's/.*<span>\(.*\)<\/span>.*/\1/' | head -1)
    email=$(echo "$content" | grep -A1 '<b>Email:</b>' | grep '<span>' | sed 's/.*<span>\(.*\)<\/span>.*/\1/' | head -1)
    phone=$(echo "$content" | grep -A1 '<b>Phone:</b>' | grep '<span>' | sed 's/.*<span>\(.*\)<\/span>.*/\1/' | head -1)
    details=$(echo "$content" | grep -A1 '<b>Project Details:</b>' | grep '<span>' | sed 's/.*<span>\(.*\)<\/span>.*/\1/' | head -1)
    subject=$(echo "$content" | grep '^subject' | cut -f2-)
    date=$(echo "$content" | grep '^date' | cut -f2-)
    
    # Only output if we found a name (valid lead)
    if [ -n "$name" ]; then
        echo "NEW_LEAD"
        echo "ID: $msg_id"
        echo "NAME: $name"
        echo "EMAIL: $email"
        echo "PHONE: $phone"
        echo "DETAILS: $details"
        echo "FORM: $subject"
        echo "DATE: $date"
        echo "---"
        
        # Mark as seen
        echo "$msg_id" >> "$SEEN_FILE"
    fi
done
