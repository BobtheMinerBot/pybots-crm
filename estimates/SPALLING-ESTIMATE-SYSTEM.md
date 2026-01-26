# Spalling Estimate System v1

## Trigger Phrases
- "new spalling estimate"
- "spalling estimate for [name]"
- "new estimate for [name]"

---

## Smart Intake Flow

### Step 1: Client Lookup
When user says "new spalling estimate for [Client Name]":

1. **Search CRM** (pybots API):
   ```
   GET https://pybots.pythonanywhere.com/api/leads?search=[name]
   Header: X-API-Key: BoTGdKZCMhf8_uWQ1DHjAXlsM9Jk4kqG9thsq9iVz_o
   ```

2. **Search JobTread** for existing customer:
   ```
   organization.accounts where name like "%[name]%"
   ```

3. **Search JobTread** for existing job (if customer found):
   ```
   account.locations.jobs
   ```

### Step 2: Present Template

**If client found:**
```
📋 SPALLING ESTIMATE

Found: [Client Name]
Address: [Address from CRM/JobTread]
Phone: [Phone]
JobTread: [Job #XX - Job Name] ✓ (or "Will create new")

Just need the repair details:

REPAIRS:
• Column: ___ cf
• Tie Beam: ___ cf
• Cantilever: ___ cf
• Slab: ___ cf / sf

PRICING:
• $/cf: (default $400)
• $/sf for slab: (default $135)

PERMITS: Y/N
PLANS: Y/N

NOTES:
```

**If client NOT found:**
```
📋 SPALLING ESTIMATE

Client not found in CRM. Need full details:

Client name:
Address:
Phone:
Email (optional):

REPAIRS:
• Column: ___ cf
• Tie Beam: ___ cf
• Cantilever: ___ cf
• Slab: ___ cf / sf

PRICING:
• $/cf: (default $400)
• $/sf for slab: (default $135)

PERMITS: Y/N
PLANS: Y/N

NOTES:
```

### Step 3: Parse Response

Extract from user's reply:
- `column_cf`: number (default 0)
- `tie_beam_cf`: number (default 0)
- `cantilever_cf`: number (default 0)
- `slab_qty`: number (default 0)
- `slab_unit`: "cf" or "sf" (default "cf")
- `price_per_cf`: number (default 400)
- `price_per_sf`: number (default 135)
- `include_permits`: boolean
- `include_plans`: boolean
- `notes`: string

### Step 4: Generate Estimate

**Line Items:**

| Item | Qty | Unit | Unit Price | Total |
|------|-----|------|------------|-------|
| Spalling - Column | X | cf | $Y | $Z |
| Spalling - Tie Beam | X | cf | $Y | $Z |
| Spalling - Cantilever | X | cf | $Y | $Z |
| Spalling - Slab | X | cf/sf | $Y | $Z |
| Building permits | 1 | ea | $1,500 | $1,500 |
| Building Plans/Drawings | 1 | ea | $1,500 | $1,500 |

**Standard Descriptions:**

- **Column/Tie Beam/Cantilever:**
  > Demo spalled concrete until reaching sound concrete, replace corroded rebar with new galvanized rebar as needed, clean and coat remaining rebar with rust preventing acid. Form and Pour using 5000 psi concrete. Stucco and paint to match existing as close as possible.

- **Slab:**
  > Remove spalled concrete and expose rebar, clean and coat with rust preventing acid. Form and pour using 5000 psi concrete. Finish to match existing as close as possible.

- **Building permits:**
  > The contractor shall handle the entire permit procurement process, including completing and submitting applications, obtaining required signatures, and ensuring timely processing. Permit fees paid by Customer.

- **Building Plans/Drawings:**
  > Signed and sealed engineering plans showing specified locations and repair details for the city permit process.

### Step 5: Confirm & Create

Present summary:
```
📊 ESTIMATE SUMMARY

Client: John Norville
Address: 456 Sombrero Beach Rd, Marathon
Job: #135 - Column Spalling Repair

LINE ITEMS:
• Spalling - Column: 12 cf × $425 = $5,100
• Spalling - Tie Beam: 8 cf × $425 = $3,400
• Spalling - Slab: 40 sf × $140 = $5,600
• Building permits: $1,500
• Building Plans/Drawings: $1,500

TOTAL: $17,100

Create proposal in JobTread? (Y/N)
```

