# ISLA CRM — Follow-Up Reminder System

## How It Works

When a lead status changes to "Estimate Sent":
1. Record the estimate sent date
2. Queue follow-up reminders for Day 2, 5, and 10
3. Daily check (10 AM) alerts Jaasiel to due follow-ups
4. Mark complete when action taken or lead status changes

---

## Follow-Up Sequence

### Day 2 — Soft Check-In
**Trigger:** 2 days after estimate sent
**Action:** Luna prompts: "Time to check in on [Client Name]'s proposal. Want me to draft a message?"
**Goal:** Confirm receipt, answer questions

### Day 5 — Value Add
**Trigger:** 5 days after estimate sent (if not yet responded)
**Action:** Luna prompts: "Follow up on [Client Name]? They've had the estimate for 5 days."
**Goal:** Address concerns, offer to adjust scope

### Day 10 — Final Touch
**Trigger:** 10 days after estimate sent (if still pending)
**Action:** Luna prompts: "Final follow-up on [Client Name]? Time to close the loop."
**Goal:** Get a yes/no, clear the pipeline

---

## Follow-Up Record Structure

```json
{
  "id": "followup-001",
  "leadId": "lead-001",
  "clientName": "John Smith",
  "service": "spalling",
  "estimateSentDate": "2026-01-25",
  "followUps": [
    {"day": 2, "dueDate": "2026-01-27", "status": "pending"},
    {"day": 5, "dueDate": "2026-01-30", "status": "pending"},
    {"day": 10, "dueDate": "2026-02-04", "status": "pending"}
  ],
  "status": "active",
  "notes": ""
}
```

---

## Status Changes

**Lead Won:**
- Cancel remaining follow-ups
- Move to completed
- Log: "Won on Day X after Y follow-ups"

**Lead Lost:**
- Cancel remaining follow-ups
- Move to completed
- Log reason if provided

**Client Responded:**
- Mark current follow-up complete
- Continue sequence or pause based on response

---

## Daily Check (10 AM Weekdays)

The follow-up checker cron job:
1. Reads followups.json
2. Finds any with dueDate = today and status = pending
3. Alerts Jaasiel with client names and context
4. Suggests action for each

**Alert format:**
"Follow-ups due today:
• **John Smith** (spalling) — Day 2 check-in
• **Maria Garcia** (windows) — Day 5 follow-up

Want me to draft messages for these?"

---

## Commands

**Mark estimate sent:**
"Sent estimate to [Client Name]"
→ Luna queues follow-up sequence

**Check pending:**
"What follow-ups are due?"
→ Luna shows today's + overdue

**Complete follow-up:**
"Followed up with [Client Name]"
→ Luna marks complete, notes action

**Skip follow-up:**
"Skip [Client Name] follow-up"
→ Luna skips current, continues sequence

**Mark won/lost:**
"[Client Name] said yes" or "[Client Name] passed"
→ Luna updates status, cancels remaining follow-ups

---

## Message Templates

Luna can draft follow-up messages using templates in:
`/projects/isla-crm/templates/follow-up-messages.md`

Customize based on:
- Service type
- Client relationship
- Previous interactions

---

*System initialized: January 24, 2026*
