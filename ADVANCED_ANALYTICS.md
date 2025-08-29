# Advanced Log Analytics Documentation

## Overview

The improved log analytics system provides sophisticated analysis capabilities including:

- **Statistical Analysis**: Error frequency, patterns, and trends
- **Machine Learning Anomaly Detection**: ML-based pattern recognition
- **Performance Analysis**: Response time analysis and bottleneck detection
- **Security Analysis**: Threat detection and security scoring
- **Real-time Monitoring**: Continuous system health monitoring
- **Reliability Scoring**: Overall system reliability assessment

## Features

### 🔍 Core Analytics Engine

#### Error Analysis
- **Error Frequency**: Counts and rates by level, source, and time
- **Severity Scoring**: Weighted severity assessment
- **Error Patterns**: Common error signatures and clustering
- **Time Distribution**: When errors occur most frequently

#### Pattern Detection
- **Message Clustering**: Groups similar log messages
- **Temporal Patterns**: Time-based behavior analysis
- **Source Patterns**: Service-specific behavior analysis
- **Frequent Terms**: Most common words and phrases

#### Trend Analysis
- **Volume Statistics**: Log volume trends and variance
- **Hourly/Daily Distribution**: Activity patterns over time
- **Error Trends**: Error rate changes over time
- **Performance Indicators**: Response time metrics

### 🤖 Machine Learning Anomaly Detection

#### Statistical Anomalies
- **Z-Score Analysis**: Detects values outside normal ranges
- **Baseline Comparison**: Compares current vs historical patterns
- **Feature-based Detection**: Multi-dimensional anomaly detection

#### Pattern Anomalies
- **Message Pattern Analysis**: Unusual message patterns
- **Frequency Anomalies**: Unusually frequent/rare patterns
- **Signature Detection**: Common error signatures

#### Temporal Anomalies
- **Volume Spikes/Drops**: Unusual activity levels
- **Time-based Clustering**: Error clustering in time
- **Seasonal Pattern Breaks**: Deviations from normal schedules

#### Clustering Anomalies
- **Error Clustering**: Errors clustered by source/time
- **Behavioral Changes**: Unusual service behavior patterns

### ⚡ Performance Analysis

#### Response Time Analysis
- **Distribution Metrics**: Average, median, percentiles
- **Slow Operation Detection**: Operations exceeding thresholds
- **Performance Scoring**: Overall performance assessment
- **Bottleneck Identification**: System bottlenecks

#### Throughput Analysis
- **Operation Counts**: Volume by source/service
- **Capacity Planning**: Volume trend analysis
- **Load Distribution**: Request distribution patterns

### 🔒 Security Analysis

#### Threat Detection
- **Failed Login Detection**: Authentication failures
- **Injection Attempts**: SQL injection, XSS detection
- **Access Violations**: Unauthorized access attempts
- **Suspicious Activities**: Unusual user behavior

#### Security Scoring
- **Risk Assessment**: Overall security risk score
- **Threat Categorization**: High/medium/low severity
- **Security Trends**: Security event patterns over time

### 📊 Reliability Scoring

#### Multi-factor Assessment
- **Error Rate Factor**: Impact of error frequency
- **Severity Factor**: Impact of error severity
- **Volume Consistency**: Stability of log volume
- **Source Diversity**: Health across services

#### Grading System
- **A-F Grades**: Easy-to-understand reliability grades
- **Factor Breakdown**: Detailed scoring components
- **Improvement Recommendations**: Actionable insights

## Usage

### Command Line Interface

#### Basic Analysis
```bash
# Analyze last 1000 logs
python analytics_cli.py

# Analyze last 24 hours
python analytics_cli.py --hours 24

# Use sample data
python analytics_cli.py --sample
```

#### Advanced Analysis
```bash
# Enable ML anomaly detection
python analytics_cli.py --ml-anomaly --baseline-days 7

# Export detailed report
python analytics_cli.py --export report.json

# Real-time monitoring
python analytics_cli.py --real-time
```

#### Health Checks
```bash
# Test database connection
python analytics_cli.py --test-connection

# Full health check
python analytics_cli.py --health-check
```

### Python API

#### Basic Usage
```python
from dashboard import LogAnalyticsDashboard
from database_connector import get_recent_logs

# Initialize dashboard
dashboard = LogAnalyticsDashboard()

# Load logs
logs = get_recent_logs(1000)

# Run analysis
report = dashboard.run_comprehensive_analysis(logs)

# Access results
print(f"Error rate: {report['error_analysis']['error_rate']:.2f}%")
print(f"Reliability score: {report['reliability_score']['score']:.1f}/100")
```

#### ML Anomaly Detection
```python
from ml_anomaly_detector import MLAnomalyDetector
from database_connector import get_recent_logs, get_historical_baseline

# Initialize ML detector
ml_detector = MLAnomalyDetector()

# Load data
current_logs = get_recent_logs(1000)
historical_logs = get_historical_baseline(7)

# Detect anomalies
anomalies = ml_detector.detect_anomalies(current_logs, historical_logs)

# Process results
for anomaly in anomalies:
    print(f"Anomaly: {anomaly['type']} (confidence: {anomaly['confidence']:.2f})")
```

### Database Integration

#### Direct Database Queries
```python
from database_connector import db_connector

# Get error summary
summary = db_connector.get_error_summary(hours=24)

# Get logs by level
errors = db_connector.get_logs_by_level('error', limit=100)

# Get logs by source
api_logs = db_connector.get_logs_by_source('api_service', limit=500)
```

