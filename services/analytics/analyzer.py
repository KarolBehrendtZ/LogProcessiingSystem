import re
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple
import statistics
from structured_logger import create_logger_from_env, performance_monitor, log_context

# Initialize structured logger
logger = create_logger_from_env("analytics", "analyzer")

@performance_monitor(logger, "analyze_error_frequency")
def analyze_error_frequency(logs: List[Dict]) -> Dict[str, Any]:
    """
    Advanced error frequency analysis with time-based patterns.
    
    Args:
        logs: List of log dictionaries with keys: level, message, timestamp, source
    
    Returns:
        Dict containing comprehensive error analysis
    """
    with log_context(operation="analyze_error_frequency", log_count=len(logs)):
        logger.info("Starting error frequency analysis")
        
        error_analysis = {
            'total_errors': 0,
            'error_rate': 0.0,
            'errors_by_level': defaultdict(int),
            'errors_by_source': defaultdict(int),
            'error_patterns': [],
            'time_distribution': defaultdict(int),
            'severity_score': 0
        }
        
        total_logs = len(logs)
        if total_logs == 0:
            logger.warning("No logs provided for error frequency analysis")
            return error_analysis
        
        logger.debug(f"Processing {total_logs} logs for error analysis")
        
        # Define severity weights
        severity_weights = {
            'fatal': 10,
            'error': 5,
            'warn': 2,
            'info': 1,
            'debug': 0.5
        }
        
        total_severity = 0
    
    for log in logs:
        if isinstance(log, dict):
            level = log.get('level', '').lower()
            message = log.get('message', '')
            source = log.get('source', 'unknown')
            timestamp = log.get('timestamp', '')
            
            # Count errors and warnings
            if level in ['error', 'fatal', 'warn']:
                error_analysis['total_errors'] += 1
                error_analysis['errors_by_level'][level] += 1
                error_analysis['errors_by_source'][source] += 1
                
                # Extract error patterns
                error_pattern = extract_error_pattern(message)
                if error_pattern:
                    error_analysis['error_patterns'].append({
                        'pattern': error_pattern,
                        'message': message,
                        'level': level,
                        'source': source,
                        'timestamp': timestamp
                    })
                
                # Time distribution analysis
                if timestamp:
                    hour = extract_hour_from_timestamp(timestamp)
                    if hour is not None:
                        error_analysis['time_distribution'][hour] += 1
            
            # Calculate severity score
            weight = severity_weights.get(level, 1)
            total_severity += weight
    
    # Calculate metrics
    error_analysis['error_rate'] = (error_analysis['total_errors'] / total_logs) * 100
    error_analysis['severity_score'] = total_severity / total_logs if total_logs > 0 else 0
    
    # Convert defaultdicts to regular dicts for JSON serialization
    error_analysis['errors_by_level'] = dict(error_analysis['errors_by_level'])
    error_analysis['errors_by_source'] = dict(error_analysis['errors_by_source'])
    error_analysis['time_distribution'] = dict(error_analysis['time_distribution'])
    
    return error_analysis

def detect_patterns(logs: List[Dict]) -> Dict[str, Any]:
    """
    Advanced pattern detection using multiple algorithms.
    
    Args:
        logs: List of log dictionaries or strings
    
    Returns:
        Dict with comprehensive pattern analysis
    """
    pattern_analysis = {
        'frequent_terms': {},
        'error_signatures': [],
        'anomalous_patterns': [],
        'temporal_patterns': {},
        'source_patterns': {},
        'message_clusters': []
    }
    
    messages = []
    timestamps = []
    sources = []
    levels = []
    
    # Extract data for analysis
    for log in logs:
        if isinstance(log, dict):
            message = log.get('message', '')
            timestamp = log.get('timestamp', '')
            source = log.get('source', '')
            level = log.get('level', '')
            
            messages.append(message)
            timestamps.append(timestamp)
            sources.append(source)
            levels.append(level)
        elif isinstance(log, str):
            messages.append(log)
    
    # Frequent terms analysis
    pattern_analysis['frequent_terms'] = analyze_frequent_terms(messages)
    
    # Error signature detection
    pattern_analysis['error_signatures'] = detect_error_signatures(logs)
    
    # Anomaly detection
    pattern_analysis['anomalous_patterns'] = detect_anomalies(logs)
    
    # Temporal pattern analysis
    pattern_analysis['temporal_patterns'] = analyze_temporal_patterns(timestamps, levels)
    
    # Source pattern analysis
    pattern_analysis['source_patterns'] = analyze_source_patterns(sources, levels)
    
    # Message clustering
    pattern_analysis['message_clusters'] = cluster_similar_messages(messages)
    
    return pattern_analysis

