package logger

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

// LogLevel represents the logging level
type LogLevel int

const (
	DEBUG LogLevel = iota
	INFO
	WARN
	ERROR
	FATAL
)

// String returns the string representation of the log level
func (l LogLevel) String() string {
	switch l {
	case DEBUG:
		return "DEBUG"
	case INFO:
		return "INFO"
	case WARN:
		return "WARN"
	case ERROR:
		return "ERROR"
	case FATAL:
		return "FATAL"
	default:
		return "UNKNOWN"
	}
}

// LogEntry represents a structured log entry
type LogEntry struct {
	Timestamp time.Time              `json:"timestamp"`
	Level     string                 `json:"level"`
	Message   string                 `json:"message"`
	Service   string                 `json:"service"`
	Component string                 `json:"component"`
	TraceID   string                 `json:"trace_id,omitempty"`
	UserID    string                 `json:"user_id,omitempty"`
	RequestID string                 `json:"request_id,omitempty"`
	File      string                 `json:"file"`
	Line      int                    `json:"line"`
	Function  string                 `json:"function"`
	Duration  *time.Duration         `json:"duration,omitempty"`
	Error     string                 `json:"error,omitempty"`
	Fields    map[string]interface{} `json:"fields,omitempty"`
	Tags      []string               `json:"tags,omitempty"`
}

// Logger represents the structured logger
type Logger struct {
	level     LogLevel
	service   string
	component string
	output    io.Writer
	format    LogFormat
	fields    map[string]interface{}
}

// LogFormat represents the output format
type LogFormat int

const (
	JSON LogFormat = iota
	TEXT
)

// Config represents logger configuration
type Config struct {
	Level     string                 `json:"level"`
	Format    string                 `json:"format"`
	Service   string                 `json:"service"`
	Component string                 `json:"component"`
	Output    string                 `json:"output"`
	Fields    map[string]interface{} `json:"fields"`
}

// contextKey is a custom type for context keys
type contextKey string

const (
	traceIDKey   contextKey = "trace_id"
	userIDKey    contextKey = "user_id"
	requestIDKey contextKey = "request_id"
)

// New creates a new structured logger
func New(config Config) *Logger {
	logger := &Logger{
		level:     parseLogLevel(config.Level),
		service:   config.Service,
		component: config.Component,
		format:    parseLogFormat(config.Format),
		fields:    make(map[string]interface{}),
		output:    os.Stdout,
	}

	// Set output destination
	if config.Output != "" && config.Output != "stdout" {
		if file, err := os.OpenFile(config.Output, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666); err == nil {
			logger.output = file
		}
	}

	// Add default fields
	if config.Fields != nil {
		for k, v := range config.Fields {
			logger.fields[k] = v
		}
	}

	return logger
}

// NewFromEnv creates a logger from environment variables
func NewFromEnv(service, component string) *Logger {
	config := Config{
		Level:     getEnv("LOG_LEVEL", "INFO"),
		Format:    getEnv("LOG_FORMAT", "JSON"),
		Service:   service,
		Component: component,
		Output:    getEnv("LOG_OUTPUT", "stdout"),
	}

	return New(config)
}

// WithFields adds fields to the logger context
func (l *Logger) WithFields(fields map[string]interface{}) *Logger {
	newLogger := &Logger{
		level:     l.level,
		service:   l.service,
		component: l.component,
		output:    l.output,
		format:    l.format,
		fields:    make(map[string]interface{}),
	}

	// Copy existing fields
	for k, v := range l.fields {
		newLogger.fields[k] = v
	}

	// Add new fields
	for k, v := range fields {
		newLogger.fields[k] = v
	}

	return newLogger
}

// WithField adds a single field to the logger context
func (l *Logger) WithField(key string, value interface{}) *Logger {
	return l.WithFields(map[string]interface{}{key: value})
}

// WithError adds an error to the logger context
func (l *Logger) WithError(err error) *Logger {
	if err != nil {
		return l.WithField("error", err.Error())
	}
	return l
}

// WithDuration adds duration to the logger context
func (l *Logger) WithDuration(duration time.Duration) *Logger {
	return l.WithField("duration", duration.String())
}

// WithComponent sets the component for this log entry
func (l *Logger) WithComponent(component string) *Logger {
	newLogger := *l
	newLogger.component = component
	return &newLogger
}

// SetOutput sets the output destination for the logger
func (l *Logger) SetOutput(w io.Writer) {
	l.output = w
}

// Debug logs a debug message
func (l *Logger) Debug(message string) {
	l.log(DEBUG, message, nil)
}

// Debugf logs a formatted debug message
func (l *Logger) Debugf(format string, args ...interface{}) {
	l.log(DEBUG, fmt.Sprintf(format, args...), nil)
}

// DebugContext logs a debug message with context
func (l *Logger) DebugContext(ctx context.Context, message string) {
	l.logWithContext(ctx, DEBUG, message, nil)
}

// Info logs an info message
func (l *Logger) Info(message string) {
	l.log(INFO, message, nil)
}

