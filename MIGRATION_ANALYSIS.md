# SmartSuite → ISLA CRM Migration Analysis

## Source: SmartSuite Permit Tracker
- **127 Projects** (61 fields)
- **112 Customers** (16 fields)
- Currently relational (Customer → linked Projects)
- **Target: Flatten to single table**

---

## CUSTOMER DATABASE FIELDS (16 total)

| Field Name | Type | Notes |
|------------|------|-------|
| Customer Name | Text (Primary) | → Lead Name in new CRM |
| Customer Stage | Status/Select | Values: New Lead, Bid Sent, Follow Up, Complete |
| Customer Email | Email | → Email |
| Customer Address | Address | Customer's mailing address |
| Customer Phone | Phone | → Phone |
| Property Type | Single Select | Values: Residential, Commercial |
| Title 1 | Text | ? |
| First Created | Date (Auto) | System field |
| Job Scope | Text/Multi-select | Service interest |
| Link to Projects | Linked Record | Links to Projects table |
| Auto Number | Auto | System field |
| Description | Text | Notes about customer |
| ID | Text | System field |
| Last Updated | Date (Auto) | System field |
| Open Comments | Count/Rollup | System field |
| Property Address | Address | Different from customer address? |

---

## PROJECTS TABLE FIELDS (61 total)

### Core Project Info
| Field Name | Type | Notes |
|------------|------|-------|
| Title | Text (Primary) | Project name (often customer name) |
| Job Number | Text | Internal reference |
| Auto Number | Auto | System field |
| ID | Text | System field |
| Job Type | Select | Type of work |
| Service Provided | Select | ? |
| Scope | Text | Brief scope |
| Scope of Work | Long Text | Detailed scope |

### Status/Stage Fields
| Field Name | Type | Notes |
|------------|------|-------|
| Project Stage | Status | Master status |
| Current Stage | Status | ? Duplicate of Project Stage? |
| Sales Stage | Status | Sales pipeline stage |
| Permit Stage | Status | Permit process stage |
| Management Stage | Status | Project management stage |

### Location/Property Fields
| Field Name | Type | Notes |
|------------|------|-------|
| Location Address | Address | Project site address |
| Location Name | Text | Name of location |
| Property Owner Name | Text | Owner's name |
| Property Owner Address | Address | Owner's mailing address |
| Parcel ID | Text | County parcel ID |
| Folio # 1 | Text | County folio number |
| Folio # 2 | Text | Second folio if applicable |
| Block | Text | Subdivision block |
| Lot | Text | Subdivision lot |
| Legal_Description | Text | Legal description |
| Property Appraisal | URL | Link to property appraiser |
| Jurisdiction | Text | Which jurisdiction |

### Contact Fields (from linked Customer)
| Field Name | Type | Notes |
|------------|------|-------|
| Link to Customer Database | Linked Record | Link to customer |
| Cell | Phone | Customer cell (lookup?) |
| Email | Email | Customer email (lookup?) |

### Dates
| Field Name | Type | Notes |
|------------|------|-------|
| First Added | Date | When project was created |
| First Site Visit Date | Date | Initial site visit |
| Bid Sent Date | Date | When bid was sent |
| Bid Accepted Date | Date | When bid was accepted |
| Date Completed | Date | Project completion |
| Last Updated | Date (Auto) | System field |

### Financials
| Field Name | Type | Notes |
|------------|------|-------|
| Project Cost | Currency | Total project value |
| Budget Cost | Currency | Budgeted cost |
| Actual Cost | Currency | Actual cost |
| Budget Variance | Formula | Budget - Actual |
| Open Invoices | Currency/Count | Unpaid invoices |
| Paid Invoices | Currency/Count | Paid invoices |
| Pending Orders | Currency/Count | ? |
| Approved Orders | Currency/Count | ? |
| Bids | Number/Currency | ? |

### Permit Fields
| Field Name | Type | Notes |
|------------|------|-------|
| Needs Permits? | Checkbox | Does project need permits |
| Permit Required? | Checkbox | Duplicate? |
| Permit NO: | Text | Permit number |
| Engineering Plans Required? | Checkbox | Needs engineer drawings |
| Sign-ons Required? | Checkbox | Needs sign-offs |
| Generate Permits | Button/Automation | ? |
| Un-Signed Permits | Count | Permits needing signature |
| Online Portal | URL | Link to permit portal |
| Link to Jurisdiction Database | Linked Record | Jurisdiction info |

### Private Provider Fields
| Field Name | Type | Notes |
|------------|------|-------|
| Private Provider | Linked Record? | Link to PP database |
| PP Name | Text | Provider name |
| PP Cell | Phone | Provider phone |
| PP Email | Email | Provider email |
| PP Address | Address | Provider address |
| PP License # | Text | Provider license number |

### Workflow/Automation
| Field Name | Type | Notes |
|------------|------|-------|
| Forward Job to Permit | Button/Auto | Workflow trigger |
| Forward Job to MGT | Button/Auto | Workflow trigger |

### System Fields
| Field Name | Type | Notes |
|------------|------|-------|
| Open Comments | Count | Comments count |

---

## FIELD MAPPING RECOMMENDATION

### Merge Customer → Project (Flat Structure)

Since most projects are 1:1 with customers, merge customer data into project records:

**Keep from Projects:**
- Title → Lead Name
- Location Address → Address  
- Cell → Phone
- Email → Email
- Project Stage → Status (consolidated)
- Job Type → Job Type
- Scope of Work → Notes/Description
- All permit fields
- All financial fields
- All date fields

**Add from Customer (where different):**
- Customer Address → Billing Address (if different from Location)
- Property Type → Property Type
- Customer Stage → can inform Status

**Consolidate Statuses:**
Current SmartSuite has 5 separate stage fields:
- Project Stage
- Current Stage  
- Sales Stage
- Permit Stage
- Management Stage

Recommend: Single Status field with consolidated values:
- New Lead
- First Contact
- Site Visit Scheduled
- Bid Sent
- Follow Up
- Bid Accepted
- Permitting
- Active Construction
- Closeout
- Completed
- Lost/Dead

---

## NEXT STEPS

1. [ ] Export SmartSuite data to CSV
2. [ ] Create custom fields in new CRM matching above
3. [ ] Map and transform data
4. [ ] Import to new CRM
5. [ ] Verify data integrity

---

*Generated by Luna 🐕‍🦺 for ISLA Builders CRM Migration*