On approval, create proposal via JobTread API with status = "draft"

---

## Pricing Defaults

| Item | Default Price |
|------|---------------|
| Column (cf) | $400 |
| Tie Beam (cf) | $400 |
| Cantilever (cf) | $400 |
| Slab (cf) | $400 |
| Slab (sf) | $135 |
| Building permits | $1,500 |
| Building Plans/Drawings | $1,500 |

**Cost tracking:** Deferred to later phase

---

## JobTread API - Create Proposal ✅ WORKING

### Required Fields for createDocument:
```json
{
  "jobId": "JOB_ID",
  "type": "customerOrder",
  "name": "Spalling Repair Proposal",  // Must be from predefined list
  "fromName": "ISLA Builders",
  "toName": "Customer Name",
  "jobLocationName": "Location Name",
  "jobLocationAddress": "Full Address",
  "taxRate": 0,
  "dueDays": 30
}
```

**Valid document names:** Proposal, Selections, Change Order, T/M CONTRACT, Spalling Repair Proposal

### Create Proposal
```bash
curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "API_KEY", "notify": false},
      "createDocument": {
        "$": {
          "jobId": "JOB_ID",
          "type": "customerOrder",
          "name": "Spalling Repair Proposal",
          "fromName": "ISLA Builders",
          "toName": "Customer Name",
          "jobLocationName": "Property Name",
          "jobLocationAddress": "123 Street, City, FL 33050, USA",
          "taxRate": 0,
          "dueDays": 30
        }
      },
      "createdDocument": {"id": {}, "number": {}, "status": {}}
    }
  }'
```

### Add Cost Items
```bash
curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "API_KEY", "notify": false},
      "createCostItem": {
        "$": {
          "documentId": "DOCUMENT_ID",
          "costTypeId": "22NkjDG45qzH",
          "name": "Spalling - Column",
          "description": "Demo spalled concrete...",
          "quantity": 12,
          "unitPrice": 425,
          "costCodeId": "22NtteKwSvr7"
        }
      },
      "createdCostItem": {"id": {}}
    }
  }'
```

**Cost Codes:**
- Spalling Repair: `22NtteKwSvr7`
- Masonry: `22NiF3Lw9F8M`
- Uncategorized: `22NiF3Lw9F8E`
- Permit Fees: `22NzPQPYWL88`

**Cost Types:**
- Materials and Install: `22NkjDG45qzH` (use for spalling line items)
- Permit Fee: `22NzPQRhGXmv` (use for permits/plans)
- Labor: `22NiF3Lw9F8n`
- Materials: `22NiF3Lw9F8p`
- Subcontractor: `22NiF3Lw9F8q`
- Other: `22NiF3Lw9F8r`

---

---

## Photo Workflow

**When Jaasiel sends site photos:**

1. Save to job folder:
   ```
   /projects/isla-crm/photos/[JobNum]_[Client]/
   ```

2. Example for Job #140:
   ```
   /projects/isla-crm/photos/140_Lunabot/
   ├── site_plan.jpg
   ├── column_1.jpg
   └── slab_damage.jpg
   ```

3. When reviewing draft in JobTread → drag & drop photos from folder

**Note:** Direct API upload is complex (requires upload request + file creation). 
Local folder + manual upload is faster for now.

---

## Template Setup (One-Time in JobTread UI)

To get full formatting on proposals:

1. **Settings → Organization:**
   - Add phone number
   - Add email address

2. **Edit "Spalling Repair Proposal" template:**
   - Set up cost item groups (Permits, Spalling Repair)
   - Add terms/footer with payment schedule
   - Set style to "Modern"

3. **When creating proposals via API:**
   - Use `templateId: "22PQnm2z49h8"` (Spalling Repair Proposal)
   - Template settings will apply automatically

---

## Version History

- **v1.1 (2026-01-25):** Added photo workflow, template usage
- **v1 (2026-01-25):** Initial spalling-only system
