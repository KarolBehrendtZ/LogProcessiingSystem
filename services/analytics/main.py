import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dashboard import LogAnalyticsDashboard

# Add the database module to the path
sys.path.append(str(Path(__file__).resolve().parents[2] / 'services' / 'log-ingestion'))

def get_sample_logs():
    """Get sample log data for testing (replace with database connection in production)."""
    return [
        {
            "level": "error", 
            "message": "Database connection failed after 3 retries", 
            "timestamp": "2025-08-29T10:15:30Z", 
            "source": "database_service"
        },
        {
            "level": "info", 
            "message": "User authentication successful for user_123", 
            "timestamp": "2025-08-29T10:16:00Z", 
            "source": "auth_service"
        },
        {
            "level": "error", 
            "message": "Request timeout while processing /api/users (took 5500ms)", 
            "timestamp": "2025-08-29T10:16:30Z", 
            "source": "api_service"
        },
        {
            "level": "warn", 
            "message": "Disk space usage at 85% on server-01", 
            "timestamp": "2025-08-29T10:17:00Z", 
            "source": "system_monitor"
        },
        {
            "level": "fatal", 
            "message": "Critical system failure: Out of memory", 
            "timestamp": "2025-08-29T10:17:30Z", 
            "source": "system_monitor"
        },
        {
            "level": "info", 
            "message": "Database backup completed successfully (took 1200ms)", 
            "timestamp": "2025-08-29T10:18:00Z", 
            "source": "backup_service"
        },
        {
            "level": "error", 
            "message": "Failed login attempt for user admin from IP 192.168.1.100", 
            "timestamp": "2025-08-29T10:18:30Z", 
            "source": "auth_service"
        },
        {
            "level": "error", 
            "message": "Database connection failed after 3 retries", 
            "timestamp": "2025-08-29T10:19:00Z", 
            "source": "database_service"
        },
        {
            "level": "warn", 
            "message": "API rate limit exceeded for client 192.168.1.50", 
            "timestamp": "2025-08-29T10:19:30Z", 
            "source": "api_service"
        },
        {
            "level": "error", 
            "message": "SQL injection attempt detected in parameter 'user_id'", 
            "timestamp": "2025-08-29T10:20:00Z", 
            "source": "security_service"
        },
        {
            "level": "info", 
            "message": "Cache cleared successfully", 
            "timestamp": "2025-08-29T10:20:30Z", 
            "source": "cache_service"
        },
        {
            "level": "error", 
            "message": "Request timeout while processing /api/reports (took 8000ms)", 
            "timestamp": "2025-08-29T10:21:00Z", 
            "source": "api_service"
        }
    ]

def load_logs_from_database():
    """Load logs from database (requires database connection)."""
    try:
        # Import database functions
        from database.postgres import GetRecentLogs
        
        # Get recent logs from database
        logs = GetRecentLogs(1000)  # Get last 1000 logs
        
        # Convert to dictionary format
        log_dicts = []
        for log in logs:
            log_dicts.append({
                'id': log.ID,
                'level': log.Level,
                'message': log.Message,
                'timestamp': log.Timestamp.isoformat(),
                'source': log.Source
            })
        
        return log_dicts
    except ImportError:
        print("Database module not available. Using sample data.")
        return get_sample_logs()
    except Exception as e:
        print(f"Failed to load logs from database: {e}")
        print("Using sample data instead.")
        return get_sample_logs()

def main():
    """Main analytics function with advanced analysis capabilities."""
    print("=" * 60)
    print("🔍 ADVANCED LOG ANALYTICS SYSTEM")
    print("=" * 60)
    
    # Initialize analytics dashboard
    dashboard = LogAnalyticsDashboard()
    
    # Load log data
    print("\n📊 Loading log data...")
    
    # Try to load from database, fall back to sample data
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        logs = get_sample_logs()
        print(f"✅ Loaded {len(logs)} sample log entries")
    else:
        logs = load_logs_from_database()
        print(f"✅ Loaded {len(logs)} log entries from data source")
    
    if not logs:
        print("❌ No logs available for analysis")
        return
    
    # Run comprehensive analysis
    print("\n🔬 Running comprehensive analysis...")
    analysis_report = dashboard.run_comprehensive_analysis(logs)
    
    # Display results
    print("\n" + "=" * 60)
    print("📈 ANALYSIS RESULTS")
    print("=" * 60)
    
    # Summary
    summary = analysis_report['summary']
    print(f"\n📋 EXECUTIVE SUMMARY")
    print(f"   • Total logs analyzed: {summary['total_logs_analyzed']}")
    print(f"   • Time range: {summary['time_range']}")
    print(f"   • System health: {summary['health_status'].upper()}")
    print(f"   • Error rate: {summary['error_rate']}%")
    print(f"   • Most active source: {summary['most_active_source']}")
    
    # Error Analysis
    error_analysis = analysis_report['error_analysis']
    print(f"\n🚨 ERROR ANALYSIS")
    print(f"   • Total errors: {error_analysis['total_errors']}")
    print(f"   • Error rate: {error_analysis['error_rate']:.2f}%")
    print(f"   • Severity score: {error_analysis['severity_score']:.2f}")
    if error_analysis['errors_by_level']:
        print(f"   • Errors by level: {dict(error_analysis['errors_by_level'])}")
    if error_analysis['errors_by_source']:
        print(f"   • Top error sources: {dict(list(error_analysis['errors_by_source'].items())[:3])}")
    
    # Performance Analysis
    perf_analysis = analysis_report['performance_analysis']
    print(f"\n⚡ PERFORMANCE ANALYSIS")
    print(f"   • Performance score: {perf_analysis.get('performance_score', 0):.1f}/100")
    if perf_analysis.get('response_time_distribution'):
        rt_dist = perf_analysis['response_time_distribution']
        print(f"   • Average response time: {rt_dist['average']:.1f}ms")
        print(f"   • 95th percentile: {rt_dist['p95']:.1f}ms")
    slow_ops = len(perf_analysis.get('slow_operations', []))
    if slow_ops > 0:
        print(f"   • Slow operations detected: {slow_ops}")
    
    # Security Analysis
    security_analysis = analysis_report['security_analysis']
    print(f"\n🔒 SECURITY ANALYSIS")
    print(f"   • Security score: {security_analysis['security_score']}/100")
    print(f"   • Failed logins: {security_analysis['failed_logins']}")
    print(f"   • Threats detected: {len(security_analysis['threats_detected'])}")
    
    # Reliability Score
    reliability = analysis_report['reliability_score']
    print(f"\n📊 RELIABILITY SCORE")
    print(f"   • Overall score: {reliability['score']:.1f}/100 (Grade: {reliability['grade']})")
    
    # Anomalies
    anomalies = analysis_report['anomaly_analysis']
    if anomalies:
        print(f"\n⚠️  ANOMALIES DETECTED")
        for anomaly in anomalies[:3]:  # Show top 3
            print(f"   • {anomaly['type']}: {anomaly.get('pattern', anomaly.get('source', 'Unknown'))}")
    
    # Recommendations
    recommendations = analysis_report['recommendations']
    print(f"\n💡 RECOMMENDATIONS")
    for i, rec in enumerate(recommendations[:5], 1):  # Show top 5
        print(f"   {i}. {rec}")
    
    # Export report option
    export_choice = input(f"\n💾 Export detailed report to file? (y/n): ").lower().strip()
    if export_choice == 'y':
        try:
            report_file = dashboard.export_analysis_report(analysis_report)
            print(f"✅ Report exported to: {report_file}")
        except Exception as e:
            print(f"❌ Failed to export report: {e}")
    
    print(f"\n🎯 Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()