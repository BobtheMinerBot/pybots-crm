# Luna Lead Intake Guide

## When Jaasiel Texts Lead Details

This is how I handle incoming lead information from Jaasiel.

---

## Detection Patterns

Watch for messages that include:
- "new lead" / "got a lead" / "lead from"
- "just talked to" / "call from" / "phone call"
- "referral from" / "[name] referred"
- Names + phone numbers together
- Service keywords (spalling, windows, deck, balcony, remodel)

---

## Parsing Priority

**Required (must have or ask):**
1. Name
2. Phone number
3. Service type

**Important (capture if mentioned):**
4. Address/location
5. Email
6. Source (referral, website, etc.)
7. Referrer name (if referral)
8. Urgency

**Nice to have:**
9. Project details
10. Timeline preferences

---

## Response Flow

### If ALL required info present:
1. Confirm what I captured
2. Ask about urgency (hot/warm/cold)
3. Offer next actions (schedule follow-up, site visit, etc.)
4. Save to leads.json
5. Create follow-up entry

### If MISSING required info:
1. Acknowledge what I got
2. Ask for missing pieces naturally
3. Once complete, confirm and save

---

## Service Type Mapping

| Keywords | Maps To |
|----------|---------|
| spalling, concrete, pillar, column, repair | spalling |
| window, windows, impact, hurricane | windows |
| door, doors, impact door, sliding | windows |
| deck, patio, outdoor | deck |
| balcony, railing, balcony repair | balcony |
| remodel, renovation, kitchen, bath, addition | remodel |
| other/unclear | other |

---

## Priority Assignment

| Indicators | Priority |
|------------|----------|
| ASAP, urgent, emergency, needs now | hot |
| Soon, this month, ready to move | warm |
| Planning, thinking about, eventually | cold |
| Referral (any) | warm minimum |
| Large project / high value | warm minimum |

---

## Auto Follow-Up Schedule

When I create a new lead, schedule:

| Priority | Day 1 | Day 2 | Day 5 | Day 10 |
|----------|-------|-------|-------|--------|
| hot | Call | Text | Call | Final |
| warm | Call | Text | Text | Final |
| cold | Text | - | Text | Final |

---

## Example Responses

### Complete Info:
```
Got it! 📝

New Lead:
• Name: Maria Garcia
• Phone: 305-555-5678
• Service: Impact Windows
• Source: Referral (Bob Jones)
• Urgency: ASAP → Marked HOT 🔥

Saved to CRM. Follow-up call scheduled for today.

Want me to check your calendar for site visit slots this week?
```

### Incomplete Info:
```
Got it - new lead from phone call:
• Name: John
• Service: Spalling repair

What's the phone number? And did you catch a last name?
```

### Post-Call Prompt:
```
Nice! Give me the details:
• Name?
• Phone number?
• What do they need done?
• Location (if you got it)?
```

---

## Saving to leads.json

After confirming with Jaasiel, I:

1. Generate ID: `lead_YYYYMMDD_NNN` (increment NNN)
2. Set status: `new`
3. Set priority based on urgency indicators
4. Fill in all captured fields
5. Create follow-up schedule based on priority
6. Update metadata.lastId and lastUpdated

---

## Calendar Integration

If scheduling site visit:
1. Check calendar for available slots (GOG_KEYRING_PASSWORD="isla2026")
2. Suggest 2-3 options
3. Once confirmed, create event with:
   - Title: "Site Visit - [Client Name] - [Service]"
   - Description: All lead details
   - Color: 9 (blue) for site visits
   - Location: Client address

---

## Files to Update

- `/Users/jb/clawd/projects/isla-crm/data/leads.json` — Add new lead
- `/Users/jb/clawd/projects/isla-crm/data/followups.json` — Add follow-up entries
- `/Users/jb/clawd/memory/YYYY-MM-DD.md` — Log the lead capture

---

*Every lead matters. Capture clean. Follow up fast.* 🐕‍🦺
