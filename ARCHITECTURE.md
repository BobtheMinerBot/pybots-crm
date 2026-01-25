# ISLA Builders CRM - System Architecture

*Built for speed, automation, and one-person operation*

---

## 🎯 Core Philosophy

- **Automation First** — If it can be automated, it should be
- **Fast Turnaround** — Lead to estimate in ≤2 business days
- **Single Source of Truth** — JobTread is the backbone, CRM extends it
- **Mobile-Friendly** — Jaasiel is in the field, not at a desk

---

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        LEAD INTAKE                               │
│         (Phone Calls, Website Forms, Referrals)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LEAD MANAGEMENT                             │
│    • Auto-capture & categorize                                   │
│    • Smart scheduling for site visits                            │
│    • Follow-up automation                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ESTIMATE PIPELINE                             │
│    • Site visit → Measurements → Proposal                        │
│    • JobTread integration for pricing                            │
│    • Template library by service type                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PROJECT MANAGEMENT                             │
│    • Won jobs → Active projects                                  │
│    • Milestone tracking                                          │
│    • Client communication portal                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TIME & TASK MANAGEMENT                          │
│    • Daily planning prompts                                      │
│    • Auto calendar blocking                                      │
│    • Task prioritization                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Module 1: Lead Management

### Lead Sources
| Source | Capture Method | Automation Level |
|--------|---------------|------------------|
| Website Form | Webhook → Auto-create lead | Full |
| Phone Call | Voice note/text to Luna → Create lead | Semi-auto |
| Referral | Manual entry or text to Luna | Semi-auto |

### Lead Record Structure
```
Lead {
  id: string
  created: timestamp
  source: "website" | "phone" | "referral" | "other"
  
  // Contact Info
  name: string
  phone: string
  email: string
  address: string
  
  // Project Info
  service_type: "spalling" | "remodel" | "windows_doors" | "deck" | "balcony" | "other"
  description: string
  urgency: "asap" | "planning" | "just_looking"
  
  // Status Tracking
  status: "new" | "contacted" | "site_visit_scheduled" | "measured" | "estimate_sent" | "won" | "lost"
  next_action: string
  next_action_date: date
  
  // Integration
  jobtread_id: string (once converted)
}
```

### Automations
1. **New Lead Alert** — Instant notification when lead comes in
2. **Auto-Schedule Prompt** — "New lead for spalling repair. Want me to find available times for a site visit?"
3. **Follow-Up Reminders** — Auto-ping if no activity in 24/48/72 hours
4. **Status Updates** — Auto-move through pipeline based on actions

---

## 📦 Module 2: Estimate Pipeline

### Workflow
```
Site Visit Scheduled
       │
       ▼
  Site Visit Complete
  (measurements captured)
       │
       ▼
  Office Time Blocked
  (for estimate prep)
       │
       ▼
  Estimate Created in JobTread
       │
       ▼
  Proposal Sent to Client
       │
       ▼
  Follow-Up Sequence Triggered
```

### Estimate Templates (by Service Type)
- **Spalling Repair** — Sq ft based, includes assessment photos
- **Impact Windows/Doors** — Unit count, sizes, impact rating
- **Deck/Balcony** — Sq ft + linear ft railings + materials
- **Remodel** — Custom scope builder

### Automations
1. **Post-Visit Prompt** — "Site visit complete. Blocking 2 hours tomorrow for estimate prep?"
2. **Estimate Timer** — Track time from visit to estimate sent (goal: ≤2 days)
3. **Template Suggestions** — Auto-suggest template based on service type
4. **Proposal Follow-Up** — Auto-sequence: Day 2, Day 5, Day 10

---

## 📦 Module 3: Time & Task Management

### Daily Planning System
- **6 PM Daily Prompt** — "What office tasks need time tomorrow?"
- **Smart Blocking** — Luna blocks calendar based on priorities
- **Morning Briefing** — Quick rundown of today's schedule + priorities

### Task Categories
| Category | Auto-Generated From | Default Duration |
|----------|--------------------:|------------------|
| Site Visit | New lead scheduled | 1-2 hours |
| Estimate Prep | Completed site visit | 2 hours |
| Follow-Up Calls | Pipeline stage changes | 30 min |
| Admin/Office | Manual or recurring | Varies |

### Calendar Integration
- Google Calendar sync (via gog skill)
- Color coding by task type
- Buffer time between field visits
- Travel time estimation (Keys geography)

---

## 📦 Module 4: Client Communication

### Touchpoints
1. **Initial Response** — Within 4 hours of lead (automated acknowledgment)
2. **Site Visit Confirmation** — Day before reminder
3. **Estimate Delivery** — Personal message with proposal link
4. **Follow-Up Sequence** — Automated but personalized
5. **Won/Lost** — Thank you or feedback request

### Communication Channels
- **Primary:** Phone/Text (through Jaasiel or Luna proxy)
- **Secondary:** Email (formal proposals, documentation)
- **Portal:** JobTread client portal for project updates

---

## 📦 Module 5: Reporting & Insights

### Key Metrics Dashboard
- **Lead Velocity** — New leads per week/month
- **Conversion Rate** — Leads → Won jobs
- **Time to Estimate** — Average days from visit to proposal
- **Win Rate by Service** — Which services close best
- **Revenue Pipeline** — Estimated value of active proposals

### Weekly Review Prompt
Luna generates a weekly summary:
- Leads received vs contacted
- Estimates sent vs target
- Pipeline value
- Upcoming deadlines

---

## 🔧 Technical Implementation

### Data Storage
```
/Users/jb/clawd/projects/isla-crm/
├── ARCHITECTURE.md      (this file)
├── data/
│   ├── leads.json       (lead records)
│   ├── templates/       (estimate templates)
│   └── metrics/         (tracking data)
├── automations/
│   └── workflows.md     (automation rules)
└── docs/
    └── procedures.md    (SOPs)
```

### Integration Points
| System | Integration | Purpose |
|--------|-------------|---------|
| JobTread | API | Estimates, projects, client data |
| Google Calendar | gog skill | Scheduling, time blocking |
| QuickBooks | Existing sync | Invoicing (future) |
| Website | Webhook | Lead capture |

### Luna's Role
- **Proactive:** Daily check-ins, reminders, follow-ups
- **Reactive:** Process leads, schedule tasks, answer questions
- **Analytical:** Weekly reports, pipeline reviews

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [x] Daily time blocking prompt ✓
- [ ] Lead data structure finalized
- [ ] Basic lead intake workflow
- [ ] Manual lead entry via chat

### Phase 2: Automation (Week 3-4)
- [ ] Website form webhook integration
- [ ] Auto-scheduling suggestions
- [ ] Follow-up reminder system
- [ ] Calendar blocking automation

### Phase 3: Pipeline (Week 5-6)
- [ ] Estimate pipeline tracking
- [ ] JobTread workflow integration
- [ ] Template library setup
- [ ] Proposal follow-up sequences

### Phase 4: Insights (Week 7-8)
- [ ] Metrics tracking
- [ ] Weekly review automation
- [ ] Dashboard/reporting
- [ ] Optimization based on data

---

## 📝 Next Steps

1. **Review this architecture** — Does this match your vision?
2. **Prioritize features** — What's most painful right now?
3. **Website form setup** — Do you have a contact form? What fields?
4. **Calendar access** — Confirm Google Calendar integration working

---

*Architecture v1.0 — January 24, 2026*
*Built by Luna for ISLA Builders* 🐕‍🦺