def analyze_log_trends(logs: List[Dict]) -> Dict[str, Any]:
    """
    Advanced trend analysis with statistical insights.
    
    Args:
        logs: List of structured log dictionaries
    
    Returns:
        Dict with comprehensive trend analysis
    """
    trends = {
        'total_logs': len(logs),
        'by_level': defaultdict(int),
        'by_source': defaultdict(int),
        'hourly_distribution': defaultdict(int),
        'daily_distribution': defaultdict(int),
        'error_trend': [],
        'volume_statistics': {},
        'performance_indicators': {}
    }
    
    if not logs:
        return trends
    
    # Time series data for trend analysis
    error_counts_by_hour = defaultdict(int)
    log_counts_by_hour = defaultdict(int)
    response_times = []
    
    for log in logs:
        if isinstance(log, dict):
            level = log.get('level', 'unknown')
            source = log.get('source', 'unknown')
            timestamp = log.get('timestamp', '')
            message = log.get('message', '')
            
            # Basic counts
            trends['by_level'][level] += 1
            trends['by_source'][source] += 1
            
            # Time-based analysis
            if timestamp:
                hour, day = extract_time_components(timestamp)
                if hour is not None:
                    trends['hourly_distribution'][hour] += 1
                    log_counts_by_hour[hour] += 1
                    
                    if level in ['error', 'fatal']:
                        error_counts_by_hour[hour] += 1
                
                if day:
                    trends['daily_distribution'][day] += 1
            
            # Extract performance metrics
            response_time = extract_response_time(message)
            if response_time:
                response_times.append(response_time)
    
    # Calculate error trend
    for hour in sorted(log_counts_by_hour.keys()):
        error_rate = (error_counts_by_hour[hour] / log_counts_by_hour[hour]) * 100 if log_counts_by_hour[hour] > 0 else 0
        trends['error_trend'].append({
            'hour': hour,
            'total_logs': log_counts_by_hour[hour],
            'error_count': error_counts_by_hour[hour],
            'error_rate': error_rate
        })
    
    # Volume statistics
    hourly_volumes = list(log_counts_by_hour.values())
    if hourly_volumes:
        trends['volume_statistics'] = {
            'mean': statistics.mean(hourly_volumes),
            'median': statistics.median(hourly_volumes),
            'std_dev': statistics.stdev(hourly_volumes) if len(hourly_volumes) > 1 else 0,
            'min': min(hourly_volumes),
            'max': max(hourly_volumes)
        }
    
    # Performance indicators
    if response_times:
        trends['performance_indicators'] = {
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times),
            'slow_requests': len([rt for rt in response_times if rt > 1000])  # > 1 second
        }
    
    # Convert defaultdicts to regular dicts
    trends['by_level'] = dict(trends['by_level'])
    trends['by_source'] = dict(trends['by_source'])
    trends['hourly_distribution'] = dict(trends['hourly_distribution'])
    trends['daily_distribution'] = dict(trends['daily_distribution'])
    
    return trends

def detect_anomalies(logs: List[Dict], threshold_multiplier: float = 2.0) -> List[Dict]:
    """
    Detect anomalous patterns in log data.
    
    Args:
        logs: List of log dictionaries
        threshold_multiplier: Multiplier for standard deviation threshold
    
    Returns:
        List of detected anomalies
    """
    anomalies = []
    
    # Group logs by source and level
    source_level_counts = defaultdict(lambda: defaultdict(int))
    total_counts = defaultdict(int)
    
    for log in logs:
        if isinstance(log, dict):
            source = log.get('source', 'unknown')
            level = log.get('level', 'unknown')
            source_level_counts[source][level] += 1
            total_counts[source] += 1
    
    # Detect sources with unusual error rates
    for source, level_counts in source_level_counts.items():
        total = total_counts[source]
        error_count = level_counts.get('error', 0) + level_counts.get('fatal', 0)
        error_rate = (error_count / total) * 100 if total > 0 else 0
        
        # If error rate is unusually high (> 20%), flag as anomaly
        if error_rate > 20 and total > 5:  # Only consider sources with meaningful volume
            anomalies.append({
                'type': 'high_error_rate',
                'source': source,
                'error_rate': error_rate,
                'total_logs': total,
                'error_count': error_count,
                'severity': 'high' if error_rate > 50 else 'medium'
            })
    
    # Detect sudden spikes in specific error messages
    error_messages = defaultdict(int)
    for log in logs:
        if isinstance(log, dict) and log.get('level') in ['error', 'fatal']:
            message_signature = extract_error_pattern(log.get('message', ''))
            if message_signature:
                error_messages[message_signature] += 1
    
    # Flag messages that appear unusually frequently
    if error_messages:
        counts = list(error_messages.values())
        if len(counts) > 1:
            mean_count = statistics.mean(counts)
            std_dev = statistics.stdev(counts) if len(counts) > 1 else 0
            threshold = mean_count + (threshold_multiplier * std_dev)
            
            for message, count in error_messages.items():
                if count > threshold and count > 3:  # At least 3 occurrences
                    anomalies.append({
                        'type': 'frequent_error_pattern',
                        'pattern': message,
                        'count': count,
                        'threshold': threshold,
                        'severity': 'high' if count > threshold * 2 else 'medium'
                    })
    
    return anomalies

