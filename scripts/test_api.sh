#!/bin/bash

# Test script to validate API endpoint alignment
# This script tests both legacy and new JSON formats

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../.env"

echo "Testing Log Ingestion API endpoints..."
echo "API URL: $INGESTION_API_URL"
echo ""

# Test 1: Legacy format ({"log": "message"})
echo "Test 1: Legacy format"
legacy_response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"log": "This is a test log message from legacy format"}' \
  "$INGESTION_API_URL")
echo "Legacy format response: $legacy_response"
echo ""

# Test 2: New structured format
echo "Test 2: New structured format"
structured_response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "message": "This is a test log message from structured format",
    "level": "info",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "source": "test_script"
  }' \
  "$INGESTION_API_URL")
echo "Structured format response: $structured_response"
echo ""

# Test 3: Error level log
echo "Test 3: Error level log"
error_response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{
    "message": "This is an error message for testing",
    "level": "error",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "source": "test_script"
  }' \
  "$INGESTION_API_URL")
echo "Error level response: $error_response"
echo ""

# Test 4: Invalid format (should fail)
echo "Test 4: Invalid format (should fail)"
invalid_response=$(curl -s -X POST -H "Content-Type: application/json" \
  -d '{"invalid": "format"}' \
  "$INGESTION_API_URL")
echo "Invalid format response: $invalid_response"
echo ""

echo "API endpoint testing completed!"
