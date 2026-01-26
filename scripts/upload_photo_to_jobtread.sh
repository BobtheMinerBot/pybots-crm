#!/bin/bash
# Upload photo to JobTread job
# Usage: ./upload_photo_to_jobtread.sh <local_file_path> <job_id> <file_name>

set -e

LOCAL_FILE="$1"
JOB_ID="$2"
FILE_NAME="${3:-$(basename "$LOCAL_FILE")}"

# Load JobTread API key
source ~/.config/jobtread/.env

if [ -z "$LOCAL_FILE" ] || [ -z "$JOB_ID" ]; then
    echo "Usage: $0 <local_file_path> <job_id> [file_name]"
    exit 1
fi

if [ ! -f "$LOCAL_FILE" ]; then
    echo "Error: File not found: $LOCAL_FILE"
    exit 1
fi

echo "=== Step 1: Uploading to temporary host ==="
# Upload to litterbox for 24h hosting
TEMP_URL=$(curl -s -F "reqtype=fileupload" -F "time=24h" -F "fileToUpload=@$LOCAL_FILE" https://litterbox.catbox.moe/resources/internals/api.php)

if [ -z "$TEMP_URL" ] || [[ "$TEMP_URL" != http* ]]; then
    echo "Error: Failed to upload to temporary host"
    exit 1
fi

echo "Temporary URL: $TEMP_URL"

echo ""
echo "=== Step 2: Creating upload request in JobTread ==="
# Create upload request with the URL - JobTread will download it
UPLOAD_RESULT=$(curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "'$JOBTREAD_API_KEY'"},
      "createUploadRequest": {
        "$": {
          "organizationId": "22NiF3LC97Ff",
          "url": "'"$TEMP_URL"'"
        }
      },
      "createdUploadRequest": {
        "id": {}
      }
    }
  }')

echo "Upload request result: $UPLOAD_RESULT"

# Extract upload request ID
UPLOAD_ID=$(echo "$UPLOAD_RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('createdUploadRequest', {}).get('id', ''))" 2>/dev/null || echo "")

if [ -z "$UPLOAD_ID" ]; then
    echo "Error: Failed to create upload request"
    echo "Response: $UPLOAD_RESULT"
    exit 1
fi

echo "Upload Request ID: $UPLOAD_ID"

echo ""
echo "=== Step 3: Creating file record attached to job ==="
# Create file attached to job
FILE_RESULT=$(curl -s 'https://api.jobtread.com/pave' \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "$": {"grantKey": "'$JOBTREAD_API_KEY'", "notify": false},
      "createFile": {
        "$": {
          "targetId": "'$JOB_ID'",
          "targetType": "job",
          "name": "'"$FILE_NAME"'",
          "uploadRequestId": "'"$UPLOAD_ID"'"
        }
      },
      "createdFile": {
        "id": {},
        "name": {}
      }
    }
  }')

echo "File creation result: $FILE_RESULT"

echo ""
echo "✅ Photo uploaded to JobTread job $JOB_ID"
