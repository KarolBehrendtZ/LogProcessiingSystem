package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
	"log-processing-system/services/log-ingestion/models"
	"log-processing-system/services/log-ingestion/database"
	"log-processing-system/services/log-ingestion/logger"
)

// Mock database for testing
type mockDB struct {
	logs      []models.Log
	connected bool
	shouldErr bool
}

func (m *mockDB) StoreLog(log models.Log) error {
	if m.shouldErr {
		return &testError{"database error"}
	}
	m.logs = append(m.logs, log)
	return nil
}

func (m *mockDB) Ping() error {
	if !m.connected {
		return &testError{"database not connected"}
	}
	return nil
}

func (m *mockDB) Reset() {
	m.logs = []models.Log{}
	m.connected = true
	m.shouldErr = false
}

// Test error type
type testError struct {
	message string
}

func (e *testError) Error() string {
	return e.message
}

// Setup test environment
func setupTest() (*mockDB, func()) {
	// Save original database functions
	originalStoreLog := database.StoreLog
	originalPing := database.Ping
	
	// Create mock
	mockDB := &mockDB{
		logs:      []models.Log{},
		connected: true,
		shouldErr: false,
	}
	
	// Replace database functions
	database.StoreLog = mockDB.StoreLog
	database.Ping = mockDB.Ping
	
	// Return cleanup function
	cleanup := func() {
		database.StoreLog = originalStoreLog
		database.Ping = originalPing
	}
	
	return mockDB, cleanup
}

func TestHandleLogIngestion_StructuredFormat(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Prepare request body with structured format
	logData := map[string]interface{}{
		"message":   "Test log message",
		"level":     "info",
		"source":    "test-service",
		"timestamp": time.Now().Format(time.RFC3339),
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	// Add request ID to context
	ctx := logger.WithRequestID(req.Context(), "test-request-123")
	req = req.WithContext(ctx)
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response
	if rr.Code != http.StatusAccepted {
		t.Errorf("Expected status code 202, got %d", rr.Code)
	}
	
	// Check response body
	var response map[string]string
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse response JSON: %v", err)
	}
	
	if response["status"] != "accepted" {
		t.Errorf("Expected status 'accepted', got %s", response["status"])
	}
	
	if response["request_id"] != "test-request-123" {
		t.Errorf("Expected request_id 'test-request-123', got %s", response["request_id"])
	}
	
	// Check that log was stored
	if len(mockDB.logs) != 1 {
		t.Errorf("Expected 1 log to be stored, got %d", len(mockDB.logs))
	}
	
	storedLog := mockDB.logs[0]
	if storedLog.Message != "Test log message" {
		t.Errorf("Expected message 'Test log message', got %s", storedLog.Message)
	}
	if storedLog.Level != "info" {
		t.Errorf("Expected level 'info', got %s", storedLog.Level)
	}
}

