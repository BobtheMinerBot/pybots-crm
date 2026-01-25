# ISLA CRM — Auto-Scheduling System

## How It Works

When Luna receives a new lead or needs to schedule a site visit:

1. **Check calendar** for next 5 business days
2. **Find open slots** (minimum 2-hour blocks)
3. **Calculate travel time** based on address
4. **Suggest 2-3 options** to Jaasiel
5. **Book on confirmation** with travel buffer

---

## Scheduling Rules

### Site Visit Windows
- **Preferred hours:** 8 AM - 5 PM
- **Minimum block:** 2 hours (visit + buffer)
- **Travel buffer:** Added before appointment based on location
- **No double-booking:** Check for conflicts

### Travel Time Matrix (from Marathon)
| Destination | Drive Time | Buffer Added |
|-------------|-----------|--------------|
| Marathon area | 0-15 min | 30 min |
| Big Pine / Lower Keys | 15-30 min | 45 min |
| Islamorada / Upper Keys | 30-45 min | 60 min |
| Key Largo | 45-60 min | 75 min |
| Key West | 45-60 min | 75 min |

### Priority Logic
1. ASAP leads → Next available slot
2. Planning leads → Within 3-5 days
3. Just looking → Within 1-2 weeks

---

## Slot Suggestion Format

When suggesting times, Luna says:

"Got a lead for [Service] at [Address]. Here are available slots:

1. **Tomorrow (Mon)** — 10 AM - 12 PM
2. **Tuesday** — 2 PM - 4 PM  
3. **Thursday** — 9 AM - 11 AM

Which works? Or give me a different time."

---

## Booking Confirmation

When Jaasiel picks a slot:
1. Create calendar event (blue - site visit)
2. Add travel buffer before
3. Update lead status to "Site Visit Scheduled"
4. Set day-before reminder
5. Confirm: "Booked: [Client] site visit [Day] at [Time]. Travel buffer added."

---

## Commands

**Auto-suggest:**
"Schedule a site visit for [Lead Name]"
→ Luna checks calendar, suggests slots

**Manual book:**
"Book [Lead Name] for Tuesday 2pm"
→ Luna books directly, adds buffer

**Check availability:**
"What's open this week for site visits?"
→ Luna shows available 2-hour blocks

---

*System initialized: January 24, 2026*