// Infof logs a formatted info message
func (l *Logger) Infof(format string, args ...interface{}) {
	l.log(INFO, fmt.Sprintf(format, args...), nil)
}

// InfoContext logs an info message with context
func (l *Logger) InfoContext(ctx context.Context, message string) {
	l.logWithContext(ctx, INFO, message, nil)
}

// Warn logs a warning message
func (l *Logger) Warn(message string) {
	l.log(WARN, message, nil)
}

// Warnf logs a formatted warning message
func (l *Logger) Warnf(format string, args ...interface{}) {
	l.log(WARN, fmt.Sprintf(format, args...), nil)
}

// WarnContext logs a warning message with context
func (l *Logger) WarnContext(ctx context.Context, message string) {
	l.logWithContext(ctx, WARN, message, nil)
}

// Error logs an error message
func (l *Logger) Error(message string) {
	l.log(ERROR, message, nil)
}

// Errorf logs a formatted error message
func (l *Logger) Errorf(format string, args ...interface{}) {
	l.log(ERROR, fmt.Sprintf(format, args...), nil)
}

// ErrorContext logs an error message with context
func (l *Logger) ErrorContext(ctx context.Context, message string) {
	l.logWithContext(ctx, ERROR, message, nil)
}

// Fatal logs a fatal message and exits
func (l *Logger) Fatal(message string) {
	l.log(FATAL, message, nil)
	os.Exit(1)
}

// Fatalf logs a formatted fatal message and exits
func (l *Logger) Fatalf(format string, args ...interface{}) {
	l.log(FATAL, fmt.Sprintf(format, args...), nil)
	os.Exit(1)
}

// LogHTTPRequest logs HTTP request details
func (l *Logger) LogHTTPRequest(method, path, userAgent, remoteAddr string, statusCode int, duration time.Duration) {
	l.WithFields(map[string]interface{}{
		"http_method":      method,
		"http_path":        path,
		"http_user_agent":  userAgent,
		"http_remote_addr": remoteAddr,
		"http_status_code": statusCode,
		"duration":         duration.String(),
	}).Info("HTTP request processed")
}

// LogDatabaseOperation logs database operation details
func (l *Logger) LogDatabaseOperation(operation, table string, duration time.Duration, rowsAffected int64) {
	l.WithFields(map[string]interface{}{
		"db_operation":     operation,
		"db_table":         table,
		"db_rows_affected": rowsAffected,
		"duration":         duration.String(),
	}).Debug("Database operation completed")
}

// LogBusinessEvent logs business-specific events
func (l *Logger) LogBusinessEvent(event string, entityID string, fields map[string]interface{}) {
	logFields := map[string]interface{}{
		"business_event": event,
		"entity_id":      entityID,
	}

	for k, v := range fields {
		logFields[k] = v
	}

	l.WithFields(logFields).Info("Business event occurred")
}

// log writes a log entry
func (l *Logger) log(level LogLevel, message string, extraFields map[string]interface{}) {
	if level < l.level {
		return
	}

	// Get caller information
	file, line, function := getCaller()

	entry := LogEntry{
		Timestamp: time.Now().UTC(),
		Level:     level.String(),
		Message:   message,
		Service:   l.service,
		Component: l.component,
		File:      file,
		Line:      line,
		Function:  function,
		Fields:    make(map[string]interface{}),
	}

	// Add logger fields
	for k, v := range l.fields {
		entry.Fields[k] = v
	}

	// Add extra fields
	if extraFields != nil {
		for k, v := range extraFields {
			entry.Fields[k] = v
		}
	}

	// Remove empty fields map if no fields
	if len(entry.Fields) == 0 {
		entry.Fields = nil
	}

	l.writeEntry(entry)
}

// logWithContext writes a log entry with context information
func (l *Logger) logWithContext(ctx context.Context, level LogLevel, message string, extraFields map[string]interface{}) {
	if level < l.level {
		return
	}

	// Get caller information
	file, line, function := getCaller()

	entry := LogEntry{
		Timestamp: time.Now().UTC(),
		Level:     level.String(),
		Message:   message,
		Service:   l.service,
		Component: l.component,
		File:      file,
		Line:      line,
		Function:  function,
		Fields:    make(map[string]interface{}),
	}

	// Extract context values
	if traceID := getFromContext(ctx, traceIDKey); traceID != "" {
		entry.TraceID = traceID
	}
	if userID := getFromContext(ctx, userIDKey); userID != "" {
		entry.UserID = userID
	}
	if requestID := getFromContext(ctx, requestIDKey); requestID != "" {
		entry.RequestID = requestID
	}

	// Add logger fields
	for k, v := range l.fields {
		entry.Fields[k] = v
	}

	// Add extra fields
	if extraFields != nil {
		for k, v := range extraFields {
			entry.Fields[k] = v
		}
	}

	// Remove empty fields map if no fields
	if len(entry.Fields) == 0 {
		entry.Fields = nil
	}

	l.writeEntry(entry)
}

