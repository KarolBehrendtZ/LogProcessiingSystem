package logger

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"strings"
	"testing"
	"time"
)

func TestLogLevel_String(t *testing.T) {
	tests := []struct {
		level    LogLevel
		expected string
	}{
		{DEBUG, "DEBUG"},
		{INFO, "INFO"},
		{WARN, "WARN"},
		{ERROR, "ERROR"},
		{FATAL, "FATAL"},
		{LogLevel(999), "UNKNOWN"},
	}

	for _, test := range tests {
		t.Run(test.expected, func(t *testing.T) {
			if got := test.level.String(); got != test.expected {
				t.Errorf("LogLevel.String() = %v, want %v", got, test.expected)
			}
		})
	}
}

func TestParseLogLevel(t *testing.T) {
	tests := []struct {
		input    string
		expected LogLevel
	}{
		{"DEBUG", DEBUG},
		{"INFO", INFO},
		{"WARN", WARN},
		{"WARNING", WARN},
		{"ERROR", ERROR},
		{"FATAL", FATAL},
		{"INVALID", INFO}, // default case
		{"", INFO},        // default case
	}

	for _, test := range tests {
		t.Run(test.input, func(t *testing.T) {
			if got := parseLogLevel(test.input); got != test.expected {
				t.Errorf("parseLogLevel(%v) = %v, want %v", test.input, got, test.expected)
			}
		})
	}
}

func TestParseLogFormat(t *testing.T) {
	tests := []struct {
		input    string
		expected LogFormat
	}{
		{"JSON", JSON},
		{"TEXT", TEXT},
		{"INVALID", JSON}, // default case
		{"", JSON},        // default case
	}

	for _, test := range tests {
		t.Run(test.input, func(t *testing.T) {
			if got := parseLogFormat(test.input); got != test.expected {
				t.Errorf("parseLogFormat(%v) = %v, want %v", test.input, got, test.expected)
			}
		})
	}
}

func TestNew(t *testing.T) {
	config := Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
		Output:    "stdout",
		Fields: map[string]interface{}{
			"version": "1.0.0",
		},
	}

	logger := New(config)

	if logger.level != DEBUG {
		t.Errorf("Expected level DEBUG, got %v", logger.level)
	}
	if logger.service != "test-service" {
		t.Errorf("Expected service 'test-service', got %v", logger.service)
	}
	if logger.component != "test-component" {
		t.Errorf("Expected component 'test-component', got %v", logger.component)
	}
	if logger.format != JSON {
		t.Errorf("Expected format JSON, got %v", logger.format)
	}
	if logger.fields["version"] != "1.0.0" {
		t.Errorf("Expected version field '1.0.0', got %v", logger.fields["version"])
	}
}

func TestNewFromEnv(t *testing.T) {
	// Set environment variables
	os.Setenv("LOG_LEVEL", "ERROR")
	os.Setenv("LOG_FORMAT", "TEXT")
	os.Setenv("LOG_OUTPUT", "stdout")
	defer func() {
		os.Unsetenv("LOG_LEVEL")
		os.Unsetenv("LOG_FORMAT")
		os.Unsetenv("LOG_OUTPUT")
	}()

	logger := NewFromEnv("test-service", "test-component")

	if logger.level != ERROR {
		t.Errorf("Expected level ERROR, got %v", logger.level)
	}
	if logger.format != TEXT {
		t.Errorf("Expected format TEXT, got %v", logger.format)
	}
}

func TestNewFromEnvDefaults(t *testing.T) {
	// Clear environment variables
	os.Unsetenv("LOG_LEVEL")
	os.Unsetenv("LOG_FORMAT")
	os.Unsetenv("LOG_OUTPUT")

	logger := NewFromEnv("test-service", "test-component")

	if logger.level != INFO {
		t.Errorf("Expected default level INFO, got %v", logger.level)
	}
	if logger.format != JSON {
		t.Errorf("Expected default format JSON, got %v", logger.format)
	}
}

