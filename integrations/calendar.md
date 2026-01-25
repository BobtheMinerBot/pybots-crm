# ISLA CRM — Calendar Integration

## Connection Details
- **Account:** bacallaojaasiel@gmail.com
- **Services:** Calendar, Gmail
- **Connected:** 2026-01-24
- **Timezone:** America/New_York

---

## Event Types & Colors

| Type | Color ID | Hex | Use Case |
|------|----------|-----|----------|
| Site Visit | 9 | #5484ed (blue) | Client property visits |
| Estimate Prep | 10 | #51b749 (green) | Office time for estimates |
| Follow-up Call | 6 | #ffb878 (orange) | Client follow-ups |
| Admin/Office | 8 | #e1e1e1 (gray) | General office work |
| Client Meeting | 7 | #46d6db (teal) | In-person meetings |

---

## Automated Calendar Actions

### When Lead Scheduled for Site Visit
1. Create calendar event (Color 9 - blue)
2. Add 30-min travel buffer before (Keys geography)
3. Set reminder: day before + 1 hour before
4. Event title: "Site Visit: [Client Name] - [Address]"

### When Site Visit Completed
1. Prompt to block estimate prep time
2. Create event next available morning (Color 10 - green)
3. Event title: "Estimate Prep: [Client Name]"
4. Duration: 2 hours default

### Daily Time Blocking (6 PM Prompt)
1. Luna asks what needs time tomorrow
2. Creates events based on response
3. Color-codes by task type

### Morning Briefing (7 AM)
1. Read today's calendar
2. List appointments with times
3. Flag any conflicts or tight schedules

---

## Manual Commands (via Luna)

**Block time:**
"Block 2 hours tomorrow morning for estimate prep"
"Schedule site visit with John Smith at 123 Ocean Dr for Tuesday 2pm"

**Check calendar:**
"What's on my calendar tomorrow?"
"Am I free Thursday afternoon?"

**Move/cancel:**
"Move the Smith site visit to Wednesday"
"Cancel tomorrow's 9am"

---

## Travel Time Guidelines (Florida Keys)

From Marathon (approximate):
- Key West: 50 min
- Big Pine Key: 20 min
- Islamorada: 30 min
- Key Largo: 60 min

Luna adds travel buffer based on address when scheduling site visits.

---

## Integration with CRM

```
Lead Created
    ↓
Site Visit Scheduled → Calendar: Site Visit event
    ↓
Site Visit Complete
    ↓
Status → Measured → Calendar: Estimate Prep block
    ↓
Estimate Sent → Calendar: Follow-up reminders (Day 2/5/10)
```

---

*Integration configured: January 24, 2026*