# Helper functions
def extract_error_pattern(message: str) -> str:
    """Extract a generalized pattern from an error message."""
    if not message:
        return ""
    
    # Remove specific identifiers (IDs, timestamps, IP addresses, etc.)
    pattern = re.sub(r'\b\d+\b', 'NUM', message)  # Replace numbers
    pattern = re.sub(r'\b[0-9a-fA-F]{8,}\b', 'ID', pattern)  # Replace hex IDs
    pattern = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', pattern)  # Replace IPs
    pattern = re.sub(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', 'TIMESTAMP', pattern)  # Replace timestamps
    pattern = re.sub(r'/[a-zA-Z0-9/_-]+', '/PATH', pattern)  # Replace file paths
    
    return pattern.strip()

def extract_hour_from_timestamp(timestamp: str) -> int:
    """Extract hour from timestamp string."""
    try:
        if 'T' in timestamp:
            time_part = timestamp.split('T')[1]
            hour = int(time_part.split(':')[0])
            return hour
    except (ValueError, IndexError):
        pass
    return None

def extract_time_components(timestamp: str) -> Tuple[int, str]:
    """Extract hour and day from timestamp."""
    try:
        if 'T' in timestamp:
            date_part, time_part = timestamp.split('T')
            hour = int(time_part.split(':')[0])
            return hour, date_part
    except (ValueError, IndexError):
        pass
    return None, None

def extract_response_time(message: str) -> float:
    """Extract response time from log message if present."""
    # Look for patterns like "took 1234ms" or "duration: 5.67s"
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
                # Convert to milliseconds if needed
                if 'duration' in pattern or pattern.endswith('s'):
                    value *= 1000
                return value
            except ValueError:
                continue
    
    return None

def analyze_frequent_terms(messages: List[str]) -> Dict[str, int]:
    """Analyze frequent terms in log messages."""
    # Extract meaningful terms (filter out common words)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'being'}
    
    all_words = []
    for message in messages:
        # Clean and tokenize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', message.lower())
        filtered_words = [word for word in words if word not in stop_words]
        all_words.extend(filtered_words)
    
    # Return top 20 most frequent terms
    counter = Counter(all_words)
    return dict(counter.most_common(20))

def detect_error_signatures(logs: List[Dict]) -> List[Dict]:
    """Detect common error signatures."""
    error_patterns = defaultdict(list)
    
    for log in logs:
        if isinstance(log, dict) and log.get('level') in ['error', 'fatal']:
            pattern = extract_error_pattern(log.get('message', ''))
            if pattern:
                error_patterns[pattern].append(log)
    
    # Return patterns that occur multiple times
    signatures = []
    for pattern, occurrences in error_patterns.items():
        if len(occurrences) > 1:
            sources = list(set(log.get('source', 'unknown') for log in occurrences))
            signatures.append({
                'pattern': pattern,
                'count': len(occurrences),
                'sources': sources,
                'first_seen': min(log.get('timestamp', '') for log in occurrences),
                'last_seen': max(log.get('timestamp', '') for log in occurrences)
            })
    
    return sorted(signatures, key=lambda x: x['count'], reverse=True)

def analyze_temporal_patterns(timestamps: List[str], levels: List[str]) -> Dict:
    """Analyze temporal patterns in logs."""
    hour_level_counts = defaultdict(lambda: defaultdict(int))
    
    for timestamp, level in zip(timestamps, levels):
        hour = extract_hour_from_timestamp(timestamp)
        if hour is not None:
            hour_level_counts[hour][level] += 1
    
    return dict(hour_level_counts)

def analyze_source_patterns(sources: List[str], levels: List[str]) -> Dict:
    """Analyze patterns by source."""
    source_level_counts = defaultdict(lambda: defaultdict(int))
    
    for source, level in zip(sources, levels):
        source_level_counts[source][level] += 1
    
    return dict(source_level_counts)

def cluster_similar_messages(messages: List[str]) -> List[Dict]:
    """Cluster similar messages together."""
    # Simple clustering based on common words
    clusters = defaultdict(list)
    
    for message in messages:
        # Create a signature based on key words
        words = re.findall(r'\b[a-zA-Z]{4,}\b', message.lower())
        signature = ' '.join(sorted(set(words))[:3])  # Use top 3 unique words as signature
        clusters[signature].append(message)
    
    # Return clusters with more than one message
    result = []
    for signature, cluster_messages in clusters.items():
        if len(cluster_messages) > 1:
            result.append({
                'signature': signature,
                'count': len(cluster_messages),
                'sample_messages': cluster_messages[:3]  # Show first 3 as samples
            })
    
    return sorted(result, key=lambda x: x['count'], reverse=True)[:10]  # Top 10 clusters