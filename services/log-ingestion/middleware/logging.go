package middleware

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/google/uuid"
	"log-processing-system/services/log-ingestion/logger"
)

// LoggingMiddleware wraps HTTP handlers with structured logging
type LoggingMiddleware struct {
	logger *logger.Logger
}

// NewLoggingMiddleware creates a new logging middleware
func NewLoggingMiddleware(log *logger.Logger) *LoggingMiddleware {
	return &LoggingMiddleware{
		logger: log,
	}
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
	written    int64
}

func newResponseWriter(w http.ResponseWriter) *responseWriter {
	return &responseWriter{
		ResponseWriter: w,
		statusCode:     http.StatusOK,
	}
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func (rw *responseWriter) Write(data []byte) (int, error) {
	n, err := rw.ResponseWriter.Write(data)
	rw.written += int64(n)
	return n, err
}

// Handler wraps an HTTP handler with logging
func (lm *LoggingMiddleware) Handler(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		
		// Generate request ID if not present
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}

		// Add request ID to context
		ctx := logger.WithRequestID(r.Context(), requestID)
		r = r.WithContext(ctx)

		// Add request ID to response headers
		w.Header().Set("X-Request-ID", requestID)

		// Wrap response writer
		wrapped := newResponseWriter(w)

		// Log incoming request
		lm.logger.WithFields(map[string]interface{}{
			"http_method":      r.Method,
			"http_path":        r.URL.Path,
			"http_query":       r.URL.RawQuery,
			"http_user_agent":  r.UserAgent(),
			"http_remote_addr": r.RemoteAddr,
			"http_host":        r.Host,
			"request_id":       requestID,
			"content_length":   r.ContentLength,
		}).InfoContext(ctx, "HTTP request started")

		// Process request
		next.ServeHTTP(wrapped, r)

		// Calculate duration
		duration := time.Since(start)

		// Log response
		lm.logger.WithFields(map[string]interface{}{
			"http_method":       r.Method,
			"http_path":         r.URL.Path,
			"http_status_code":  wrapped.statusCode,
			"http_remote_addr":  r.RemoteAddr,
			"request_id":        requestID,
			"duration_ms":       duration.Milliseconds(),
			"response_size":     wrapped.written,
		}).InfoContext(ctx, "HTTP request completed")

		// Log slow requests as warnings
		if duration > 5*time.Second {
			lm.logger.WithFields(map[string]interface{}{
				"http_method":      r.Method,
				"http_path":        r.URL.Path,
				"duration_ms":      duration.Milliseconds(),
				"request_id":       requestID,
			}).WarnContext(ctx, "Slow HTTP request detected")
		}

		// Log errors
		if wrapped.statusCode >= 400 {
			level := "warn"
			if wrapped.statusCode >= 500 {
				level = "error"
			}
			
			logEntry := lm.logger.WithFields(map[string]interface{}{
				"http_method":      r.Method,
				"http_path":        r.URL.Path,
				"http_status_code": wrapped.statusCode,
				"request_id":       requestID,
			})

			if level == "error" {
				logEntry.ErrorContext(ctx, "HTTP request failed with server error")
			} else {
				logEntry.WarnContext(ctx, "HTTP request failed with client error")
			}
		}
	})
}

// HealthCheckMiddleware provides basic health check logging
func (lm *LoggingMiddleware) HealthCheckMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Skip detailed logging for health checks to reduce noise
		if r.URL.Path == "/health" || r.URL.Path == "/healthz" {
			next.ServeHTTP(w, r)
			return
		}
		
		lm.Handler(next).ServeHTTP(w, r)
	})
}

// RecoveryMiddleware provides panic recovery with structured logging
func (lm *LoggingMiddleware) RecoveryMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				requestID := logger.GetRequestID(r.Context())
				
				lm.logger.WithFields(map[string]interface{}{
					"http_method":      r.Method,
					"http_path":        r.URL.Path,
					"http_remote_addr": r.RemoteAddr,
					"request_id":       requestID,
					"panic":            fmt.Sprintf("%v", err),
				}).ErrorContext(r.Context(), "HTTP handler panic recovered")

				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			}
		}()

		next.ServeHTTP(w, r)
	})
}

// CORSMiddleware adds CORS headers and logs CORS requests
func (lm *LoggingMiddleware) CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		
		if origin != "" {
			lm.logger.WithFields(map[string]interface{}{
				"http_method": r.Method,
				"http_path":   r.URL.Path,
				"origin":      origin,
				"request_id":  logger.GetRequestID(r.Context()),
			}).DebugContext(r.Context(), "CORS request received")
		}

		// Set CORS headers
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")

		// Handle preflight requests
		if r.Method == "OPTIONS" {
			lm.logger.WithFields(map[string]interface{}{
				"http_path":  r.URL.Path,
				"origin":     origin,
				"request_id": logger.GetRequestID(r.Context()),
			}).DebugContext(r.Context(), "CORS preflight request handled")
			
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// SecurityHeadersMiddleware adds security headers and logs security events
func (lm *LoggingMiddleware) SecurityHeadersMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Security headers
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("X-XSS-Protection", "1; mode=block")
		w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

		// Log suspicious requests
		userAgent := r.UserAgent()
		if userAgent == "" {
			lm.logger.WithFields(map[string]interface{}{
				"http_method":      r.Method,
				"http_path":        r.URL.Path,
				"http_remote_addr": r.RemoteAddr,
				"request_id":       logger.GetRequestID(r.Context()),
			}).WarnContext(r.Context(), "Request with empty User-Agent detected")
		}

		// Log requests with suspicious patterns
		if r.URL.Path != r.URL.EscapedPath() {
			lm.logger.WithFields(map[string]interface{}{
				"http_method":      r.Method,
				"http_path":        r.URL.Path,
				"escaped_path":     r.URL.EscapedPath(),
				"http_remote_addr": r.RemoteAddr,
				"request_id":       logger.GetRequestID(r.Context()),
			}).WarnContext(r.Context(), "Request with URL encoding detected")
		}

		next.ServeHTTP(w, r)
	})
}

// RateLimitMiddleware provides basic rate limiting with logging
func (lm *LoggingMiddleware) RateLimitMiddleware(next http.Handler) http.Handler {
	// Simple in-memory rate limiting (for demo purposes)
	// In production, use Redis or similar
	requestCounts := make(map[string]int)
	lastReset := time.Now()
	
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Reset counts every minute
		if time.Since(lastReset) > time.Minute {
			requestCounts = make(map[string]int)
			lastReset = time.Now()
		}

		clientIP := r.RemoteAddr
		requestCounts[clientIP]++

		// Simple rate limit: 100 requests per minute
		if requestCounts[clientIP] > 100 {
			lm.logger.WithFields(map[string]interface{}{
				"http_method":      r.Method,
				"http_path":        r.URL.Path,
				"http_remote_addr": r.RemoteAddr,
				"request_count":    requestCounts[clientIP],
				"request_id":       logger.GetRequestID(r.Context()),
			}).WarnContext(r.Context(), "Rate limit exceeded")

			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		// Log high request rates
		if requestCounts[clientIP] > 50 {
			lm.logger.WithFields(map[string]interface{}{
				"http_remote_addr": r.RemoteAddr,
				"request_count":    requestCounts[clientIP],
				"request_id":       logger.GetRequestID(r.Context()),
			}).InfoContext(r.Context(), "High request rate detected")
		}

		next.ServeHTTP(w, r)
	})
}
