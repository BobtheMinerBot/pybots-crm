# ISLA Builders — Game Plan for January 25, 2026

## Goal: Optimal Business Automation

**Yesterday:** Built the foundation (CRM structure, cron jobs, integrations)
**Today:** Connect the pipes (data flows, automated actions, real workflows)

---

## Morning Block (7 AM - 12 PM)

### 1. Email Integration (1 hour)
**Why:** Leads come through email. We need to catch them automatically.

**Tasks:**
- [ ] Set up email monitoring via `gog` (Gmail skill)
- [ ] Create filters for lead sources:
  - Website contact forms
  - Google Business inquiries
  - Referral emails
- [ ] Auto-create lead entry when new inquiry detected
- [ ] Alert Jaasiel via WhatsApp for hot leads

**Automation:** New email → Luna parses → Creates lead → Sends you alert

---

### 2. Lead Intake Workflow (1 hour)
**Why:** Turn scattered inquiries into organized leads with zero manual entry.

**Tasks:**
- [ ] Define lead capture command: "Luna, new lead: [name], [phone], [address], [service]"
- [ ] Build intake parser (voice notes, texts, emails)
- [ ] Auto-populate CRM fields
- [ ] Auto-schedule first follow-up
- [ ] Auto-create calendar block for site visit slot

**Automation:** You text details → Luna creates lead → Schedules follow-up → Blocks calendar

---

### 3. JobTread Dashboard Build (1 hour)
**Why:** Visual command center you check every morning.

**Tasks:**
- [ ] You click through UI (5 min per tile)
- [ ] Luna guides via WhatsApp step-by-step
- [ ] 6 core tiles minimum:
  1. Revenue Pipeline ($)
  2. Days to Estimate
  3. Win Rate
  4. Pending Proposals
  5. This Week's Tasks
  6. Active Jobs

---

## Afternoon Block (1 PM - 6 PM)

### 4. Estimate Generation System (2 hours)
**Why:** Cut estimate prep time from hours to minutes.

**Tasks:**
- [ ] Expand templates with unit pricing from your catalog
- [ ] Build "estimate wizard" command:
  - "Luna, estimate for [customer]: spalling, 500 sqft, moderate damage"
  - Luna generates line items, calculates total
- [ ] Output formats:
  - Quick text summary for client
  - Full breakdown for JobTread import
  - PDF for email attachment
- [ ] Connect to JobTread API to auto-create proposals

**Automation:** Describe job → Luna generates estimate → Creates JobTread proposal → Emails client

---

### 5. Client Communication Automation (1 hour)
**Why:** Keep clients informed without you typing every message.

**Tasks:**
- [ ] Status update templates:
  - "Site visit confirmed for [date]"
  - "Estimate ready - check your email"
  - "Project starts [date]"
  - "Work completed - invoice sent"
- [ ] Trigger rules:
  - Proposal sent → Auto-text "Estimate on the way"
  - Job started → Auto-text "Crew arriving today"
  - Invoice created → Auto-text payment reminder
- [ ] Integrate with WhatsApp or SMS

**Automation:** JobTread status change → Luna texts client automatically

---

### 6. Invoice & Payment Tracking (1 hour)
**Why:** Don't chase money — let Luna do it.

**Tasks:**
- [ ] Pull open invoices from JobTread API daily
- [ ] Age tracking (current, 30, 60, 90 days)
- [ ] Auto-reminder schedule:
  - Day 7: Friendly reminder
  - Day 21: Follow-up
  - Day 30: Escalation alert to you
- [ ] Weekly AR summary in Sunday report

**Automation:** Invoice ages → Luna sends reminder → Escalates if needed

---

## Evening Block (7 PM - 9 PM)

### 7. Weekly Reporting Dashboard (1 hour)
**Why:** Know exactly how the business is performing without digging.

**Tasks:**
- [ ] Build comprehensive weekly report:
  - Leads received / converted / lost
  - Revenue won vs target
  - Days to estimate trend
  - Win rate trend
  - Cash collected vs outstanding
  - Next week preview
- [ ] Auto-generate every Sunday 7 PM
- [ ] Send via WhatsApp with key highlights

---

### 8. Voice Command Integration (30 min)
**Why:** Hands-free operation while driving between sites.

**Tasks:**
- [ ] Define voice commands:
  - "Luna, add note to [job]: [note]"
  - "Luna, what's on my calendar today?"
  - "Luna, create lead for [name] at [address]"
  - "Luna, send [client] a site visit confirmation"
- [ ] Test via WhatsApp voice messages
- [ ] Confirm parsing accuracy

---

## Tomorrow's Success Metrics

| Metric | Target |
|--------|--------|
| New automations live | 5+ |
| Manual steps eliminated | 10+ |
| Time saved per lead | 30+ min |
| Email → Lead (auto) | Working |
| Estimate generation | <5 min |
| Client auto-updates | Working |

---

## The Vision We're Building Toward

```
LEAD COMES IN (email/call/text/referral)
        ↓
    [AUTOMATIC]
        ↓
Luna captures → Creates lead → Schedules follow-up → Blocks calendar
        ↓
    SITE VISIT
        ↓
Jaasiel texts measurements/notes
        ↓
    [AUTOMATIC]
        ↓
Luna generates estimate → Creates JobTread proposal → Emails client → Texts confirmation
        ↓
    CLIENT DECIDES
        ↓
    [AUTOMATIC]
        ↓
Won → Luna creates job → Schedules start → Notifies client
Lost → Luna logs reason → Schedules 30-day follow-up
        ↓
    PROJECT RUNS
        ↓
    [AUTOMATIC]
        ↓
Luna sends status updates → Tracks milestones → Creates invoices → Sends reminders
        ↓
    PROJECT COMPLETE
        ↓
    [AUTOMATIC]
        ↓
Luna sends thank you → Requests review → Adds to referral list
```

**That's the goal: You focus on craft and clients. Luna handles the paper.**

---

## Pre-Sleep Checklist for Tonight

- [x] CRM foundation built
- [x] Cron jobs running
- [x] Calendar integrated
- [x] JobTread API connected
- [x] Templates created
- [x] Metrics defined
- [ ] Get good sleep — tomorrow we build the machine

---

*Rest up, Boss. We're building something real.* 🐕‍🦺
