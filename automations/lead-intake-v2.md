# Lead Intake Automation v2

## Overview
Automated lead capture from multiple sources with CRM + JobTread integration.

## Sources
1. **Squarespace Forms** — Auto-monitored every 15 min via `lead-monitor` cron
2. **Text from Jaasiel** — Conversational intake when he texts lead details

## Workflow

### 1. Lead Detection
When a new lead is detected (form submission or text):
- Parse: Name, Phone, Email, Address, Service Type, Notes
- Check for duplicates in CRM (by phone or email)

### 2. Duplicate Check
If potential duplicate found:
```
⚠️ Possible duplicate:
New: John Smith, (305) 555-1234
Existing: John Smith, (305) 555-1234 (added Jan 20, status: Contacted)

Add as new lead anyway?
```
Wait for Jaasiel's decision.

### 3. CRM Creation
Auto-create lead in CRM:
- **Name:** From form/text
- **Phone:** From form/text
- **Email:** From form/text (if provided)
- **Address:** From form/text (if provided)
- **Job Type:** From form/text or ask
- **Sales Stage:** "New Lead"
- **Status:** "New Lead"
- **Source:** "Website" or "Phone" or "Referral"

### 4. Notification
Send to Jaasiel:
```
📥 New Lead Added to CRM

Name: [Name]
Phone: [Phone]
Email: [Email]
Service: [Service Type]
Source: [Website/Phone/Referral]

Create Customer + Job in JobTread?
```

### 5. JobTread Creation (if confirmed)
If Jaasiel says yes:

**Ask job type if not already known:**
```
What type of job?
1. Spalling (default)
2. Impact Windows/Doors
3. Deck
4. Balcony
5. Remodel
6. Other
```

**Create Customer:**
- Name: Lead name
- Phone: Lead phone
- Email: Lead email
- Address: Lead address

**Create Job:**
- Title: "[Customer Name] - [Job Type]"
- Customer: Link to created customer
- Job Type: Selected type
- Status: "New Lead" or first sales stage

**Confirm:**
```
✅ Created in JobTread:
- Customer: [Name] 
- Job: [Job Title]
- Link: [JobTread URL]
```

### 6. Update CRM
After JobTread creation:
- Link JobTread Job ID to CRM lead
- Update notes with JobTread reference

## Text Intake Patterns

Luna recognizes these patterns when Jaasiel texts:

**Full details:**
```
New lead - John Smith, 305-555-1234, spalling repair at 123 Main St
```

**Partial details:**
```
Got a call from Jane Doe 786-555-4321 about windows
```

**Referral:**
```
Referral from Mike - Sarah Johnson 305-555-9876, deck project
```

Luna will:
1. Parse what's provided
2. Ask for missing critical info (at minimum: name + phone)
3. Proceed with workflow

## API Endpoints Used

### CRM (pybots.pythonanywhere.com)
- `POST /api/leads` — Create new lead
- `GET /api/leads?search=` — Check duplicates

### JobTread
- `POST /graphql` with createCustomer mutation
- `POST /graphql` with createJob mutation

## Cron Job: lead-monitor
- **Schedule:** Every 15 minutes
- **Action:** Check jaasiel@islabuilders.com for new form submissions
- **On new lead:** Execute this workflow

---
*Luna handles intake so Jaasiel can focus on the craft.* 🐕‍🦺
