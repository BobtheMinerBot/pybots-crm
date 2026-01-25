# Metrics Tracking

## Days to Estimate

**Definition:** Number of days from lead creation to estimate delivery.

**Formula:**
```
Days to Estimate = estimateSent date - created date
```

**Tracking:**
- Calculated per lead when `dates.estimateSent` is populated
- Rolling average stored in `metrics.json → avgDaysToEstimate`
- Weekly/monthly breakdowns available

**Goal:** Keep under 5 days for residential, 7 days for commercial

---

## Days to Close

**Definition:** Number of days from lead creation to won/lost status.

**Formula:**
```
Days to Close = closed date - created date
```

---

## Win Rate

**Definition:** Percentage of leads that convert to jobs.

**Formula:**
```
Win Rate = (leadsWon / (leadsWon + leadsLost)) × 100
```

**Current:** Calculated weekly in Weekly Review cron job

---

## How Luna Tracks These

### On Lead Entry
When a new lead is added:
```json
{
  "dates": {
    "created": "2026-01-24T10:00:00Z"
  }
}
```

### On Estimate Delivery
When estimate is sent:
```json
{
  "dates": {
    "estimateSent": "2026-01-26T14:00:00Z"
  }
}
```
→ Luna calculates: 2 days to estimate

### Weekly Calculation
Every Sunday at 7 PM, Luna:
1. Queries all leads with `estimateSent` dates in past week
2. Calculates average days to estimate
3. Updates `metrics.json`
4. Reports in weekly review

---

## Target Benchmarks (ISLA Builders)

| Metric | Target | Good | Needs Work |
|--------|--------|------|------------|
| Days to Estimate | <5 days | 3-5 days | >7 days |
| Days to Close | <14 days | 7-14 days | >21 days |
| Win Rate | >40% | 35-40% | <30% |
| Follow-up Response | <24 hrs | <24 hrs | >48 hrs |

---

## Reporting

**Morning Briefing (7 AM):**
- Yesterday's new leads
- Estimates due today
- Proposals pending response

**Weekly Review (Sunday 7 PM):**
- Week's win rate
- Average days to estimate
- Pipeline health
- Top pending proposals

**Monthly Summary (1st of month):**
- Revenue closed
- Leads converted
- Trend analysis
