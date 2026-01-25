# ISLA Builders — JobTread Dashboard Blueprint

## Overview

This is a step-by-step guide to build the ultimate ISLA Builders dashboard in JobTread.

**Access:** JobTread → Settings → Dashboards → Create New Dashboard

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ISLA BUILDERS COMMAND CENTER                       │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│   💰 REVENUE        │   📊 PIPELINE        │   🎯 THIS WEEK                  │
│   PIPELINE          │   FUNNEL             │   ACTION ITEMS                  │
│   $XX,XXX           │   [Visual]           │   • Overdue tasks               │
│                     │                       │   • Pending proposals           │
├─────────────────────┼─────────────────────┼─────────────────────────────────┤
│   📈 PROPOSALS      │   ⏱️ DAYS TO         │   📅 UPCOMING                   │
│   THIS MONTH        │   ESTIMATE           │   SITE VISITS                   │
│   Sent: X           │   Avg: X days        │   [Task List]                   │
│   Won: X            │   Target: 2          │                                 │
├─────────────────────┴─────────────────────┴─────────────────────────────────┤
│   💵 REVENUE BY MONTH                        📊 WIN RATE TREND               │
│   [Bar Chart - Last 6 Months]                [Line Chart - Last 6 Months]    │
├─────────────────────────────────────────────────────────────────────────────┤
│   📋 ACTIVE JOBS                             💬 RECENT ACTIVITY              │
│   [Job List with Status]                     [Activity Feed]                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tile-by-Tile Setup Instructions

### ROW 1

#### Tile 1: Revenue Pipeline (Number Tile)
**Purpose:** Total $ of pending proposals

**Settings:**
- Tile Type: **Number**
- Data Source: **Documents**
- Filter: 
  - Type = "Customer Order" (Proposal)
  - Status = "Pending"
- Value: **Sum of Price**
- Format: Currency
- Color: Green
- Goal: Set your monthly target (e.g., $50,000)

---

#### Tile 2: Pipeline Funnel (Chart Tile)
**Purpose:** Visual of leads by stage

**Settings:**
- Tile Type: **Chart (Bar or Funnel)**
- Data Source: **Jobs**
- Group By: **Custom Field "Status"** (create if needed)
  - Values: Lead → Quoted → Sold → In Progress → Complete
- Value: Count
- Sort: By status order

**If no Status field exists, create custom field:**
1. Settings → Custom Fields → Jobs
2. Add "Status" (Dropdown)
3. Options: Lead, Site Visit Scheduled, Quoted, Negotiating, Sold, In Progress, Complete, Lost

---

#### Tile 3: This Week Action Items (List Tile)
**Purpose:** Tasks due this week

**Settings:**
- Tile Type: **List**
- Data Source: **Tasks**
- Filter:
  - End Date = This Week
  - Progress < 100%
- Sort: End Date (ascending)
- Show: Task Name, Job Name, End Date
- Limit: 10 items

---

### ROW 2

#### Tile 4: Proposals This Month (Number Grid)
**Purpose:** Proposals sent vs won

**Settings:**
- Tile Type: **Number** (create 2 tiles side by side)

**Tile 4a - Sent:**
- Data Source: Documents
- Filter: Type = Customer Order, Created This Month
- Value: Count
- Label: "Proposals Sent"

**Tile 4b - Won:**
- Data Source: Documents
- Filter: Type = Customer Order, Status = Accepted, Updated This Month
- Value: Count
- Label: "Proposals Won"
- Color: Green

---

#### Tile 5: Days to Estimate (Number Tile)
**Purpose:** Average time from job creation to proposal

**Settings:**
- Tile Type: **Number**
- Data Source: **Documents**
- Filter: Type = Customer Order, Created This Month
- Formula: `AVG(DAYS(document.createdAt - job.createdAt))`
- Label: "Avg Days to Estimate"
- Goal Threshold: 
  - Green: ≤ 2 days
  - Yellow: 3-4 days
  - Red: > 4 days

*Note: Formula syntax depends on JobTread's formula builder. May need adjustment.*

---

#### Tile 6: Upcoming Site Visits (List Tile)
**Purpose:** Next 7 days of scheduled tasks

