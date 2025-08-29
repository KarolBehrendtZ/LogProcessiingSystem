#!/bin/bash

# This script parses log files and sends the parsed logs to the log ingestion API.

LOG_FILE_PATH="$1"
# Load global environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

if [[ -z "$LOG_FILE_PATH" ]]; then
  echo "Usage: $0 <path_to_log_file>"
  exit 1
fi

if [[ ! -f "$LOG_FILE_PATH" ]]; then
  echo "Log file not found: $LOG_FILE_PATH"
  exit 1
fi

while IFS= read -r line; do
  # Parse log line and extract structured data
  # Default parsing - you can customize this based on your log format
  
  # Try to extract log level from the line (common patterns)
  level="info"
  if [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"error"* ]]; then
    level="error"
  elif [[ "$line" == *"WARN"* ]] || [[ "$line" == *"warn"* ]]; then
    level="warn"
  elif [[ "$line" == *"DEBUG"* ]] || [[ "$line" == *"debug"* ]]; then
    level="debug"
  elif [[ "$line" == *"FATAL"* ]] || [[ "$line" == *"fatal"* ]]; then
    level="fatal"
  fi
  
  # Get current timestamp in ISO8601 format
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  # Create structured JSON payload
  json_payload=$(cat <<EOF
{
  "message": "$line",
  "level": "$level",
  "timestamp": "$timestamp",
  "source": "parse_logs_script"
}
EOF
)
  
  # Sending the structured log entry to the ingestion API
  curl -X POST -H "Content-Type: application/json" -d "$json_payload" "$INGESTION_API_URL"
done < "$LOG_FILE_PATH"