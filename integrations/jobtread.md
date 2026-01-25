# ISLA CRM — JobTread Integration

## Connection Details
- **API Endpoint:** https://api.jobtread.com/pave
- **Organization ID:** 22NiF3LC97Ff
- **API Key:** Stored at ~/.config/jobtread/.env
- **Connected:** 2026-01-24

---

## Data Mapping

### CRM Lead → JobTread

| CRM Field | JobTread Object | JobTread Field |
|-----------|-----------------|----------------|
| Client Name | Account | name |
| Phone | Contact | phone |
| Email | Contact | email |
| Address | Location | address |
| Service Type | Job | name prefix |
| Description | Job | description |

### JobTread → CRM

| JobTread | CRM |
|----------|-----|
| customerOrder status = "accepted" | Lead status = "won" |
| customerOrder status = "declined" | Lead status = "lost" |

---

## Workflow: Lead → JobTread

### When Lead Status = "Won"

1. **Create Account (Customer)**
   ```
   POST to createAccount
   - name: Lead client name
   - type: customer
   - organizationId: 22NiF3LC97Ff
   ```

2. **Create Location**
   ```
   POST to createLocation
   - accountId: (from step 1)
   - name: "Primary"
   - address: Lead address
   ```

3. **Create Job**
   ```
   POST to createJob
   - locationId: (from step 2)
   - name: "[Service Type] - [Client Name]"
   - description: Lead description + notes
   ```

4. **Update CRM Lead**
   - Store jobtread_account_id
   - Store jobtread_job_id
   - Mark as synced

---

## Workflow: Proposal Tracking

### Sync Proposal Status

Check JobTread documents for status changes:
- `pending` → Lead in follow-up sequence
- `accepted` → Lead won, cancel follow-ups
- `declined` → Lead lost, log reason

### Estimate Pipeline Metrics

Track from CRM data:
- Date of site visit (status = "measured")
- Date estimate created (manually logged or via JobTread)
- Date proposal sent (document createdAt)
- Days to estimate = proposal date - site visit date

---

## Commands Luna Understands

**Sync to JobTread:**
"Create [Client Name] in JobTread"
→ Creates account + location + job

**Check proposal status:**
"What's the status on [Client Name]'s proposal?"
→ Checks JobTread document status

**Pull JobTread data:**
"Show recent jobs from JobTread"
"How many pending proposals?"

---

## API Quick Reference

### Create Customer + Location + Job (Full Flow)
```bash
source ~/.config/jobtread/.env

# Step 1: Create Account
curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "'$JOBTREAD_API_KEY'", "notify": false},
      "createAccount": {
        "$": {
          "organizationId": "22NiF3LC97Ff",
          "name": "CLIENT_NAME",
          "type": "customer"
        }
      },
      "createdAccount": {"id": {}, "name": {}}
    }
  }'

# Step 2: Create Location (use account ID from step 1)
curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "'$JOBTREAD_API_KEY'", "notify": false},
      "createLocation": {
        "$": {
          "accountId": "ACCOUNT_ID",
          "name": "Primary",
          "address": "123 Ocean Dr, Marathon, FL 33050"
        }
      },
      "createdLocation": {"id": {}, "address": {}}
    }
  }'

# Step 3: Create Job (use location ID from step 2)
curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "'$JOBTREAD_API_KEY'", "notify": false},
      "createJob": {
        "$": {
          "locationId": "LOCATION_ID",
          "name": "Spalling Repair - CLIENT_NAME",
          "description": "Project description here"
        }
      },
      "createdJob": {"id": {}, "name": {}, "number": {}}
    }
  }'
```

### Check Pending Proposals
```bash
source ~/.config/jobtread/.env

curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "'$JOBTREAD_API_KEY'"},
      "organization": {
        "$": {"id": "22NiF3LC97Ff"},
        "documents": {
          "$": {"where": {"and": [["type", "=", "customerOrder"], ["status", "=", "pending"]]}, "size": 20},
          "nodes": {"id": {}, "name": {}, "createdAt": {}, "status": {}}
        }
      }
    }
  }'
```

---

*Integration configured: January 24, 2026*