func TestLogger_WithFields(t *testing.T) {
	logger := NewFromEnv("test-service", "test-component")

	fields := map[string]interface{}{
		"user_id": "123",
		"action":  "test",
	}

	newLogger := logger.WithFields(fields)

	if newLogger.fields["user_id"] != "123" {
		t.Errorf("Expected user_id '123', got %v", newLogger.fields["user_id"])
	}
	if newLogger.fields["action"] != "test" {
		t.Errorf("Expected action 'test', got %v", newLogger.fields["action"])
	}

	// Original logger should be unchanged
	if len(logger.fields) != 0 {
		t.Errorf("Original logger fields should be empty, got %v", logger.fields)
	}
}

func TestLogger_WithField(t *testing.T) {
	logger := NewFromEnv("test-service", "test-component")

	newLogger := logger.WithField("user_id", "123")

	if newLogger.fields["user_id"] != "123" {
		t.Errorf("Expected user_id '123', got %v", newLogger.fields["user_id"])
	}
}

func TestLogger_WithError(t *testing.T) {
	logger := NewFromEnv("test-service", "test-component")

	err := &testError{"test error"}
	newLogger := logger.WithError(err)

	if newLogger.fields["error"] != "test error" {
		t.Errorf("Expected error 'test error', got %v", newLogger.fields["error"])
	}

	// Test with nil error
	nilLogger := logger.WithError(nil)
	if _, exists := nilLogger.fields["error"]; exists {
		t.Errorf("Expected no error field for nil error")
	}
}

func TestLogger_WithDuration(t *testing.T) {
	logger := NewFromEnv("test-service", "test-component")

	duration := 100 * time.Millisecond
	newLogger := logger.WithDuration(duration)

	if newLogger.fields["duration"] != duration.String() {
		t.Errorf("Expected duration '%v', got %v", duration.String(), newLogger.fields["duration"])
	}
}

func TestLogger_WithComponent(t *testing.T) {
	logger := NewFromEnv("test-service", "test-component")

	newLogger := logger.WithComponent("new-component")

	if newLogger.component != "new-component" {
		t.Errorf("Expected component 'new-component', got %v", newLogger.component)
	}

	// Original logger should be unchanged
	if logger.component != "test-component" {
		t.Errorf("Original logger component should be 'test-component', got %v", logger.component)
	}
}

func TestLogger_JSONOutput(t *testing.T) {
	var buffer bytes.Buffer

	config := Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}

	logger := New(config)
	logger.output = &buffer

	logger.Info("test message")

	output := buffer.String()

	// Parse JSON to verify structure
	var entry LogEntry
	if err := json.Unmarshal([]byte(strings.TrimSpace(output)), &entry); err != nil {
		t.Fatalf("Failed to parse JSON output: %v", err)
	}

	if entry.Level != "INFO" {
		t.Errorf("Expected level 'INFO', got %v", entry.Level)
	}
	if entry.Message != "test message" {
		t.Errorf("Expected message 'test message', got %v", entry.Message)
	}
	if entry.Service != "test-service" {
		t.Errorf("Expected service 'test-service', got %v", entry.Service)
	}
	if entry.Component != "test-component" {
		t.Errorf("Expected component 'test-component', got %v", entry.Component)
	}
}

func TestLogger_TextOutput(t *testing.T) {
	var buffer bytes.Buffer

	config := Config{
		Level:     "DEBUG",
		Format:    "TEXT",
		Service:   "test-service",
		Component: "test-component",
	}

	logger := New(config)
	logger.output = &buffer

	logger.Info("test message")

	output := buffer.String()

	if !strings.Contains(output, "INFO") {
		t.Errorf("Expected output to contain 'INFO', got %v", output)
	}
	if !strings.Contains(output, "test message") {
		t.Errorf("Expected output to contain 'test message', got %v", output)
	}
	if !strings.Contains(output, "test-service") {
		t.Errorf("Expected output to contain 'test-service', got %v", output)
	}
	if !strings.Contains(output, "test-component") {
		t.Errorf("Expected output to contain 'test-component', got %v", output)
	}
}

