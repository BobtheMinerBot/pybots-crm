#!/bin/bash
# Save a photo to the job's folder
# Usage: ./save_job_photo.sh <job_number> <client_name> <source_path> <photo_name>

JOB_NUM="$1"
CLIENT="$2"
SOURCE="$3"
PHOTO_NAME="$4"

DEST_DIR="/Users/jb/clawd/projects/isla-crm/photos/${JOB_NUM}_${CLIENT}"
mkdir -p "$DEST_DIR"

if [ -f "$SOURCE" ]; then
    cp "$SOURCE" "$DEST_DIR/$PHOTO_NAME"
    echo "✅ Saved: $DEST_DIR/$PHOTO_NAME"
else
    echo "❌ Source file not found: $SOURCE"
    exit 1
fi
