package middleware

import (
	"bytes"
	"log-processing-system/services/log-ingestion/logger"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestLoggingMiddleware_Handler(t *testing.T) {
	var buffer bytes.Buffer

	// Create a logger with buffer output
	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	// Create a test handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("test response"))
	})

	// Wrap handler with middleware
	wrappedHandler := middleware.Handler(testHandler)

	// Create test request
	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("User-Agent", "test-agent")

	// Create response recorder
	rr := httptest.NewRecorder()

	// Execute request
	wrappedHandler.ServeHTTP(rr, req)

	// Check response
	if rr.Code != http.StatusOK {
		t.Errorf("Expected status code 200, got %d", rr.Code)
	}

	// Check that request ID header was added
	requestID := rr.Header().Get("X-Request-ID")
	if requestID == "" {
		t.Errorf("Expected X-Request-ID header to be set")
	}

	// Check logs
	output := buffer.String()
	if !strings.Contains(output, "HTTP request started") {
		t.Errorf("Expected log to contain 'HTTP request started', got %v", output)
	}
	if !strings.Contains(output, "HTTP request completed") {
		t.Errorf("Expected log to contain 'HTTP request completed', got %v", output)
	}
	if !strings.Contains(output, requestID) {
		t.Errorf("Expected log to contain request ID %s, got %v", requestID, output)
	}
}

func TestLoggingMiddleware_HandlerWithExistingRequestID(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.Handler(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("X-Request-ID", "existing-request-id")

	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	// Should preserve existing request ID
	if rr.Header().Get("X-Request-ID") != "existing-request-id" {
		t.Errorf("Expected to preserve existing request ID 'existing-request-id', got %s", rr.Header().Get("X-Request-ID"))
	}

	output := buffer.String()
	if !strings.Contains(output, "existing-request-id") {
		t.Errorf("Expected log to contain existing request ID, got %v", output)
	}
}

func TestLoggingMiddleware_HandlerErrorResponse(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	// Handler that returns an error
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	})

	wrappedHandler := middleware.Handler(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)
	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	if rr.Code != http.StatusInternalServerError {
		t.Errorf("Expected status code 500, got %d", rr.Code)
	}

	output := buffer.String()
	if !strings.Contains(output, "HTTP request failed with server error") {
		t.Errorf("Expected log to contain error message, got %v", output)
	}
}

func TestLoggingMiddleware_HandlerClientError(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	// Handler that returns a client error
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
	})

	wrappedHandler := middleware.Handler(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)
	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	if rr.Code != http.StatusBadRequest {
		t.Errorf("Expected status code 400, got %d", rr.Code)
	}

	output := buffer.String()
	if !strings.Contains(output, "HTTP request failed with client error") {
		t.Errorf("Expected log to contain client error message, got %v", output)
	}
}

func TestLoggingMiddleware_SlowRequest(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	// Slow handler
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(6 * time.Second) // Longer than slow request threshold
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.Handler(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)
	rr := httptest.NewRecorder()

	start := time.Now()
	wrappedHandler.ServeHTTP(rr, req)
	duration := time.Since(start)

	if duration < 5*time.Second {
		t.Skip("Test didn't take long enough to trigger slow request warning")
	}

	output := buffer.String()
	if !strings.Contains(output, "Slow HTTP request detected") {
		t.Errorf("Expected log to contain slow request warning, got %v", output)
	}
}

func TestLoggingMiddleware_HealthCheckMiddleware(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.HealthCheckMiddleware(testHandler)

	// Test health check endpoint - should skip detailed logging
	req := httptest.NewRequest("GET", "/health", nil)
	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	output := buffer.String()
	if strings.Contains(output, "HTTP request started") {
		t.Errorf("Health check should skip detailed logging, but got %v", output)
	}

	// Test regular endpoint - should log normally
	buffer.Reset()
	req = httptest.NewRequest("GET", "/api/test", nil)
	rr = httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	output = buffer.String()
	if !strings.Contains(output, "HTTP request started") {
		t.Errorf("Regular endpoint should log normally, got %v", output)
	}
}

func TestLoggingMiddleware_RecoveryMiddleware(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	// Handler that panics
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic("test panic")
	})

	wrappedHandler := middleware.RecoveryMiddleware(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)
	rr := httptest.NewRecorder()

	// Should not panic
	wrappedHandler.ServeHTTP(rr, req)

	if rr.Code != http.StatusInternalServerError {
		t.Errorf("Expected status code 500 after panic recovery, got %d", rr.Code)
	}

	output := buffer.String()
	if !strings.Contains(output, "HTTP handler panic recovered") {
		t.Errorf("Expected log to contain panic recovery message, got %v", output)
	}
	if !strings.Contains(output, "test panic") {
		t.Errorf("Expected log to contain panic message, got %v", output)
	}
}

