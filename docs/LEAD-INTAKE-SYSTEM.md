# ISLA Builders — Lead Intake System

## The Vision

**Lead comes in → Luna handles everything → Jaasiel focuses on craft**

When the marketing campaign hits, this system catches every lead, nurtures them automatically, and only bothers Jaasiel when human judgment is needed.

---

## Lead Sources

| Source | How Luna Catches It |
|--------|---------------------|
| Website forms | Auto-detected via email monitor (every 15 min) |
| Phone calls | Jaasiel texts Luna the details |
| Referrals | Jaasiel texts Luna the details |
| Google Business | Future: email monitor or API |
| Angi/HomeAdvisor | Future: email monitor |

---

## Lead Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        LEAD COMES IN                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. CAPTURE                                                      │
│  • Auto (email) or Manual (text to Luna)                        │
│  • Required: Name, Phone, Service Type                          │
│  • Optional: Email, Address, Details, Source                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. QUALIFY                                                      │
│  • Service match? (spalling, windows, deck, balcony, remodel)   │
│  • Location OK? (Florida Keys service area)                     │
│  • Timeline? (urgent, soon, planning)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. SCHEDULE SITE VISIT                                         │
│  • Luna suggests available slots from calendar                  │
│  • Jaasiel confirms or adjusts                                  │
│  • Calendar event created with client info                      │
│  • Luna texts client confirmation (optional)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. FOLLOW-UP SEQUENCE (if no response)                         │
│  • Day 1: Initial contact attempt (call)                        │
│  • Day 2: Text follow-up                                        │
│  • Day 5: Second follow-up                                      │
│  • Day 10: Final attempt + mark cold if no response             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. SITE VISIT COMPLETE                                         │
│  • Jaasiel texts measurements/notes to Luna                     │
│  • Luna logs to lead record                                     │
│  • Triggers estimate creation workflow                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. ESTIMATE & PROPOSAL                                         │
│  • Luna generates estimate from notes + templates               │
│  • Creates JobTread proposal                                    │
│  • Sends to client via JobTread portal                          │
│  • Luna texts client: "Estimate on the way"                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. DECISION                                                     │
│  • WON → Create job, schedule start, celebrate 🎉               │
│  • LOST → Log reason, schedule 30-day check-in                  │
│  • NO RESPONSE → Follow-up sequence on proposal                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Lead Data Structure

```json
{
  "id": "lead_20260125_001",
  "status": "new|contacted|site_scheduled|estimate_sent|won|lost|cold",
  "priority": "hot|warm|cold",
  
  "contact": {
    "name": "Kent Lee",
    "phone": "(360) 430-0010",
    "email": "kentslee@hotmail.com",
    "address": "123 Ocean Dr, Key Largo, FL",
    "preferredContact": "phone|text|email"
  },
  
  "project": {
    "service": "spalling|windows|deck|balcony|remodel|other",
    "details": "Pillar repair on front porch",
    "urgency": "urgent|soon|planning",
    "estimatedValue": null
  },
  
  "source": {
    "type": "website|phone|referral|google|angi",
    "referredBy": null,
    "emailId": "19bcd7727b3ab5ed",
    "capturedAt": "2026-01-25T06:00:00Z"
  },
  
  "timeline": {
    "firstContact": null,
    "siteVisit": null,
    "estimateSent": null,
    "decision": null
  },
  
  "followUps": [
    {"date": "2026-01-26", "type": "call", "status": "pending"},
    {"date": "2026-01-28", "type": "text", "status": "pending"}
  ],
  
  "notes": [],
  
  "outcome": {
    "result": null,
    "reason": null,
    "jobTreadId": null,
    "finalValue": null
  }
}
```

---

## Conversational Intake Examples

### Quick Capture (minimum info)
```
Jaasiel: "New lead - John Smith, 305-555-1234, spalling repair"
Luna: "Got it! 📝
  Name: John Smith
  Phone: 305-555-1234
  Service: Spalling repair
  
  Want me to schedule a follow-up call for today, or do you have more details?"
```

### Full Capture
```
Jaasiel: "Lead from referral - Maria Garcia, 305-555-5678, maria@email.com, 
         456 Palm Ave Key West, needs impact windows, Bob Jones referred her, 
         she wants quote ASAP"
         
Luna: "Got it! 🔥 HOT LEAD
  Name: Maria Garcia
  Phone: 305-555-5678
  Email: maria@email.com
  Address: 456 Palm Ave, Key West
  Service: Impact Windows
  Referred by: Bob Jones
  Urgency: ASAP
  
  Marked as HOT. Want me to:
  1. Block time for a site visit tomorrow?
  2. Send her a text intro?
  3. Both?"
```

### Post-Call Capture
```
Jaasiel: "Just got off the phone with new lead"
Luna: "Nice! Give me the details:
  • Name?
  • Phone?
  • What do they need?
  • Where are they located?"
```

---

## Auto-Actions by Status

| Status | Luna Auto-Actions |
|--------|-------------------|
| `new` | Schedule Day 1 follow-up, alert Jaasiel |
| `contacted` | Schedule site visit prompt if not done |
| `site_scheduled` | Create calendar event, send reminders |
| `estimate_sent` | Start proposal follow-up sequence |
| `won` | 🎉 Celebrate, create JobTread job |
| `lost` | Log reason, schedule 30-day check-in |
| `cold` | Move to nurture list, quarterly check-in |

---

## Metrics to Track

- **Lead velocity**: Leads per week/month
- **Response time**: Hours from lead → first contact
- **Conversion rate**: Leads → Site visits → Estimates → Won
- **Average deal value**: By service type
- **Lead source ROI**: Which sources produce wins
- **Days to close**: Lead → Won average time

---

## Ready for Marketing

When the campaign launches:
1. ✅ Website forms auto-captured
2. ✅ Phone leads easy to log (text Luna)
3. ✅ Follow-up sequences automated
4. ✅ Nothing falls through cracks
5. ✅ Jaasiel gets alerts only when needed
6. ✅ Full pipeline visibility

**The machine is ready. Just add leads.** 🚀
