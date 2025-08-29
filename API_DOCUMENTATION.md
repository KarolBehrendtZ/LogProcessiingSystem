# API Endpoint Documentation

## Log Ingestion API

### Base URL
```
http://localhost:8080
```

### Endpoints

#### POST /logs
#### POST /ingest

Both endpoints accept log entries for ingestion into the system.

### Request Formats

The API supports two formats for backward compatibility:

#### 1. Structured Format (Recommended)

```json
{
  "message": "Log message content",
  "level": "info|debug|warn|error|fatal",
  "timestamp": "2025-08-29T10:15:30Z",
  "source": "service_name"
}
```

**Fields:**
- `message` (required): The log message content
- `level` (optional): Log level, defaults to "info" if not provided
- `timestamp` (optional): ISO8601 timestamp, defaults to current time if not provided
- `source` (optional): Source identifier, defaults to "unknown" if not provided

**Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "message": "User authentication successful",
    "level": "info",
    "timestamp": "2025-08-29T10:15:30Z",
    "source": "auth_service"
  }' \
  http://localhost:8080/logs
```

#### 2. Legacy Format (For Backward Compatibility)

```json
{
  "log": "Raw log message"
}
```

**Fields:**
- `log` (required): Raw log message text

**Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"log": "This is a legacy format log message"}' \
  http://localhost:8080/logs
```

### Response Format

#### Success Response
```json
{
  "status": "accepted",
  "message": "Log entry stored successfully"
}
```

**HTTP Status:** `202 Accepted`

#### Error Responses

**Invalid JSON Format:**
```
HTTP Status: 400 Bad Request
Content: "Invalid JSON format"
```

**Missing Required Fields:**
```
HTTP Status: 400 Bad Request
Content: "Missing required fields: either 'message' or 'log' field required"
```

**Validation Error:**
```
HTTP Status: 400 Bad Request
Content: "Validation error message"
```

**Database Error:**
```
HTTP Status: 500 Internal Server Error
Content: "Failed to store log entry"
```

### Log Levels

Supported log levels (case-insensitive):
- `debug` - Detailed debugging information
- `info` - General information messages
- `warn` - Warning messages
- `error` - Error messages
- `fatal` - Critical error messages

### Timestamp Format

Timestamps should be in ISO8601 format:
```
YYYY-MM-DDTHH:MM:SSZ
```

Example: `2025-08-29T10:15:30Z`

### Testing the API

Use the provided test script to validate API functionality:
```bash
./scripts/test_api.sh
```

### Integration with Parse Script

The `parse_logs.sh` script automatically formats log entries in the structured format:

```bash
./scripts/parse_logs.sh /path/to/logfile.log
```

This script will:
1. Read each line from the log file
2. Detect log level based on common patterns
3. Add timestamp and source information
4. Send structured JSON to the ingestion API

### Database Schema

Log entries are stored with the following structure:
```sql
CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    source VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```