## Configuration

### Environment Variables

```bash
# Analytics Configuration
ALERT_THRESHOLD=5                    # Error count threshold for alerts
ANALYSIS_WINDOW_HOURS=24            # Default analysis window
ANOMALY_DETECTION_ENABLED=true      # Enable anomaly detection
AUTO_ALERT_ENABLED=true             # Enable automatic alerting
PERFORMANCE_THRESHOLD_MS=5000       # Performance threshold in milliseconds
ML_ANOMALY_THRESHOLD=0.7            # ML anomaly confidence threshold
BASELINE_DAYS=7                     # Days of historical data for baseline

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=log_processing_db

# Alerting Configuration
SLACK_WEBHOOK_URL=your_slack_webhook
SENDER_EMAIL=alerts@company.com
RECEIVER_EMAIL=admin@company.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
```

## Analysis Report Structure

### Complete Report Schema
```json
{
  "timestamp": "2025-08-29T10:30:00Z",
  "summary": {
    "total_logs_analyzed": 1000,
    "time_range": "2025-08-29T09:30:00Z to 2025-08-29T10:30:00Z",
    "health_status": "good",
    "error_rate": 2.5,
    "most_active_source": "api_service"
  },
  "error_analysis": {
    "total_errors": 25,
    "error_rate": 2.5,
    "severity_score": 3.2,
    "errors_by_level": {"error": 20, "fatal": 5},
    "errors_by_source": {"api_service": 15, "db_service": 10},
    "error_patterns": [...],
    "time_distribution": {...}
  },
  "pattern_analysis": {
    "frequent_terms": {...},
    "error_signatures": [...],
    "anomalous_patterns": [...],
    "temporal_patterns": {...},
    "message_clusters": [...]
  },
  "performance_analysis": {
    "performance_score": 85.2,
    "response_time_distribution": {...},
    "slow_operations": [...],
    "bottlenecks": [...]
  },
  "security_analysis": {
    "security_score": 95,
    "failed_logins": 3,
    "threats_detected": [...],
    "access_violations": [...]
  },
  "reliability_score": {
    "score": 82.5,
    "grade": "B",
    "factors": {...}
  },
  "anomaly_analysis": [...],
  "ml_anomalies": [...],
  "recommendations": [...]
}
```

## Alerting System

### Automatic Alerts
- **High Error Rate**: When error rate exceeds threshold
- **Security Threats**: When security issues detected
- **Performance Degradation**: When performance drops
- **System Anomalies**: When ML detects unusual patterns

### Alert Channels
- **Slack**: Real-time notifications
- **Email**: Detailed alert reports
- **Console**: Local notifications

### Alert Configuration
```python
# Customize alert thresholds
dashboard.config['alert_threshold'] = 10
dashboard.config['performance_threshold_ms'] = 3000
dashboard.config['auto_alert_enabled'] = True
```

## Best Practices

### 1. Regular Monitoring
- Run analytics at least hourly for production systems
- Use real-time monitoring for critical services
- Set up automated daily/weekly reports

### 2. Baseline Management
- Update baselines weekly with historical data
- Use at least 7 days of clean historical data
- Exclude known incident periods from baselines

### 3. Threshold Tuning
- Start with conservative thresholds
- Adjust based on false positive rates
- Consider different thresholds for different services

### 4. Performance Optimization
- Use time-range queries for large datasets
- Cache analysis results for repeated queries
- Consider data sampling for very high-volume systems

### 5. Alert Management
- Implement alert escalation procedures
- Use alert grouping to reduce noise
- Regular review and tuning of alert rules

## Troubleshooting

### Common Issues

#### Database Connection Problems
```bash
# Test connection
python analytics_cli.py --test-connection

# Check configuration
echo $DB_HOST $DB_PORT $DB_USER $DB_NAME
```

#### Memory Issues with Large Datasets
```python
# Use time-range queries instead of large limits
logs = db_connector.get_logs_by_time_range(start_time, end_time)

# Process in batches
for batch in batched_logs(logs, batch_size=1000):
    analysis = dashboard.run_comprehensive_analysis(batch)
```

#### Performance Issues
```python
# Disable expensive features for large datasets
dashboard.config['anomaly_detection_enabled'] = False

# Use sampling for very large datasets
sampled_logs = random.sample(logs, 10000)
```

## Integration Examples

### Continuous Integration
```yaml
# GitLab CI example
log_analysis:
  script:
    - python analytics_cli.py --hours 1 --export ci_report.json
    - python check_report.py ci_report.json  # Custom validation
  artifacts:
    reports:
      junit: ci_report.json
```

### Monitoring Integration
```python
# Prometheus metrics export
from prometheus_client import Gauge, Counter

error_rate_gauge = Gauge('log_error_rate', 'Current error rate')
reliability_gauge = Gauge('system_reliability_score', 'System reliability score')

# Update metrics from analysis
report = dashboard.run_comprehensive_analysis(logs)
error_rate_gauge.set(report['error_analysis']['error_rate'])
reliability_gauge.set(report['reliability_score']['score'])
```

### Custom Dashboards
```python
# Web dashboard integration
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/analytics')
def get_analytics():
    logs = get_recent_logs(1000)
    report = dashboard.run_comprehensive_analysis(logs)
    return jsonify(report)
```

This advanced analytics system provides comprehensive insights into your log data with minimal configuration required. The ML-based anomaly detection and multi-dimensional analysis help identify issues before they become critical problems.
