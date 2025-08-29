"""
Advanced Log Analytics Dashboard
Provides real-time monitoring and analysis capabilities
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from analyzer import analyze_error_frequency, detect_patterns, analyze_log_trends, detect_anomalies
from alerting import send_slack_alert, send_email_alert

class LogAnalyticsDashboard:
    """Advanced analytics dashboard for log monitoring."""
    
    def __init__(self):
        self.load_config()
        self.alert_history = []
        self.analysis_cache = {}
        
    def load_config(self):
        """Load configuration from environment variables."""
        from dotenv import load_dotenv
        
        # Load .env from project root
        env_path = Path(__file__).resolve().parents[2] / '.env'
        load_dotenv(dotenv_path=env_path)
        
        self.config = {
            'alert_threshold': int(os.getenv('ALERT_THRESHOLD', 5)),
            'analysis_window_hours': int(os.getenv('ANALYSIS_WINDOW_HOURS', 24)),
            'anomaly_detection_enabled': os.getenv('ANOMALY_DETECTION_ENABLED', 'true').lower() == 'true',
            'auto_alert_enabled': os.getenv('AUTO_ALERT_ENABLED', 'true').lower() == 'true',
            'performance_threshold_ms': int(os.getenv('PERFORMANCE_THRESHOLD_MS', 5000))
        }
    
    def run_comprehensive_analysis(self, logs: List[Dict]) -> Dict[str, Any]:
        """Run comprehensive analysis on log data."""
        if not logs:
            return {'error': 'No logs provided for analysis'}
        
        print(f"Running comprehensive analysis on {len(logs)} log entries...")
        
        # Core analyses
        error_analysis = analyze_error_frequency(logs)
        pattern_analysis = detect_patterns(logs)
        trend_analysis = analyze_log_trends(logs)
        
        # Advanced analyses
        anomaly_analysis = detect_anomalies(logs) if self.config['anomaly_detection_enabled'] else []
        performance_analysis = self.analyze_performance(logs)
        security_analysis = self.analyze_security_events(logs)
        reliability_score = self.calculate_reliability_score(logs, error_analysis, trend_analysis)
        
        # Compile comprehensive report
        analysis_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.generate_summary(logs, error_analysis, trend_analysis),
            'error_analysis': error_analysis,
            'pattern_analysis': pattern_analysis,
            'trend_analysis': trend_analysis,
            'anomaly_analysis': anomaly_analysis,
            'performance_analysis': performance_analysis,
            'security_analysis': security_analysis,
            'reliability_score': reliability_score,
            'recommendations': self.generate_recommendations(error_analysis, anomaly_analysis, performance_analysis)
        }
        
        # Check for alerts
        self.check_and_send_alerts(analysis_report)
        
        # Cache analysis for comparison
        self.analysis_cache[datetime.now().isoformat()] = analysis_report
        
        return analysis_report
    
    def analyze_performance(self, logs: List[Dict]) -> Dict[str, Any]:
        """Analyze performance metrics from logs."""
        performance_data = {
            'slow_operations': [],
            'response_time_distribution': {},
            'throughput_analysis': {},
            'bottlenecks': [],
            'performance_score': 0
        }
        
        response_times = []
        operation_counts = {}
        slow_operations = []
        
        for log in logs:
            if isinstance(log, dict):
                message = log.get('message', '')
                timestamp = log.get('timestamp', '')
                source = log.get('source', '')
                
                # Extract response times
                response_time = self.extract_response_time(message)
                if response_time:
                    response_times.append(response_time)
                    
                    # Flag slow operations
                    if response_time > self.config['performance_threshold_ms']:
                        slow_operations.append({
                            'timestamp': timestamp,
                            'source': source,
                            'response_time': response_time,
                            'message': message[:100]  # Truncate for readability
                        })
                
                # Count operations by source
                operation_counts[source] = operation_counts.get(source, 0) + 1
        
        if response_times:
            # Response time analysis
            avg_response_time = sum(response_times) / len(response_times)
            performance_data['response_time_distribution'] = {
                'average': avg_response_time,
                'min': min(response_times),
                'max': max(response_times),
                'p50': sorted(response_times)[len(response_times)//2],
                'p95': sorted(response_times)[int(len(response_times)*0.95)],
                'p99': sorted(response_times)[int(len(response_times)*0.99)]
            }
            
            # Performance score (0-100, higher is better)
            performance_data['performance_score'] = max(0, 100 - (avg_response_time / 100))
        
        performance_data['slow_operations'] = slow_operations[:10]  # Top 10 slowest
        performance_data['throughput_analysis'] = operation_counts
        
        # Identify bottlenecks
        performance_data['bottlenecks'] = self.identify_bottlenecks(operation_counts, slow_operations)
        
        return performance_data
    
    def analyze_security_events(self, logs: List[Dict]) -> Dict[str, Any]:
        """Analyze security-related events in logs."""
        security_data = {
            'failed_logins': 0,
            'suspicious_activities': [],
            'access_violations': [],
            'security_score': 100,
            'threats_detected': []
        }
        
        # Security patterns to look for
        security_patterns = {
            'failed_login': ['failed login', 'authentication failed', 'invalid credentials', 'login denied'],
            'access_violation': ['access denied', 'unauthorized', 'forbidden', 'permission denied'],
            'suspicious': ['brute force', 'multiple attempts', 'unusual activity', 'security alert'],
            'injection': ['sql injection', 'xss', 'script injection', 'code injection']
        }
        
        for log in logs:
            if isinstance(log, dict):
                message = log.get('message', '').lower()
                level = log.get('level', '').lower()
                source = log.get('source', '')
                timestamp = log.get('timestamp', '')
                
                # Check for security events
                for event_type, patterns in security_patterns.items():
                    for pattern in patterns:
                        if pattern in message:
                            if event_type == 'failed_login':
                                security_data['failed_logins'] += 1
                            elif event_type == 'access_violation':
                                security_data['access_violations'].append({
                                    'timestamp': timestamp,
                                    'source': source,
                                    'message': log.get('message', '')[:100]
                                })
                            elif event_type in ['suspicious', 'injection']:
                                security_data['threats_detected'].append({
                                    'type': event_type,
                                    'timestamp': timestamp,
                                    'source': source,
                                    'severity': 'high' if level in ['error', 'fatal'] else 'medium',
                                    'message': log.get('message', '')[:100]
                                })
                            break
        
        # Calculate security score
        total_security_events = (security_data['failed_logins'] + 
                               len(security_data['access_violations']) + 
                               len(security_data['threats_detected']))
        
        if total_security_events > 0:
            security_data['security_score'] = max(0, 100 - (total_security_events * 5))
        
        return security_data
    
    def calculate_reliability_score(self, logs: List[Dict], error_analysis: Dict, trend_analysis: Dict) -> Dict[str, Any]:
        """Calculate overall system reliability score."""
        if not logs:
            return {'score': 0, 'factors': {}}
        
        factors = {}
        
        # Error rate factor (0-40 points)
        error_rate = error_analysis.get('error_rate', 0)
        error_factor = max(0, 40 - (error_rate * 2))
        factors['error_rate'] = {'score': error_factor, 'value': error_rate}
        
        # Severity factor (0-20 points)
        severity_score = error_analysis.get('severity_score', 0)
        severity_factor = max(0, 20 - severity_score)
        factors['severity'] = {'score': severity_factor, 'value': severity_score}
        
        # Volume consistency factor (0-20 points)
        volume_stats = trend_analysis.get('volume_statistics', {})
        if volume_stats and volume_stats.get('std_dev', 0) > 0:
            cv = volume_stats['std_dev'] / volume_stats['mean']  # Coefficient of variation
            volume_factor = max(0, 20 - (cv * 10))
        else:
            volume_factor = 20
        factors['volume_consistency'] = {'score': volume_factor, 'value': volume_stats.get('std_dev', 0)}
        
        # Source diversity factor (0-20 points)
        source_count = len(trend_analysis.get('by_source', {}))
        source_factor = min(20, source_count * 2)
        factors['source_diversity'] = {'score': source_factor, 'value': source_count}
        
        # Calculate overall score
        total_score = sum(factor['score'] for factor in factors.values())
        
        return {
            'score': total_score,
            'grade': self.get_reliability_grade(total_score),
            'factors': factors
        }
    
    def generate_summary(self, logs: List[Dict], error_analysis: Dict, trend_analysis: Dict) -> Dict[str, Any]:
        """Generate executive summary of log analysis."""
        total_logs = len(logs)
        error_count = error_analysis.get('total_errors', 0)
        error_rate = error_analysis.get('error_rate', 0)
        
        # Determine overall health status
        if error_rate < 1:
            health_status = 'excellent'
        elif error_rate < 5:
            health_status = 'good'
        elif error_rate < 15:
            health_status = 'warning'
        else:
            health_status = 'critical'
        
        return {
            'total_logs_analyzed': total_logs,
            'time_range': self.get_time_range(logs),
            'health_status': health_status,
            'error_count': error_count,
            'error_rate': round(error_rate, 2),
            'most_active_source': max(trend_analysis.get('by_source', {}).items(), key=lambda x: x[1])[0] if trend_analysis.get('by_source') else 'unknown',
            'peak_activity_hour': max(trend_analysis.get('hourly_distribution', {}).items(), key=lambda x: x[1])[0] if trend_analysis.get('hourly_distribution') else 'unknown'
        }
    
    def generate_recommendations(self, error_analysis: Dict, anomaly_analysis: List, performance_analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Error-based recommendations
        error_rate = error_analysis.get('error_rate', 0)
        if error_rate > 10:
            recommendations.append(f"High error rate detected ({error_rate:.1f}%). Investigate error patterns and implement fixes.")
        
        # Source-based recommendations
        errors_by_source = error_analysis.get('errors_by_source', {})
        if errors_by_source:
            top_error_source = max(errors_by_source.items(), key=lambda x: x[1])
            if top_error_source[1] > 5:
                recommendations.append(f"Source '{top_error_source[0]}' has {top_error_source[1]} errors. Focus debugging efforts here.")
        
        # Anomaly-based recommendations
        for anomaly in anomaly_analysis:
            if anomaly.get('severity') == 'high':
                recommendations.append(f"High-severity anomaly detected: {anomaly.get('type')}. Immediate investigation recommended.")
        
        # Performance-based recommendations
        slow_ops = performance_analysis.get('slow_operations', [])
        if len(slow_ops) > 5:
            recommendations.append(f"{len(slow_ops)} slow operations detected. Consider performance optimization.")
        
        # Default recommendation if no issues found
        if not recommendations:
            recommendations.append("System appears to be operating normally. Continue monitoring.")
        
        return recommendations
    
    def check_and_send_alerts(self, analysis_report: Dict):
        """Check analysis results and send alerts if necessary."""
        if not self.config['auto_alert_enabled']:
            return
        
        alerts_to_send = []
        
        # Error rate alerts
        error_rate = analysis_report['error_analysis'].get('error_rate', 0)
        if error_rate > self.config['alert_threshold']:
            alerts_to_send.append(f"High error rate alert: {error_rate:.1f}% error rate detected")
        
        # Anomaly alerts
        high_severity_anomalies = [a for a in analysis_report['anomaly_analysis'] if a.get('severity') == 'high']
        if high_severity_anomalies:
            alerts_to_send.append(f"High-severity anomalies detected: {len(high_severity_anomalies)} anomalies found")
        
        # Security alerts
        security_threats = analysis_report['security_analysis'].get('threats_detected', [])
        if security_threats:
            alerts_to_send.append(f"Security threats detected: {len(security_threats)} potential threats found")
        
        # Performance alerts
        slow_operations = analysis_report['performance_analysis'].get('slow_operations', [])
        if len(slow_operations) > 10:
            alerts_to_send.append(f"Performance degradation detected: {len(slow_operations)} slow operations")
        
        # Send alerts
        for alert_message in alerts_to_send:
            print(f"ALERT: {alert_message}")
            self.alert_history.append({
                'timestamp': datetime.now().isoformat(),
                'message': alert_message
            })
            
            try:
                send_slack_alert(alert_message)
                send_email_alert("Log Analysis Alert", alert_message)
            except Exception as e:
                print(f"Failed to send alert: {e}")
    
    # Helper methods
    def extract_response_time(self, message: str) -> float:
        """Extract response time from log message."""
        import re
        patterns = [
            r'took (\d+\.?\d*)ms',
            r'duration:?\s*(\d+\.?\d*)s',
            r'(\d+\.?\d*)ms',
            r'time=(\d+\.?\d*)ms'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1))
                    if 'duration' in pattern or pattern.endswith('s'):
                        value *= 1000
                    return value
                except ValueError:
                    continue
        return None
    
    def identify_bottlenecks(self, operation_counts: Dict, slow_operations: List) -> List[Dict]:
        """Identify potential bottlenecks in the system."""
        bottlenecks = []
        
        # Sources with high operation counts and slow operations
        slow_sources = {}
        for op in slow_operations:
            source = op.get('source', 'unknown')
            slow_sources[source] = slow_sources.get(source, 0) + 1
        
        for source, slow_count in slow_sources.items():
            total_ops = operation_counts.get(source, 0)
            if total_ops > 0:
                slow_ratio = slow_count / total_ops
                if slow_ratio > 0.1:  # More than 10% slow operations
                    bottlenecks.append({
                        'source': source,
                        'slow_operations': slow_count,
                        'total_operations': total_ops,
                        'slow_ratio': slow_ratio,
                        'severity': 'high' if slow_ratio > 0.3 else 'medium'
                    })
        
        return sorted(bottlenecks, key=lambda x: x['slow_ratio'], reverse=True)
    
    def get_reliability_grade(self, score: float) -> str:
        """Convert reliability score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_time_range(self, logs: List[Dict]) -> str:
        """Get time range of log data."""
        timestamps = [log.get('timestamp', '') for log in logs if log.get('timestamp')]
        if timestamps:
            return f"{min(timestamps)} to {max(timestamps)}"
        return "Unknown"
    
    def export_analysis_report(self, analysis_report: Dict, filename: str = None) -> str:
        """Export analysis report to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"log_analysis_report_{timestamp}.json"
        
        filepath = Path(__file__).parent / "reports" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(analysis_report, f, indent=2, default=str)
        
        return str(filepath)