// writeEntry writes the log entry to the output
func (l *Logger) writeEntry(entry LogEntry) {
	var output string

	switch l.format {
	case JSON:
		if jsonBytes, err := json.Marshal(entry); err == nil {
			output = string(jsonBytes)
		} else {
			output = fmt.Sprintf(`{"level":"ERROR","message":"Failed to marshal log entry: %s","timestamp":"%s"}`,
				err.Error(), time.Now().UTC().Format(time.RFC3339))
		}
	case TEXT:
		output = l.formatTextEntry(entry)
	}

	fmt.Fprintln(l.output, output)
}

// formatTextEntry formats a log entry as human-readable text
func (l *Logger) formatTextEntry(entry LogEntry) string {
	timestamp := entry.Timestamp.Format("2006-01-02 15:04:05")

	baseMsg := fmt.Sprintf("[%s] %s [%s/%s] %s:%d %s - %s",
		timestamp, entry.Level, entry.Service, entry.Component,
		entry.File, entry.Line, entry.Function, entry.Message)

	if entry.TraceID != "" {
		baseMsg += fmt.Sprintf(" [trace=%s]", entry.TraceID)
	}
	if entry.RequestID != "" {
		baseMsg += fmt.Sprintf(" [request=%s]", entry.RequestID)
	}
	if entry.UserID != "" {
		baseMsg += fmt.Sprintf(" [user=%s]", entry.UserID)
	}

	if entry.Fields != nil && len(entry.Fields) > 0 {
		if fieldsJSON, err := json.Marshal(entry.Fields); err == nil {
			baseMsg += fmt.Sprintf(" fields=%s", string(fieldsJSON))
		}
	}

	return baseMsg
}

// getCaller returns information about the calling function
func getCaller() (file string, line int, function string) {
	// Skip 3 frames: getCaller, log/logWithContext, public logging method
	pc, fullFile, line, ok := runtime.Caller(3)
	if !ok {
		return "unknown", 0, "unknown"
	}

	file = filepath.Base(fullFile)

	if fn := runtime.FuncForPC(pc); fn != nil {
		function = filepath.Base(fn.Name())
	} else {
		function = "unknown"
	}

	return file, line, function
}

// Helper functions

func parseLogLevel(level string) LogLevel {
	switch level {
	case "DEBUG":
		return DEBUG
	case "INFO":
		return INFO
	case "WARN", "WARNING":
		return WARN
	case "ERROR":
		return ERROR
	case "FATAL":
		return FATAL
	default:
		return INFO
	}
}

func parseLogFormat(format string) LogFormat {
	switch format {
	case "JSON":
		return JSON
	case "TEXT":
		return TEXT
	default:
		return JSON
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getFromContext(ctx context.Context, key contextKey) string {
	if value := ctx.Value(key); value != nil {
		if str, ok := value.(string); ok {
			return str
		}
	}
	return ""
}

// Context helper functions

// WithTraceID adds a trace ID to the context
func WithTraceID(ctx context.Context, traceID string) context.Context {
	return context.WithValue(ctx, traceIDKey, traceID)
}

// WithUserID adds a user ID to the context
func WithUserID(ctx context.Context, userID string) context.Context {
	return context.WithValue(ctx, userIDKey, userID)
}

// WithRequestID adds a request ID to the context
func WithRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, requestIDKey, requestID)
}

// GetTraceID retrieves the trace ID from context
func GetTraceID(ctx context.Context) string {
	return getFromContext(ctx, traceIDKey)
}

// GetUserID retrieves the user ID from context
func GetUserID(ctx context.Context) string {
	return getFromContext(ctx, userIDKey)
}

// GetRequestID retrieves the request ID from context
func GetRequestID(ctx context.Context) string {
	return getFromContext(ctx, requestIDKey)
}

// Default logger instance
var defaultLogger *Logger

// InitDefault initializes the default logger
func InitDefault(service, component string) {
	defaultLogger = NewFromEnv(service, component)
}

// Default logging functions using the default logger

func Debug(message string) {
	if defaultLogger != nil {
		defaultLogger.Debug(message)
	}
}

func Debugf(format string, args ...interface{}) {
	if defaultLogger != nil {
		defaultLogger.Debugf(format, args...)
	}
}

func Info(message string) {
	if defaultLogger != nil {
		defaultLogger.Info(message)
	}
}

func Infof(format string, args ...interface{}) {
	if defaultLogger != nil {
		defaultLogger.Infof(format, args...)
	}
}

func Warn(message string) {
	if defaultLogger != nil {
		defaultLogger.Warn(message)
	}
}

func Warnf(format string, args ...interface{}) {
	if defaultLogger != nil {
		defaultLogger.Warnf(format, args...)
	}
}

func Error(message string) {
	if defaultLogger != nil {
		defaultLogger.Error(message)
	}
}

func Errorf(format string, args ...interface{}) {
	if defaultLogger != nil {
		defaultLogger.Errorf(format, args...)
	}
}

func Fatal(message string) {
	if defaultLogger != nil {
		defaultLogger.Fatal(message)
	}
}

func Fatalf(format string, args ...interface{}) {
	if defaultLogger != nil {
		defaultLogger.Fatalf(format, args...)
	}
}
