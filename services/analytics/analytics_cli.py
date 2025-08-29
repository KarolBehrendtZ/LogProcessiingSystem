#!/usr/bin/env python3
"""
Advanced Log Analytics CLI Tool
Provides command-line interface for running sophisticated log analysis
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from dashboard import LogAnalyticsDashboard
from ml_anomaly_detector import MLAnomalyDetector
from database_connector import db_connector, get_recent_logs, get_historical_baseline

def setup_args():
    """Setup command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced Log Analytics CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --recent 1000                    # Analyze last 1000 logs
  %(prog)s --hours 24 --ml-anomaly         # 24-hour analysis with ML anomaly detection
  %(prog)s --export report.json            # Export detailed report
  %(prog)s --real-time                     # Real-time monitoring mode
  %(prog)s --baseline-days 7               # Use 7 days of historical data for baseline
        """
    )
    
    # Data source options
    data_group = parser.add_argument_group('Data Source Options')
    data_group.add_argument('--recent', type=int, default=1000,
                           help='Number of recent logs to analyze (default: 1000)')
    data_group.add_argument('--hours', type=int,
                           help='Analyze logs from last N hours')
    data_group.add_argument('--days', type=int,
                           help='Analyze logs from last N days')
    data_group.add_argument('--sample', action='store_true',
                           help='Use sample data instead of database')
    
    # Analysis options
    analysis_group = parser.add_argument_group('Analysis Options')
    analysis_group.add_argument('--ml-anomaly', action='store_true',
                               help='Enable machine learning-based anomaly detection')
    analysis_group.add_argument('--baseline-days', type=int, default=7,
                               help='Days of historical data for baseline (default: 7)')
    analysis_group.add_argument('--no-alerts', action='store_true',
                               help='Disable automatic alerting')
    analysis_group.add_argument('--threshold', type=float, default=0.7,
                               help='Anomaly detection threshold (default: 0.7)')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--export', type=str,
                             help='Export detailed report to JSON file')
    output_group.add_argument('--format', choices=['text', 'json'], default='text',
                             help='Output format (default: text)')
    output_group.add_argument('--verbose', '-v', action='store_true',
                             help='Verbose output')
    output_group.add_argument('--quiet', '-q', action='store_true',
                             help='Minimal output')
    
    # Special modes
    mode_group = parser.add_argument_group('Special Modes')
    mode_group.add_argument('--real-time', action='store_true',
                           help='Real-time monitoring mode')
    mode_group.add_argument('--test-connection', action='store_true',
                           help='Test database connection and exit')
    mode_group.add_argument('--health-check', action='store_true',
                           help='Quick health check and exit')
    
    return parser

def load_sample_data():
    """Load sample data for testing."""
    return [
        {"level": "error", "message": "Database connection failed after 3 retries", "timestamp": "2025-08-29T10:15:30Z", "source": "database_service"},
        {"level": "info", "message": "User authentication successful for user_123", "timestamp": "2025-08-29T10:16:00Z", "source": "auth_service"},
        {"level": "error", "message": "Request timeout while processing /api/users (took 5500ms)", "timestamp": "2025-08-29T10:16:30Z", "source": "api_service"},
        {"level": "warn", "message": "Disk space usage at 85% on server-01", "timestamp": "2025-08-29T10:17:00Z", "source": "system_monitor"},
        {"level": "fatal", "message": "Critical system failure: Out of memory", "timestamp": "2025-08-29T10:17:30Z", "source": "system_monitor"},
        {"level": "info", "message": "Database backup completed successfully (took 1200ms)", "timestamp": "2025-08-29T10:18:00Z", "source": "backup_service"},
        {"level": "error", "message": "Failed login attempt for user admin from IP 192.168.1.100", "timestamp": "2025-08-29T10:18:30Z", "source": "auth_service"},
        {"level": "error", "message": "SQL injection attempt detected in parameter 'user_id'", "timestamp": "2025-08-29T10:20:00Z", "source": "security_service"},
    ]

def load_logs_from_database(args):
    """Load logs from database based on arguments."""
    if args.hours:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=args.hours)
        return db_connector.get_logs_by_time_range(
            start_time.isoformat(),
            end_time.isoformat()
        )
    elif args.days:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=args.days)
        return db_connector.get_logs_by_time_range(
            start_time.isoformat(),
            end_time.isoformat()
        )
    else:
        return get_recent_logs(args.recent)

def print_text_output(analysis_report, verbose=False):
    """Print analysis results in text format."""
    print("=" * 80)
    print("🔍 LOG ANALYSIS RESULTS")
    print("=" * 80)
    
    # Summary
    summary = analysis_report['summary']
    print(f"\n📋 EXECUTIVE SUMMARY")
    print(f"   • Analysis Time: {analysis_report['timestamp']}")
    print(f"   • Total Logs: {summary['total_logs_analyzed']}")
    print(f"   • Time Range: {summary['time_range']}")
    print(f"   • Health Status: {summary['health_status'].upper()}")
    print(f"   • Error Rate: {summary['error_rate']}%")
    print(f"   • Most Active Source: {summary['most_active_source']}")
    
    # Error Analysis
    error_analysis = analysis_report['error_analysis']
    print(f"\n🚨 ERROR ANALYSIS")
    print(f"   • Total Errors: {error_analysis['total_errors']}")
    print(f"   • Error Rate: {error_analysis['error_rate']:.2f}%")
    print(f"   • Severity Score: {error_analysis['severity_score']:.2f}")
    
    if error_analysis.get('errors_by_level') and verbose:
        print(f"   • Errors by Level:")
        for level, count in error_analysis['errors_by_level'].items():
            print(f"     - {level}: {count}")
    
    # Performance Analysis
    perf_analysis = analysis_report['performance_analysis']
    print(f"\n⚡ PERFORMANCE ANALYSIS")
    print(f"   • Performance Score: {perf_analysis.get('performance_score', 0):.1f}/100")
    
    if perf_analysis.get('response_time_distribution'):
        rt_dist = perf_analysis['response_time_distribution']
        print(f"   • Average Response Time: {rt_dist['average']:.1f}ms")
        print(f"   • 95th Percentile: {rt_dist['p95']:.1f}ms")
    
    slow_ops = len(perf_analysis.get('slow_operations', []))
    if slow_ops > 0:
        print(f"   • Slow Operations: {slow_ops}")
    
    # Security Analysis
    security_analysis = analysis_report['security_analysis']
    print(f"\n🔒 SECURITY ANALYSIS")
    print(f"   • Security Score: {security_analysis['security_score']}/100")
    print(f"   • Failed Logins: {security_analysis['failed_logins']}")
    print(f"   • Threats Detected: {len(security_analysis['threats_detected'])}")
    
    # Reliability Score
    reliability = analysis_report['reliability_score']
    print(f"\n📊 RELIABILITY SCORE")
    print(f"   • Overall Score: {reliability['score']:.1f}/100 (Grade: {reliability['grade']})")
    
    # Anomalies
    anomalies = analysis_report['anomaly_analysis']
    if anomalies:
        print(f"\n⚠️  ANOMALIES DETECTED ({len(anomalies)})")
        for i, anomaly in enumerate(anomalies[:5], 1):  # Show top 5
            confidence = anomaly.get('confidence', 0) * 100
            print(f"   {i}. {anomaly['type']} (confidence: {confidence:.1f}%)")
            if verbose:
                print(f"      {anomaly.get('description', 'No description')}")
    
    # ML Anomalies (if available)
    if 'ml_anomalies' in analysis_report:
        ml_anomalies = analysis_report['ml_anomalies']
        if ml_anomalies:
            print(f"\n🤖 ML-DETECTED ANOMALIES ({len(ml_anomalies)})")
            for i, anomaly in enumerate(ml_anomalies[:3], 1):  # Show top 3
                confidence = anomaly.get('confidence', 0) * 100
                print(f"   {i}. {anomaly['type']} (confidence: {confidence:.1f}%)")
                if verbose:
                    print(f"      {anomaly.get('description', 'No description')}")
    
    # Recommendations
    recommendations = analysis_report['recommendations']
    print(f"\n💡 RECOMMENDATIONS")
    for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
        print(f"   {i}. {rec}")

def print_json_output(analysis_report):
    """Print analysis results in JSON format."""
    print(json.dumps(analysis_report, indent=2, default=str))

def run_health_check():
    """Run quick health check."""
    print("🏥 Running health check...")
    
    # Test database connection
    if db_connector.test_connection():
        print("✅ Database connection: OK")
    else:
        print("❌ Database connection: FAILED")
        return False
    
    # Test log retrieval
    try:
        recent_logs = get_recent_logs(10)
        if recent_logs:
            print(f"✅ Log retrieval: OK ({len(recent_logs)} logs)")
        else:
            print("⚠️  Log retrieval: No logs found")
    except Exception as e:
        print(f"❌ Log retrieval: FAILED ({e})")
        return False
    
    # Test analytics
    try:
        dashboard = LogAnalyticsDashboard()
        print("✅ Analytics dashboard: OK")
    except Exception as e:
        print(f"❌ Analytics dashboard: FAILED ({e})")
        return False
    
    print("🎯 Health check completed successfully!")
    return True

def run_real_time_monitoring():
    """Run real-time monitoring mode."""
    print("🔄 Starting real-time monitoring mode...")
    print("Press Ctrl+C to stop")
    
    try:
        import time
        dashboard = LogAnalyticsDashboard()
        
        while True:
            print(f"\n{'='*60}")
            print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Get recent logs
            logs = get_recent_logs(100)  # Analyze last 100 logs
            
            if logs:
                # Run quick analysis
                analysis = dashboard.run_comprehensive_analysis(logs)
                
                # Print summary
                summary = analysis['summary']
                error_analysis = analysis['error_analysis']
                
                print(f"📊 Logs: {len(logs)} | Errors: {error_analysis['total_errors']} | Rate: {error_analysis['error_rate']:.1f}%")
                print(f"🏥 Health: {summary['health_status'].upper()}")
                
                # Check for anomalies
                anomalies = analysis['anomaly_analysis']
                if anomalies:
                    print(f"⚠️  {len(anomalies)} anomalies detected!")
                
            else:
                print("📭 No recent logs found")
            
            # Wait for next check
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        print("\n\n👋 Real-time monitoring stopped")

def main():
    """Main CLI function."""
    parser = setup_args()
    args = parser.parse_args()
    
    # Handle special modes first
    if args.test_connection:
        success = db_connector.test_connection()
        print("✅ Database connection successful!" if success else "❌ Database connection failed!")
        sys.exit(0 if success else 1)
    
    if args.health_check:
        success = run_health_check()
        sys.exit(0 if success else 1)
    
    if args.real_time:
        run_real_time_monitoring()
        return
    
    # Load log data
    if not args.quiet:
        print("📊 Loading log data...")
    
    if args.sample:
        logs = load_sample_data()
        if not args.quiet:
            print(f"✅ Loaded {len(logs)} sample log entries")
    else:
        try:
            logs = load_logs_from_database(args)
            if not args.quiet:
                print(f"✅ Loaded {len(logs)} log entries from database")
        except Exception as e:
            print(f"❌ Failed to load logs from database: {e}")
            print("🔄 Falling back to sample data...")
            logs = load_sample_data()
    
    if not logs:
        print("❌ No logs available for analysis")
        sys.exit(1)
    
    # Initialize analytics
    dashboard = LogAnalyticsDashboard()
    
    # Disable alerts if requested
    if args.no_alerts:
        dashboard.config['auto_alert_enabled'] = False
    
    # Run analysis
    if not args.quiet:
        print("🔬 Running comprehensive analysis...")
    
    analysis_report = dashboard.run_comprehensive_analysis(logs)
    
    # Add ML anomaly detection if requested
    if args.ml_anomaly:
        if not args.quiet:
            print("🤖 Running ML-based anomaly detection...")
        
        ml_detector = MLAnomalyDetector()
        
        # Get historical baseline if available
        historical_data = None
        if not args.sample:
            try:
                historical_data = get_historical_baseline(args.baseline_days)
                if not args.quiet and historical_data:
                    print(f"📚 Using {len(historical_data)} historical logs for baseline")
            except Exception as e:
                if args.verbose:
                    print(f"⚠️  Could not load historical baseline: {e}")
        
        ml_anomalies = ml_detector.detect_anomalies(logs, historical_data)
        analysis_report['ml_anomalies'] = ml_anomalies
        
        if not args.quiet and ml_anomalies:
            print(f"🤖 ML detected {len(ml_anomalies)} anomalies")
    
    # Output results
    if args.format == 'json':
        print_json_output(analysis_report)
    else:
        print_text_output(analysis_report, verbose=args.verbose)
    
    # Export if requested
    if args.export:
        try:
            report_file = dashboard.export_analysis_report(analysis_report, args.export)
            if not args.quiet:
                print(f"\n💾 Report exported to: {report_file}")
        except Exception as e:
            print(f"❌ Failed to export report: {e}")
            sys.exit(1)
    
    if not args.quiet:
        print(f"\n🎯 Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        if '--verbose' in sys.argv:
            traceback.print_exc()
        sys.exit(1)