func TestLoggingMiddleware_CORSMiddleware(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.CORSMiddleware(testHandler)

	// Test CORS preflight request
	req := httptest.NewRequest("OPTIONS", "/test", nil)
	req.Header.Set("Origin", "https://example.com")
	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	// Check CORS headers
	if rr.Header().Get("Access-Control-Allow-Origin") != "*" {
		t.Errorf("Expected CORS origin header to be '*'")
	}

	output := buffer.String()
	if !strings.Contains(output, "CORS preflight request handled") {
		t.Errorf("Expected log to contain CORS preflight message, got %v", output)
	}

	// Test regular CORS request
	buffer.Reset()
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("Origin", "https://example.com")
	rr = httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	output = buffer.String()
	if !strings.Contains(output, "CORS request received") {
		t.Errorf("Expected log to contain CORS request message, got %v", output)
	}
}

func TestLoggingMiddleware_SecurityHeadersMiddleware(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.SecurityHeadersMiddleware(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)
	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	// Check security headers
	expectedHeaders := map[string]string{
		"X-Content-Type-Options":    "nosniff",
		"X-Frame-Options":           "DENY",
		"X-XSS-Protection":          "1; mode=block",
		"Strict-Transport-Security": "max-age=31536000; includeSubDomains",
	}

	for header, expectedValue := range expectedHeaders {
		if rr.Header().Get(header) != expectedValue {
			t.Errorf("Expected header %s to be %s, got %s", header, expectedValue, rr.Header().Get(header))
		}
	}

	// Test request with empty User-Agent
	buffer.Reset()
	req = httptest.NewRequest("GET", "/test", nil)
	req.Header.Set("User-Agent", "")
	rr = httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	output := buffer.String()
	if !strings.Contains(output, "Request with empty User-Agent detected") {
		t.Errorf("Expected log to contain empty User-Agent warning, got %v", output)
	}
}

func TestLoggingMiddleware_RateLimitMiddleware(t *testing.T) {
	var buffer bytes.Buffer

	config := logger.Config{
		Level:     "DEBUG",
		Format:    "JSON",
		Service:   "test-service",
		Component: "test-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&buffer)

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.RateLimitMiddleware(testHandler)

	// Make multiple requests to trigger rate limiting
	req := httptest.NewRequest("GET", "/test", nil)
	req.RemoteAddr = "192.168.1.1:12345"

	// Make 51 requests to trigger high rate warning
	for i := 0; i < 51; i++ {
		rr := httptest.NewRecorder()
		wrappedHandler.ServeHTTP(rr, req)

		if i < 50 && rr.Code != http.StatusOK {
			t.Errorf("Request %d should succeed, got status %d", i, rr.Code)
		}
	}

	output := buffer.String()
	if !strings.Contains(output, "High request rate detected") {
		t.Errorf("Expected log to contain high request rate warning, got %v", output)
	}

	// Make many more requests to trigger rate limit
	for i := 51; i < 105; i++ {
		rr := httptest.NewRecorder()
		wrappedHandler.ServeHTTP(rr, req)
	}

	// The last request should be rate limited
	rr := httptest.NewRecorder()
	wrappedHandler.ServeHTTP(rr, req)

	if rr.Code != http.StatusTooManyRequests {
		t.Errorf("Expected rate limit status 429, got %d", rr.Code)
	}

	output = buffer.String()
	if !strings.Contains(output, "Rate limit exceeded") {
		t.Errorf("Expected log to contain rate limit message, got %v", output)
	}
}

func TestResponseWriter(t *testing.T) {
	rr := httptest.NewRecorder()
	wrapped := newResponseWriter(rr)

	// Test default status code
	if wrapped.statusCode != http.StatusOK {
		t.Errorf("Expected default status code 200, got %d", wrapped.statusCode)
	}

	// Test WriteHeader
	wrapped.WriteHeader(http.StatusCreated)
	if wrapped.statusCode != http.StatusCreated {
		t.Errorf("Expected status code 201, got %d", wrapped.statusCode)
	}

	// Test Write
	data := []byte("test response")
	n, err := wrapped.Write(data)
	if err != nil {
		t.Errorf("Unexpected error writing data: %v", err)
	}
	if n != len(data) {
		t.Errorf("Expected to write %d bytes, wrote %d", len(data), n)
	}
	if wrapped.written != int64(len(data)) {
		t.Errorf("Expected written count %d, got %d", len(data), wrapped.written)
	}
}

// Benchmark tests
func BenchmarkLoggingMiddleware_Handler(b *testing.B) {
	config := logger.Config{
		Level:     "INFO",
		Format:    "JSON",
		Service:   "bench-service",
		Component: "bench-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&bytes.Buffer{}) // Discard output

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.Handler(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		rr := httptest.NewRecorder()
		wrappedHandler.ServeHTTP(rr, req)
	}
}

func BenchmarkLoggingMiddleware_Recovery(b *testing.B) {
	config := logger.Config{
		Level:     "INFO",
		Format:    "JSON",
		Service:   "bench-service",
		Component: "bench-component",
	}
	testLogger := logger.New(config)
	testLogger.SetOutput(&bytes.Buffer{}) // Discard output

	middleware := NewLoggingMiddleware(testLogger)

	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	wrappedHandler := middleware.RecoveryMiddleware(testHandler)

	req := httptest.NewRequest("GET", "/test", nil)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		rr := httptest.NewRecorder()
		wrappedHandler.ServeHTTP(rr, req)
	}
}