func TestHandleLogIngestion_LegacyFormat(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Prepare request body with legacy format
	logData := map[string]interface{}{
		"log": "Legacy log message",
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response
	if rr.Code != http.StatusAccepted {
		t.Errorf("Expected status code 202, got %d", rr.Code)
	}
	
	// Check that log was stored with correct defaults
	if len(mockDB.logs) != 1 {
		t.Errorf("Expected 1 log to be stored, got %d", len(mockDB.logs))
	}
	
	storedLog := mockDB.logs[0]
	if storedLog.Message != "Legacy log message" {
		t.Errorf("Expected message 'Legacy log message', got %s", storedLog.Message)
	}
	if storedLog.Level != "info" {
		t.Errorf("Expected default level 'info', got %s", storedLog.Level)
	}
	if storedLog.Source != "legacy_api" {
		t.Errorf("Expected source 'legacy_api', got %s", storedLog.Source)
	}
}

func TestHandleLogIngestion_InvalidJSON(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Send invalid JSON
	req := httptest.NewRequest("POST", "/logs", strings.NewReader("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response
	if rr.Code != http.StatusBadRequest {
		t.Errorf("Expected status code 400, got %d", rr.Code)
	}
	
	// Check that no log was stored
	if len(mockDB.logs) != 0 {
		t.Errorf("Expected 0 logs to be stored, got %d", len(mockDB.logs))
	}
}

func TestHandleLogIngestion_MissingFields(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Send JSON without required fields
	logData := map[string]interface{}{
		"timestamp": time.Now().Format(time.RFC3339),
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response
	if rr.Code != http.StatusBadRequest {
		t.Errorf("Expected status code 400, got %d", rr.Code)
	}
	
	responseBody := rr.Body.String()
	if !strings.Contains(responseBody, "Missing required fields") {
		t.Errorf("Expected error message about missing fields, got %s", responseBody)
	}
}

func TestHandleLogIngestion_ValidationError(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Send log with invalid data that will fail validation
	logData := map[string]interface{}{
		"message": "", // Empty message should fail validation
		"level":   "info",
		"source":  "test-service",
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response (assuming empty message fails validation)
	if rr.Code != http.StatusBadRequest {
		t.Errorf("Expected status code 400, got %d", rr.Code)
	}
}

func TestHandleLogIngestion_DatabaseError(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Set mock to return error
	mockDB.shouldErr = true
	
	logData := map[string]interface{}{
		"message": "Test message",
		"level":   "info",
		"source":  "test-service",
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response
	if rr.Code != http.StatusInternalServerError {
		t.Errorf("Expected status code 500, got %d", rr.Code)
	}
	
	responseBody := rr.Body.String()
	if !strings.Contains(responseBody, "Failed to store log entry") {
		t.Errorf("Expected error message about storage failure, got %s", responseBody)
	}
}

func TestHandleHealthCheck_Healthy(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	req := httptest.NewRequest("GET", "/health", nil)
	rr := httptest.NewRecorder()
	
	HandleHealthCheck(rr, req)
	
	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status code 200, got %d", rr.Code)
	}
	
	// Check response body
	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse response JSON: %v", err)
	}
	
	if response["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got %s", response["status"])
	}
	
	if response["service"] != "log-ingestion" {
		t.Errorf("Expected service 'log-ingestion', got %s", response["service"])
	}
}

func TestHandleHealthCheck_Unhealthy(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Set database as disconnected
	mockDB.connected = false
	
	req := httptest.NewRequest("GET", "/health", nil)
	rr := httptest.NewRecorder()
	
	HandleHealthCheck(rr, req)
	
	// Check response
	if rr.Code != http.StatusServiceUnavailable {
		t.Errorf("Expected status code 503, got %d", rr.Code)
	}
	
	// Check response body
	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Fatalf("Failed to parse response JSON: %v", err)
	}
	
	if response["status"] != "unhealthy" {
		t.Errorf("Expected status 'unhealthy', got %s", response["status"])
	}
	
	if response["error"] == nil {
		t.Errorf("Expected error field to be present")
	}
}

func TestHandleLogIngestion_WithContext(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	logData := map[string]interface{}{
		"message": "Test with context",
		"level":   "info",
		"source":  "test-service",
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	// Add context values
	ctx := context.Background()
	ctx = logger.WithRequestID(ctx, "req-123")
	ctx = logger.WithUserID(ctx, "user-456")
	ctx = logger.WithTraceID(ctx, "trace-789")
	req = req.WithContext(ctx)
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Check response
	if rr.Code != http.StatusAccepted {
		t.Errorf("Expected status code 202, got %d", rr.Code)
	}
	
	// Verify context values are used in logging
	// This would be verified by checking log output in a real scenario
}

func TestHandleLogIngestion_ContentTypes(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	logData := map[string]interface{}{
		"message": "Test message",
		"level":   "info",
		"source":  "test-service",
	}
	
	jsonData, _ := json.Marshal(logData)
	
	testCases := []struct {
		contentType string
		expectCode  int
	}{
		{"application/json", http.StatusAccepted},
		{"application/json; charset=utf-8", http.StatusAccepted},
		{"text/plain", http.StatusAccepted}, // Should still work
		{"", http.StatusAccepted},           // Should still work
	}
	
	for _, tc := range testCases {
		t.Run(tc.contentType, func(t *testing.T) {
			mockDB.Reset()
			
			req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
			if tc.contentType != "" {
				req.Header.Set("Content-Type", tc.contentType)
			}
			
			rr := httptest.NewRecorder()
			HandleLogIngestion(rr, req)
			
			if rr.Code != tc.expectCode {
				t.Errorf("Expected status code %d, got %d", tc.expectCode, rr.Code)
			}
		})
	}
}

func TestHandleLogIngestion_LargePayload(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Create a large message
	largeMessage := strings.Repeat("A", 10000)
	
	logData := map[string]interface{}{
		"message": largeMessage,
		"level":   "info",
		"source":  "test-service",
	}
	
	jsonData, _ := json.Marshal(logData)
	req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	
	rr := httptest.NewRecorder()
	
	HandleLogIngestion(rr, req)
	
	// Should handle large payloads
	if rr.Code != http.StatusAccepted {
		t.Errorf("Expected status code 202 for large payload, got %d", rr.Code)
	}
	
	// Verify the large message was stored
	if len(mockDB.logs) != 1 {
		t.Errorf("Expected 1 log to be stored, got %d", len(mockDB.logs))
	}
	
	if len(mockDB.logs[0].Message) != len(largeMessage) {
		t.Errorf("Expected message length %d, got %d", len(largeMessage), len(mockDB.logs[0].Message))
	}
}

// Integration test for complete log processing flow
func TestLogIngestionFlow_Integration(t *testing.T) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	// Test complete flow with multiple log entries
	testLogs := []map[string]interface{}{
		{
			"message": "User login attempt",
			"level":   "info",
			"source":  "auth-service",
		},
		{
			"log": "Legacy error occurred", // Legacy format
		},
		{
			"message": "Database connection established",
			"level":   "debug",
			"source":  "db-service",
		},
	}
	
	for i, logData := range testLogs {
		jsonData, _ := json.Marshal(logData)
		req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		
		// Add request ID
		ctx := logger.WithRequestID(req.Context(), fmt.Sprintf("req-%d", i))
		req = req.WithContext(ctx)
		
		rr := httptest.NewRecorder()
		HandleLogIngestion(rr, req)
		
		if rr.Code != http.StatusAccepted {
			t.Errorf("Request %d: Expected status code 202, got %d", i, rr.Code)
		}
	}
	
	// Verify all logs were stored
	if len(mockDB.logs) != len(testLogs) {
		t.Errorf("Expected %d logs to be stored, got %d", len(testLogs), len(mockDB.logs))
	}
	
	// Verify specific log properties
	if mockDB.logs[0].Message != "User login attempt" {
		t.Errorf("First log message incorrect")
	}
	
	if mockDB.logs[1].Source != "legacy_api" {
		t.Errorf("Second log should have legacy source")
	}
	
	if mockDB.logs[2].Level != "debug" {
		t.Errorf("Third log level incorrect")
	}
}

// Benchmark tests
func BenchmarkHandleLogIngestion_StructuredFormat(b *testing.B) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	logData := map[string]interface{}{
		"message": "Benchmark test message",
		"level":   "info",
		"source":  "bench-service",
	}
	
	jsonData, _ := json.Marshal(logData)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		mockDB.Reset()
		
		req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		
		rr := httptest.NewRecorder()
		HandleLogIngestion(rr, req)
	}
}

func BenchmarkHandleLogIngestion_LegacyFormat(b *testing.B) {
	mockDB, cleanup := setupTest()
	defer cleanup()
	
	logData := map[string]interface{}{
		"log": "Benchmark legacy message",
	}
	
	jsonData, _ := json.Marshal(logData)
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		mockDB.Reset()
		
		req := httptest.NewRequest("POST", "/logs", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		
		rr := httptest.NewRecorder()
		HandleLogIngestion(rr, req)
	}
}
