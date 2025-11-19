"""
Base Labeler Class - Labels dataset records
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class BaseLabeler(ABC):
    """Abstract base class for data labelers"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize labeler"""
        self.config = config or {}
        self.labeled_data = []
        self.labeling_stats = {}
    
    @abstractmethod
    def label(self, records: List[Dict]) -> List[Dict]:
        """Label records"""
        pass
    
    def get_labeled_data(self) -> List[Dict]:
        """Get labeled data"""
        return self.labeled_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get labeling statistics"""
        return self.labeling_stats

class BugSeverityLabeler(BaseLabeler):
    """Labels bugs by severity"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize bug severity labeler"""
        super().__init__(config)
    
    def label(self, records: List[Dict]) -> List[Dict]:
        """Label bugs by severity"""
        logger.info(f"Labeling {len(records)} bug records")
        
        labeled = []
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for record in records:
            labeled_record = record.copy()
            
            # Determine severity
            severity = self._determine_severity(record)
            labeled_record["severity"] = severity
            severity_counts[severity] += 1
            
            labeled.append(labeled_record)
        
        self.labeled_data = labeled
        self.labeling_stats = severity_counts
        
        logger.info(f"Labeled {len(labeled)} records")
        return labeled
    
    @staticmethod
    def _determine_severity(record: Dict) -> str:
        """Determine bug severity"""
        
        # Check existing severity field
        if "severity" in record:
            return record["severity"]
        
        # Heuristics for severity
        description = (record.get("description", "") or record.get("title", "")).lower()
        
        critical_keywords = ["crash", "exception", "fatal", "panic", "deadlock"]
        high_keywords = ["regression", "data loss", "security", "vulnerability"]
        
        for keyword in critical_keywords:
            if keyword in description:
                return "critical"
        
        for keyword in high_keywords:
            if keyword in description:
                return "high"
        
        if len(description) > 200:
            return "medium"
        
        return "low"

class CodeComplexityLabeler(BaseLabeler):
    """Labels code by complexity"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize code complexity labeler"""
        super().__init__(config)
    
    def label(self, records: List[Dict]) -> List[Dict]:
        """Label code by complexity"""
        logger.info(f"Labeling {len(records)} code records")
        
        labeled = []
        complexity_counts = {"simple": 0, "moderate": 0, "complex": 0, "very_complex": 0}
        
        for record in records:
            labeled_record = record.copy()
            
            # Calculate complexity
            complexity = self._calculate_complexity(record)
            labeled_record["complexity_label"] = complexity
            complexity_counts[complexity] += 1
            
            labeled.append(labeled_record)
        
        self.labeled_data = labeled
        self.labeling_stats = complexity_counts
        
        logger.info(f"Labeled {len(labeled)} records")
        return labeled
    
    @staticmethod
    def _calculate_complexity(record: Dict) -> str:
        """Calculate code complexity"""
        
        complexity_score = 0
        
        # Code length
        if "lines_of_code" in record:
            loc = record["lines_of_code"]
            if isinstance(loc, (int, float)):
                complexity_score += min(loc / 50, 3)
        
        # Cyclomatic complexity
        if "cyclomatic_complexity" in record:
            cc = record["cyclomatic_complexity"]
            if isinstance(cc, (int, float)):
                complexity_score += cc / 5
        
        # Parameters
        if "parameters" in record:
            params = record["parameters"]
            if isinstance(params, (int, float)):
                complexity_score += params / 3
        
        # Classify
        if complexity_score < 3:
            return "simple"
        elif complexity_score < 6:
            return "moderate"
        elif complexity_score < 10:
            return "complex"
        else:
            return "very_complex"

class FeatureLabelClassifier(BaseLabeler):
    """Classifies features/records by type"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize feature classifier"""
        super().__init__(config)
        self.feature_keywords = {
            "feature_request": ["feature", "enhancement", "improvement", "new functionality"],
            "bug_fix": ["bug", "fix", "broken", "error", "issue", "crash"],
            "refactoring": ["refactor", "cleanup", "restructure", "rewrite"],
            "documentation": ["doc", "documentation", "readme", "comment", "javadoc"],
            "performance": ["performance", "optimization", "speed", "slow", "fast"],
            "security": ["security", "vulnerability", "cve", "xss", "injection"],
            "testing": ["test", "unittest", "integration test", "coverage"],
        }
    
    def label(self, records: List[Dict]) -> List[Dict]:
        """Classify records by feature type"""
        logger.info(f"Classifying {len(records)} records")
        
        labeled = []
        type_counts = {ftype: 0 for ftype in self.feature_keywords.keys()}
        type_counts["other"] = 0
        
        for record in records:
            labeled_record = record.copy()
            
            # Classify
            feature_type = self._classify(record)
            labeled_record["feature_type"] = feature_type
            type_counts[feature_type] += 1
            
            labeled.append(labeled_record)
        
        self.labeled_data = labeled
        self.labeling_stats = type_counts
        
        logger.info(f"Classified {len(labeled)} records")
        return labeled
    
    def _classify(self, record: Dict) -> str:
        """Classify single record"""
        
        # Combine relevant fields
        text = ""
        for field in ["title", "description", "message", "body"]:
            if field in record:
                text += " " + str(record.get(field, "")).lower()
        
        text = text.lower()
        
        # Match against keywords
        for feature_type, keywords in self.feature_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return feature_type
        
        return "other"

class MultiLabelClassifier(BaseLabeler):
    """Assigns multiple labels to records"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize multi-label classifier"""
        super().__init__(config)
    
    def label(self, records: List[Dict]) -> List[Dict]:
        """Assign multiple labels"""
        logger.info(f"Multi-labeling {len(records)} records")
        
        labeled = []
        label_counts = {}
        
        for record in records:
            labeled_record = record.copy()
            
            # Assign labels
            labels = self._assign_labels(record)
            labeled_record["labels"] = labels
            
            # Count labels
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
            
            labeled.append(labeled_record)
        
        self.labeled_data = labeled
        self.labeling_stats = label_counts
        
        logger.info(f"Multi-labeled {len(labeled)} records")
        return labeled
    
    @staticmethod
    def _assign_labels(record: Dict) -> List[str]:
        """Assign multiple labels to record"""
        labels = []
        
        # Add type-based labels
        record_type = record.get("type", "").lower()
        if "bug" in record_type:
            labels.append("buggy")
        elif "feature" in record_type:
            labels.append("feature")
        
        # Add severity-based labels
        severity = record.get("severity", "").lower()
        if severity in ["critical", "high"]:
            labels.append("important")
        
        # Add complexity-based labels
        if "complexity_label" in record:
            complexity = record["complexity_label"]
            if complexity in ["complex", "very_complex"]:
                labels.append("complex")
        
        # Add language label
        if "language" in record:
            labels.append(f"lang_{record['language']}")
        
        return labels if labels else ["unclassified"]