func TestLogger_LogLevels(t *testing.T) {
	var buffer bytes.Buffer

	config := Config{
		Level:     "WARN",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}

	logger := New(config)
	logger.output = &buffer

	// These should not be logged (below WARN level)
	logger.Debug("debug message")
	logger.Info("info message")

	// These should be logged (WARN level and above)
	logger.Warn("warn message")
	logger.Error("error message")

	output := buffer.String()
	lines := strings.Split(strings.TrimSpace(output), "\n")

	// Should only have 2 lines (warn and error)
	if len(lines) != 2 {
		t.Errorf("Expected 2 log lines, got %d: %v", len(lines), lines)
	}

	if !strings.Contains(output, "warn message") {
		t.Errorf("Expected output to contain 'warn message', got %v", output)
	}
	if !strings.Contains(output, "error message") {
		t.Errorf("Expected output to contain 'error message', got %v", output)
	}
}

func TestLogger_WithContext(t *testing.T) {
	var buffer bytes.Buffer

	config := Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}

	logger := New(config)
	logger.output = &buffer

	ctx := context.Background()
	ctx = WithTraceID(ctx, "trace-123")
	ctx = WithUserID(ctx, "user-456")
	ctx = WithRequestID(ctx, "request-789")

	logger.InfoContext(ctx, "test message")

	output := buffer.String()

	var entry LogEntry
	if err := json.Unmarshal([]byte(strings.TrimSpace(output)), &entry); err != nil {
		t.Fatalf("Failed to parse JSON output: %v", err)
	}

	if entry.TraceID != "trace-123" {
		t.Errorf("Expected trace_id 'trace-123', got %v", entry.TraceID)
	}
	if entry.UserID != "user-456" {
		t.Errorf("Expected user_id 'user-456', got %v", entry.UserID)
	}
	if entry.RequestID != "request-789" {
		t.Errorf("Expected request_id 'request-789', got %v", entry.RequestID)
	}
}

func TestLogger_FormattedMethods(t *testing.T) {
	var buffer bytes.Buffer

	config := Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}

	logger := New(config)
	logger.output = &buffer

	logger.Debugf("debug %s %d", "message", 123)
	logger.Infof("info %s %d", "message", 456)
	logger.Warnf("warn %s %d", "message", 789)
	logger.Errorf("error %s %d", "message", 101112)

	output := buffer.String()

	if !strings.Contains(output, "debug message 123") {
		t.Errorf("Expected output to contain 'debug message 123', got %v", output)
	}
	if !strings.Contains(output, "info message 456") {
		t.Errorf("Expected output to contain 'info message 456', got %v", output)
	}
	if !strings.Contains(output, "warn message 789") {
		t.Errorf("Expected output to contain 'warn message 789', got %v", output)
	}
	if !strings.Contains(output, "error message 101112") {
		t.Errorf("Expected output to contain 'error message 101112', got %v", output)
	}
}

func TestLogger_SpecializedMethods(t *testing.T) {
	var buffer bytes.Buffer

	config := Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}

	logger := New(config)
	logger.output = &buffer

	// Test LogHTTPRequest
	logger.LogHTTPRequest("GET", "/api/test", "Mozilla/5.0", "192.168.1.1", 200, 100*time.Millisecond)

	// Test LogDatabaseOperation
	logger.LogDatabaseOperation("SELECT", "users", 50*time.Millisecond, 10)

	// Test LogBusinessEvent
	logger.LogBusinessEvent("user_login", "user-123", map[string]interface{}{
		"method":  "oauth",
		"success": true,
	})

	output := buffer.String()

	if !strings.Contains(output, "HTTP request processed") {
		t.Errorf("Expected output to contain 'HTTP request processed', got %v", output)
	}
	if !strings.Contains(output, "Database operation completed") {
		t.Errorf("Expected output to contain 'Database operation completed', got %v", output)
	}
	if !strings.Contains(output, "Business event occurred") {
		t.Errorf("Expected output to contain 'Business event occurred', got %v", output)
	}
}

