# ISLA CRM — Automation Workflows

## How to Use This System

**Adding a Lead:**
Just text Luna with the details. Examples:
- "New lead: John Smith, 305-555-1234, spalling repair at 123 Ocean Dr, Marathon"
- "Got a call from Maria Garcia about impact windows, her number is 305-555-5678"
- "Website lead came in for deck work"

Luna will:
1. Create the lead record
2. Confirm the details
3. Ask about scheduling a site visit
4. Set up follow-up reminders

---

## Automated Triggers

### New Lead Created
**Trigger:** Lead added to system
**Actions:**
1. Send confirmation to Jaasiel with lead summary
2. Prompt: "Want me to find times for a site visit?"
3. Set 24-hour follow-up reminder if no action taken

### Site Visit Scheduled
**Trigger:** Site visit date/time set
**Actions:**
1. Block time on Google Calendar (site visit duration + travel buffer)
2. Send day-before reminder
3. After visit: prompt for measurements/notes

### Site Visit Completed
**Trigger:** Status changed to "Measured"
**Actions:**
1. Prompt: "Block time for estimate prep?"
2. Start 2-day estimate timer
3. Alert if estimate not sent within SLA

### Estimate Sent
**Trigger:** Status changed to "Estimate Sent"
**Actions:**
1. Record estimate date
2. Schedule follow-up sequence:
   - Day 2: "Check in on [Client Name] proposal?"
   - Day 5: "Follow up on [Client Name]?"
   - Day 10: "Final follow-up on [Client Name] — still interested?"

### Lead Won
**Trigger:** Status changed to "Won"
**Actions:**
1. Update metrics
2. Create project in JobTread (if not already)
3. Archive from active pipeline

### Lead Lost
**Trigger:** Status changed to "Lost"
**Actions:**
1. Prompt for reason (optional)
2. Update metrics
3. Archive from active pipeline

---

## Daily Automations

### 6 PM — Tomorrow Planning (Active ✅)
- Prompt for office tasks needing calendar time
- Block time based on response

### Morning Briefing (Planned)
- Today's appointments
- Overdue follow-ups
- Estimates due
- New leads needing attention

---

## Weekly Automations

### Sunday Evening — Week Ahead
- Preview of scheduled site visits
- Pending estimates
- Follow-ups due
- Pipeline summary

### Friday — Weekly Metrics
- Leads received this week
- Conversion stats
- Revenue pipeline
- What worked, what didn't

---

## Commands Luna Understands

**Lead Management:**
- "New lead: [details]" — Create lead
- "Update [name] to [status]" — Change status
- "Schedule site visit with [name] for [date/time]"
- "Show me my pipeline" — Current active leads
- "What's overdue?" — Show missed follow-ups

**Calendar:**
- "Block [X hours] tomorrow for [task]"
- "What's on my calendar tomorrow?"
- "Move [appointment] to [new time]"

**Reporting:**
- "Weekly summary" — Stats and pipeline
- "How many leads this month?"
- "What's my close rate?"

---

## Data Locations

- Leads: `/projects/isla-crm/data/leads.json`
- Config: `/projects/isla-crm/data/config.json`
- Metrics: `/projects/isla-crm/data/metrics.json`
- Architecture: `/projects/isla-crm/ARCHITECTURE.md`

---

*System initialized: January 24, 2026*
