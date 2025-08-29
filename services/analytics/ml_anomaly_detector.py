"""
Machine Learning-based Anomaly Detection for Log Analysis
Uses statistical methods and pattern recognition to detect unusual behaviors
"""

import numpy as np
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple
import math

class MLAnomalyDetector:
    """Machine learning-based anomaly detector for log data."""
    
    def __init__(self):
        self.baseline_patterns = {}
        self.feature_weights = {
            'error_rate': 0.3,
            'message_entropy': 0.2,
            'temporal_pattern': 0.2,
            'source_diversity': 0.15,
            'volume_variance': 0.15
        }
        
    def detect_anomalies(self, logs: List[Dict], historical_data: List[Dict] = None) -> List[Dict]:
        """
        Detect anomalies using multiple ML-inspired techniques.
        
        Args:
            logs: Current log data to analyze
            historical_data: Historical log data for baseline (optional)
        
        Returns:
            List of detected anomalies with confidence scores
        """
        anomalies = []
        
        if historical_data:
            self.build_baseline(historical_data)
        
        # Extract features from current logs
        current_features = self.extract_features(logs)
        
        # Run different anomaly detection algorithms
        anomalies.extend(self.detect_statistical_anomalies(logs, current_features))
        anomalies.extend(self.detect_pattern_anomalies(logs, current_features))
        anomalies.extend(self.detect_temporal_anomalies(logs))
        anomalies.extend(self.detect_clustering_anomalies(logs))
        
        # Sort by confidence score
        anomalies.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return self.merge_similar_anomalies(anomalies)
    
    def build_baseline(self, historical_data: List[Dict]):
        """Build baseline patterns from historical data."""
        self.baseline_patterns = {
            'error_rate': self.calculate_baseline_error_rate(historical_data),
            'message_patterns': self.extract_message_patterns(historical_data),
            'temporal_patterns': self.extract_temporal_patterns(historical_data),
            'source_patterns': self.extract_source_patterns(historical_data),
            'volume_patterns': self.extract_volume_patterns(historical_data)
        }
    
    def extract_features(self, logs: List[Dict]) -> Dict[str, float]:
        """Extract numerical features from log data for ML analysis."""
        if not logs:
            return {}
        
        features = {}
        
        # Error rate feature
        error_count = sum(1 for log in logs if log.get('level', '').lower() in ['error', 'fatal'])
        features['error_rate'] = error_count / len(logs) if logs else 0
        
        # Message entropy (diversity of messages)
        messages = [log.get('message', '') for log in logs]
        features['message_entropy'] = self.calculate_entropy(messages)
        
        # Temporal distribution variance
        timestamps = [log.get('timestamp', '') for log in logs]
        features['temporal_variance'] = self.calculate_temporal_variance(timestamps)
        
        # Source diversity
        sources = [log.get('source', '') for log in logs]
        unique_sources = len(set(sources))
        features['source_diversity'] = unique_sources / len(logs) if logs else 0
        
        # Volume features
        features['total_volume'] = len(logs)
        features['volume_variance'] = self.calculate_volume_variance(logs)
        
        # Level distribution
        levels = [log.get('level', '').lower() for log in logs]
        level_counts = Counter(levels)
        for level in ['debug', 'info', 'warn', 'error', 'fatal']:
            features[f'level_{level}_ratio'] = level_counts.get(level, 0) / len(logs) if logs else 0
        
        return features
    
    def detect_statistical_anomalies(self, logs: List[Dict], features: Dict[str, float]) -> List[Dict]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        # Z-score based detection
        if self.baseline_patterns:
            for feature_name, current_value in features.items():
                if feature_name in self.baseline_patterns.get('statistical_baseline', {}):
                    baseline = self.baseline_patterns['statistical_baseline'][feature_name]
                    z_score = self.calculate_z_score(current_value, baseline['mean'], baseline['std'])
                    
                    if abs(z_score) > 2.5:  # 2.5 sigma threshold
                        anomalies.append({
                            'type': 'statistical_anomaly',
                            'feature': feature_name,
                            'current_value': current_value,
                            'expected_value': baseline['mean'],
                            'z_score': z_score,
                            'confidence': min(abs(z_score) / 3.0, 1.0),
                            'severity': 'high' if abs(z_score) > 3.0 else 'medium',
                            'description': f"Statistical anomaly in {feature_name}: {current_value:.3f} (expected: {baseline['mean']:.3f})"
                        })
        
        return anomalies
    
    def detect_pattern_anomalies(self, logs: List[Dict], features: Dict[str, float]) -> List[Dict]:
        """Detect anomalies in message patterns."""
        anomalies = []
        
        # Analyze message patterns
        message_patterns = {}
        for log in logs:
            message = log.get('message', '')
            pattern = self.extract_message_signature(message)
            message_patterns[pattern] = message_patterns.get(pattern, 0) + 1
        
        # Find unusual patterns
        if message_patterns:
            pattern_counts = list(message_patterns.values())
            mean_count = np.mean(pattern_counts)
            std_count = np.std(pattern_counts)
            
            for pattern, count in message_patterns.items():
                if std_count > 0:
                    z_score = (count - mean_count) / std_count
                    
                    # Detect both unusually high and low frequency patterns
                    if z_score > 2.0:  # Unusually frequent
                        anomalies.append({
                            'type': 'frequent_pattern_anomaly',
                            'pattern': pattern,
                            'count': count,
                            'expected_count': mean_count,
                            'confidence': min(z_score / 3.0, 1.0),
                            'severity': 'medium',
                            'description': f"Unusually frequent pattern: '{pattern}' appeared {count} times"
                        })
                    elif z_score < -2.0 and count == 1:  # Unique/rare patterns
                        anomalies.append({
                            'type': 'rare_pattern_anomaly',
                            'pattern': pattern,
                            'count': count,
                            'confidence': 0.6,
                            'severity': 'low',
                            'description': f"Rare pattern detected: '{pattern}'"
                        })
        
        return anomalies
    
    def detect_temporal_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Detect temporal anomalies in log patterns."""
        anomalies = []
        
        # Group logs by time windows
        time_windows = self.group_logs_by_time_window(logs, window_minutes=10)
        
        if len(time_windows) < 3:
            return anomalies  # Need at least 3 windows for analysis
        
        # Analyze volume per time window
        volumes = [len(window_logs) for window_logs in time_windows.values()]
        mean_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        if std_volume > 0:
            for timestamp, window_logs in time_windows.items():
                volume = len(window_logs)
                z_score = (volume - mean_volume) / std_volume
                
                if abs(z_score) > 2.0:
                    anomaly_type = 'volume_spike' if z_score > 0 else 'volume_drop'
                    anomalies.append({
                        'type': f'temporal_{anomaly_type}',
                        'timestamp': timestamp,
                        'volume': volume,
                        'expected_volume': mean_volume,
                        'z_score': z_score,
                        'confidence': min(abs(z_score) / 3.0, 1.0),
                        'severity': 'high' if abs(z_score) > 3.0 else 'medium',
                        'description': f"Temporal {anomaly_type}: {volume} logs in window (expected: {mean_volume:.1f})"
                    })
        
        # Analyze error rate per time window
        error_rates = []
        for window_logs in time_windows.values():
            error_count = sum(1 for log in window_logs if log.get('level', '').lower() in ['error', 'fatal'])
            error_rate = error_count / len(window_logs) if window_logs else 0
            error_rates.append(error_rate)
        
        mean_error_rate = np.mean(error_rates)
        std_error_rate = np.std(error_rates)
        
        if std_error_rate > 0:
            for (timestamp, window_logs), error_rate in zip(time_windows.items(), error_rates):
                z_score = (error_rate - mean_error_rate) / std_error_rate
                
                if z_score > 2.0:  # Only flag high error rates as anomalies
                    anomalies.append({
                        'type': 'temporal_error_spike',
                        'timestamp': timestamp,
                        'error_rate': error_rate,
                        'expected_error_rate': mean_error_rate,
                        'z_score': z_score,
                        'confidence': min(z_score / 3.0, 1.0),
                        'severity': 'high',
                        'description': f"Error rate spike: {error_rate:.1%} in window (expected: {mean_error_rate:.1%})"
                    })
        
        return anomalies
    
    def detect_clustering_anomalies(self, logs: List[Dict]) -> List[Dict]:
        """Detect anomalies using clustering-like approaches."""
        anomalies = []
        
        # Group logs by source and analyze
        source_groups = defaultdict(list)
        for log in logs:
            source = log.get('source', 'unknown')
            source_groups[source].append(log)
        
        # Analyze each source group
        for source, source_logs in source_groups.items():
            if len(source_logs) < 5:  # Skip sources with too few logs
                continue
            
            # Check for unusual error clustering
            error_logs = [log for log in source_logs if log.get('level', '').lower() in ['error', 'fatal']]
            
            if error_logs:
                # Check if errors are clustered in time
                error_timestamps = [log.get('timestamp', '') for log in error_logs]
                time_clustering_score = self.calculate_time_clustering_score(error_timestamps)
                
                if time_clustering_score > 0.7:  # High clustering threshold
                    anomalies.append({
                        'type': 'error_time_clustering',
                        'source': source,
                        'error_count': len(error_logs),
                        'clustering_score': time_clustering_score,
                        'confidence': time_clustering_score,
                        'severity': 'high',
                        'description': f"Error clustering detected in {source}: {len(error_logs)} errors clustered in time"
                    })
        
        return anomalies
    
    def merge_similar_anomalies(self, anomalies: List[Dict]) -> List[Dict]:
        """Merge similar anomalies to reduce noise."""
        merged = []
        used_indices = set()
        
        for i, anomaly in enumerate(anomalies):
            if i in used_indices:
                continue
            
            similar_anomalies = [anomaly]
            
            for j, other_anomaly in enumerate(anomalies[i+1:], i+1):
                if j in used_indices:
                    continue
                
                if self.are_similar_anomalies(anomaly, other_anomaly):
                    similar_anomalies.append(other_anomaly)
                    used_indices.add(j)
            
            if len(similar_anomalies) > 1:
                # Merge similar anomalies
                merged_anomaly = self.merge_anomaly_group(similar_anomalies)
                merged.append(merged_anomaly)
            else:
                merged.append(anomaly)
            
            used_indices.add(i)
        
        return merged
    
    # Helper methods
    def calculate_entropy(self, messages: List[str]) -> float:
        """Calculate Shannon entropy of message diversity."""
        if not messages:
            return 0
        
        # Create message signatures
        signatures = [self.extract_message_signature(msg) for msg in messages]
        signature_counts = Counter(signatures)
        
        total = len(signatures)
        entropy = 0
        
        for count in signature_counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def extract_message_signature(self, message: str) -> str:
        """Extract a signature pattern from a message."""
        import re
        
        # Normalize the message
        signature = message.lower()
        
        # Replace numbers with placeholder
        signature = re.sub(r'\d+', 'NUM', signature)
        
        # Replace common variable parts
        signature = re.sub(r'\b[a-f0-9]{8,}\b', 'HASH', signature)  # Hex values
        signature = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', signature)  # IP addresses
        signature = re.sub(r'/[a-zA-Z0-9/_-]+', '/PATH', signature)  # File paths
        
        # Extract key words (remove common words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', signature)
        key_words = [w for w in words if w not in {'the', 'and', 'for', 'with', 'from', 'that', 'this'}]
        
        return ' '.join(key_words[:5])  # Use top 5 key words
    
    def calculate_temporal_variance(self, timestamps: List[str]) -> float:
        """Calculate variance in temporal distribution."""
        if len(timestamps) < 2:
            return 0
        
        # Convert timestamps to hour buckets
        hour_counts = defaultdict(int)
        for timestamp in timestamps:
            try:
                if 'T' in timestamp:
                    hour = timestamp.split('T')[1].split(':')[0]
                    hour_counts[hour] += 1
            except (IndexError, ValueError):
                continue
        
        if not hour_counts:
            return 0
        
        counts = list(hour_counts.values())
        return np.var(counts) if len(counts) > 1 else 0
    
    def calculate_volume_variance(self, logs: List[Dict]) -> float:
        """Calculate variance in log volume."""
        # Group by minute and calculate variance
        minute_counts = defaultdict(int)
        
        for log in logs:
            timestamp = log.get('timestamp', '')
            try:
                if 'T' in timestamp:
                    minute_key = timestamp.split('T')[1][:5]  # HH:MM
                    minute_counts[minute_key] += 1
            except (IndexError, ValueError):
                continue
        
        if not minute_counts:
            return 0
        
        counts = list(minute_counts.values())
        return np.var(counts) if len(counts) > 1 else 0
    
    def calculate_z_score(self, value: float, mean: float, std: float) -> float:
        """Calculate Z-score for anomaly detection."""
        if std == 0:
            return 0
        return (value - mean) / std
    
    def group_logs_by_time_window(self, logs: List[Dict], window_minutes: int = 10) -> Dict[str, List[Dict]]:
        """Group logs into time windows."""
        windows = defaultdict(list)
        
        for log in logs:
            timestamp = log.get('timestamp', '')
            try:
                if 'T' in timestamp:
                    # Round to nearest time window
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    rounded_minute = (dt.minute // window_minutes) * window_minutes
                    window_key = dt.replace(minute=rounded_minute, second=0, microsecond=0).isoformat()
                    windows[window_key].append(log)
            except (ValueError, AttributeError):
                continue
        
        return dict(windows)
    
    def calculate_time_clustering_score(self, timestamps: List[str]) -> float:
        """Calculate how clustered in time the timestamps are."""
        if len(timestamps) < 2:
            return 0
        
        try:
            # Convert to datetime objects
            dts = []
            for ts in timestamps:
                if 'T' in ts:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    dts.append(dt)
            
            if len(dts) < 2:
                return 0
            
            # Calculate time differences
            dts.sort()
            diffs = [(dts[i+1] - dts[i]).total_seconds() for i in range(len(dts)-1)]
            
            # If most time differences are small, it's clustered
            mean_diff = np.mean(diffs)
            std_diff = np.std(diffs)
            
            if mean_diff == 0:
                return 1.0
            
            # Score based on coefficient of variation (lower = more clustered)
            cv = std_diff / mean_diff if mean_diff > 0 else 0
            clustering_score = max(0, 1 - (cv / 2))  # Normalize
            
            return clustering_score
            
        except Exception:
            return 0
    
    def are_similar_anomalies(self, anomaly1: Dict, anomaly2: Dict) -> bool:
        """Check if two anomalies are similar and should be merged."""
        # Same type
        if anomaly1.get('type') != anomaly2.get('type'):
            return False
        
        # Similar source/pattern
        if anomaly1.get('source') and anomaly2.get('source'):
            return anomaly1['source'] == anomaly2['source']
        
        if anomaly1.get('pattern') and anomaly2.get('pattern'):
            return anomaly1['pattern'] == anomaly2['pattern']
        
        return False
    
    def merge_anomaly_group(self, anomalies: List[Dict]) -> Dict:
        """Merge a group of similar anomalies."""
        merged = anomalies[0].copy()
        
        # Combine counts and confidence scores
        if 'count' in merged:
            merged['count'] = sum(a.get('count', 1) for a in anomalies)
        
        confidences = [a.get('confidence', 0) for a in anomalies]
        merged['confidence'] = max(confidences)
        
        # Update description to reflect merger
        merged['description'] += f" (merged from {len(anomalies)} similar anomalies)"
        merged['merged_count'] = len(anomalies)
        
        return merged