func TestContextHelpers(t *testing.T) {
	ctx := context.Background()

	// Test WithTraceID and GetTraceID
	ctx = WithTraceID(ctx, "trace-123")
	if got := GetTraceID(ctx); got != "trace-123" {
		t.Errorf("Expected trace ID 'trace-123', got %v", got)
	}

	// Test WithUserID and GetUserID
	ctx = WithUserID(ctx, "user-456")
	if got := GetUserID(ctx); got != "user-456" {
		t.Errorf("Expected user ID 'user-456', got %v", got)
	}

	// Test WithRequestID and GetRequestID
	ctx = WithRequestID(ctx, "request-789")
	if got := GetRequestID(ctx); got != "request-789" {
		t.Errorf("Expected request ID 'request-789', got %v", got)
	}

	// Test empty context
	emptyCtx := context.Background()
	if got := GetTraceID(emptyCtx); got != "" {
		t.Errorf("Expected empty trace ID, got %v", got)
	}
}

func TestDefaultLogger(t *testing.T) {
	// Initialize default logger
	InitDefault("test-service", "test-component")

	// Test that default functions work
	Debug("debug message")
	Info("info message")
	Warn("warn message")
	Error("error message")

	Debugf("debug %s", "formatted")
	Infof("info %s", "formatted")
	Warnf("warn %s", "formatted")
	Errorf("error %s", "formatted")

	// Should not panic
}

func TestGetEnv(t *testing.T) {
	// Test with existing env var
	os.Setenv("TEST_VAR", "test_value")
	defer os.Unsetenv("TEST_VAR")

	if got := getEnv("TEST_VAR", "default"); got != "test_value" {
		t.Errorf("Expected 'test_value', got %v", got)
	}

	// Test with non-existing env var
	if got := getEnv("NON_EXISTING_VAR", "default"); got != "default" {
		t.Errorf("Expected 'default', got %v", got)
	}
}

func TestGetCaller(t *testing.T) {
	file, line, function := getCaller()

	if file == "unknown" || line == 0 || function == "unknown" {
		t.Errorf("getCaller() returned unknown values: file=%s, line=%d, function=%s", file, line, function)
	}

	// Check if we got a valid filename (could be logger_test.go or other valid file)
	if file == "" {
		t.Errorf("Expected valid file name, got empty string")
	}
}

// Test helper types
type testError struct {
	message string
}

func (e *testError) Error() string {
	return e.message
}

// Benchmark tests
func BenchmarkLogger_Info(b *testing.B) {
	logger := NewFromEnv("bench-service", "bench-component")
	logger.output = &bytes.Buffer{} // Discard output

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		logger.Info("benchmark message")
	}
}

func BenchmarkLogger_InfoWithFields(b *testing.B) {
	logger := NewFromEnv("bench-service", "bench-component")
	logger.output = &bytes.Buffer{} // Discard output

	fields := map[string]interface{}{
		"user_id": "123",
		"action":  "test",
		"count":   42,
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		logger.WithFields(fields).Info("benchmark message")
	}
}

func BenchmarkLogger_JSONMarshal(b *testing.B) {
	entry := LogEntry{
		Timestamp: time.Now().UTC(),
		Level:     "INFO",
		Message:   "benchmark message",
		Service:   "bench-service",
		Component: "bench-component",
		File:      "test.go",
		Line:      42,
		Function:  "TestFunction",
		Fields: map[string]interface{}{
			"user_id": "123",
			"action":  "test",
			"count":   42,
		},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = json.Marshal(entry)
	}
}