**Settings:**
- Tile Type: **List**
- Data Source: **Tasks**
- Filter:
  - Name contains "Site Visit" OR Task Type = Site Visit
  - Start Date = Next 7 Days
- Sort: Start Date (ascending)
- Show: Task Name, Job Name, Customer, Start Date
- Limit: 10

---

### ROW 3

#### Tile 7: Revenue by Month (Chart Tile)
**Purpose:** Won revenue trend

**Settings:**
- Tile Type: **Chart (Bar)**
- Data Source: **Documents**
- Filter: Type = Customer Order, Status = Accepted
- Group By: Created Month (Last 6 months)
- Value: Sum of Price
- Show: Monthly totals with trend line

---

#### Tile 8: Win Rate Trend (Chart Tile)
**Purpose:** Proposal close rate over time

**Settings:**
- Tile Type: **Chart (Line)**
- Data Source: **Documents**
- Filter: Type = Customer Order
- Group By: Month
- Formula: `COUNT(Status = Accepted) / COUNT(*) * 100`
- Label: "Win Rate %"
- Goal Line: 30% (or your target)

---

### ROW 4

#### Tile 9: Active Jobs (List Tile)
**Purpose:** All open jobs with status

**Settings:**
- Tile Type: **List**
- Data Source: **Jobs**
- Filter: Closed On = Empty (open jobs)
- Sort: Created (descending)
- Show: Job Number, Name, Customer, Created Date
- Limit: 15
- Click Action: Open Job

---

#### Tile 10: Recent Activity (Activity Feed Tile)
**Purpose:** Live feed of what's happening

**Settings:**
- Tile Type: **Activity Feed**
- Data Source: **Daily Logs** or **All Activity**
- Filter: Last 7 Days
- Show: Activity description, User, Timestamp
- Limit: 20 items

---

## Custom Fields to Create First

Before building the dashboard, create these custom fields if they don't exist:

### Jobs Custom Fields
1. **Lead Source** (Dropdown)
   - Phone, Website, Referral, Repeat Customer, Other

2. **Job Status** (Dropdown)
   - Lead, Site Visit Scheduled, Measured, Proposal Sent, Negotiating, Won, Lost, In Progress, Complete

3. **Service Type** (Dropdown)
   - Spalling Repair, Impact Windows/Doors, Deck, Balcony Repair, Remodeling, Other

### Documents Custom Fields
1. **Follow-Up Status** (Dropdown)
   - Pending, Day 2 Sent, Day 5 Sent, Day 10 Sent, Responded, Closed

---

## Step-by-Step Creation

### Step 1: Access Dashboard Builder
1. Log into JobTread
2. Click **Settings** (gear icon)
3. Select **Dashboards**
4. Click **+ Create Dashboard**
5. Name it: "ISLA Command Center"

### Step 2: Add Tiles
1. Click **+ Add Tile**
2. Select tile type (Number, Chart, List, Activity)
3. Configure data source and filters
4. Set display options
5. Position with drag-and-drop

### Step 3: Set as Default
1. After building, click **Settings** on dashboard
2. Enable **"Set as Default"**
3. Enable **"Full Screen Mode"** for office display

### Step 4: Mobile Access
- Dashboard automatically works on mobile
- Tiles stack vertically on phone

---

## Pro Tips

1. **Full Screen Mode:** Enable for a TV in the office — auto-refreshes
2. **Sync Mode:** Multiple screens stay synchronized
3. **Goal Thresholds:** Set them for instant visual status (green/yellow/red)
4. **Formulas:** Use for calculated metrics like averages and rates
5. **Filters:** Date filters like "This Week" and "This Month" update automatically

---

## Future Enhancements

Once basic dashboard is working:
- Add lead source pie chart
- Add revenue by service type
- Add customer acquisition cost tracking
- Add job profitability metrics

---

## Need Help?

JobTread has video tutorials:
- https://www.jobtread.com/webinars/jobtread-updates-custom-dashboards-and-more

Or tell Luna what's not working — I'll troubleshoot.

---

*Blueprint created: January 24, 2026*
*For: ISLA Builders - Jaasiel Bacallao*
