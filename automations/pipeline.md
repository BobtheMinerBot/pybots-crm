# ISLA CRM — Estimate Pipeline Tracking

## Overview

Track every estimate from site visit to proposal sent. Goal: ≤2 business days.

---

## Pipeline Record Structure

```json
{
  "id": "est-001",
  "leadId": "lead-001",
  "clientName": "John Smith",
  "service": "spalling",
  "address": "123 Ocean Dr, Marathon",
  
  "siteVisitDate": "2026-01-24",
  "siteVisitNotes": "3 columns, moderate damage, ~150 sq ft total",
  "measurements": "Col 1: 4x8, Col 2: 3x6, Col 3: 5x10",
  "photos": ["photo1.jpg", "photo2.jpg"],
  
  "estimatePrepStarted": "2026-01-25",
  "estimatePrepHours": 2,
  "estimateCreatedDate": "2026-01-25",
  "proposalSentDate": "2026-01-25",
  
  "jobtreadDocumentId": "22PQnwxPAy5t",
  "proposalAmount": 8500,
  
  "daysToEstimate": 1,
  "onTime": true,
  "status": "sent"
}
```

---

## Pipeline Stages

### 1. Site Visit Complete
**Trigger:** Lead status changed to "measured"
**Capture:**
- Site visit date
- Measurements (text notes)
- Photos (file references)
- Rough notes

**Luna asks:**
"Site visit complete for [Client]. Got measurements/notes to capture?"

### 2. Estimate Prep
**Trigger:** Jaasiel says "working on estimate for [Client]"
**Actions:**
- Record prep start time
- Track time spent
- Alert if approaching SLA

### 3. Estimate Created
**Trigger:** Estimate built in JobTread
**Actions:**
- Record creation date
- Calculate days since site visit
- Flag if over SLA

### 4. Proposal Sent
**Trigger:** Jaasiel says "sent estimate to [Client]"
**Actions:**
- Record sent date
- Start follow-up sequence
- Log final metrics

---

## SLA Tracking

### Target: 2 Business Days

| Days | Status | Action |
|------|--------|--------|
| 0-1 | Green ✅ | On track |
| 2 | Yellow ⚠️ | Due today |
| 3+ | Red 🔴 | Overdue alert |

### Daily SLA Check (Part of Morning Briefing)

Luna checks pipeline.json for:
- Estimates in progress > 1 day
- Site visits without estimate started
- Overdue proposals

**Alert format:**
"⚠️ Estimate SLA:
• John Smith (spalling) — site visit 2 days ago, no estimate started
• Maria Garcia (windows) — estimate due TODAY"

---

## Commands

**Log site visit:**
"Finished site visit for [Client]. Notes: [details]"
→ Luna records date, notes, prompts for measurements

**Log measurements:**
"Measurements for [Client]: [details]"
→ Luna stores in pipeline record

**Start estimate:**
"Working on [Client]'s estimate"
→ Luna starts prep timer

**Estimate sent:**
"Sent estimate to [Client] for $[amount]"
→ Luna completes pipeline, starts follow-up sequence

**Check pipeline:**
"What estimates are pending?"
→ Luna shows in-progress estimates with days elapsed

---

## Metrics Tracked

### Per Estimate
- Days from site visit to proposal sent
- On-time (≤2 days) or late
- Prep time spent

### Aggregate (Weekly/Monthly)
- Average days to estimate
- On-time rate (% within SLA)
- Total estimates sent
- Conversion rate (estimates → won)

---

## Integration with Follow-Ups

When estimate is sent:
1. Pipeline record marked "sent"
2. Follow-up sequence triggered (Day 2/5/10)
3. If proposal accepted → Pipeline record marked "won"
4. If proposal declined → Pipeline record marked "lost"

---

*System initialized: January 24, 2026*
