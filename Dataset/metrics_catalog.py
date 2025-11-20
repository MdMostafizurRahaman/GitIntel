"""
Comprehensive Metrics Catalog
Lists all available metrics that can be extracted from source code
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class MetricsCatalog:
    """Complete catalog of all available metrics"""
    
    # Size Metrics
    SIZE_METRICS = {
        'loc': {
            'name': 'Lines of Code',
            'description': 'Total lines of code (excluding comments and blank lines)',
            'type': 'integer',
            'category': 'size'
        },
        'comment_lines': {
            'name': 'Comment Lines',
            'description': 'Number of lines with comments',
            'type': 'integer',
            'category': 'size'
        },
        'blank_lines': {
            'name': 'Blank Lines',
            'description': 'Number of blank lines',
            'type': 'integer',
            'category': 'size'
        },
        'total_lines': {
            'name': 'Total Lines',
            'description': 'Total lines including comments and blanks',
            'type': 'integer',
            'category': 'size'
        },
        'lines_of_code_actual': {
            'name': 'Actual Lines of Code',
            'description': 'LOC minus comment and blank lines',
            'type': 'integer',
            'category': 'size'
        },
    }
    
    # Complexity Metrics
    COMPLEXITY_METRICS = {
        'cyclomatic_complexity': {
            'name': 'Cyclomatic Complexity',
            'description': 'Number of independent paths through code (CC)',
            'type': 'integer',
            'category': 'complexity'
        },
        'max_nesting_depth': {
            'name': 'Maximum Nesting Depth',
            'description': 'Maximum depth of nested blocks',
            'type': 'integer',
            'category': 'complexity'
        },
        'avg_nesting_depth': {
            'name': 'Average Nesting Depth',
            'description': 'Average depth of nested blocks',
            'type': 'float',
            'category': 'complexity'
        },
        'cognitive_complexity': {
            'name': 'Cognitive Complexity',
            'description': 'How difficult is code to understand',
            'type': 'integer',
            'category': 'complexity'
        },
    }
    
    # OOP Metrics (Chidamber & Kemerer)
    CK_METRICS = {
        'wmc': {
            'name': 'Weighted Methods per Class',
            'description': 'Sum of complexities of all methods in a class',
            'type': 'integer',
            'category': 'ck'
        },
        'dit': {
            'name': 'Depth of Inheritance Tree',
            'description': 'Maximum inheritance depth in class hierarchy',
            'type': 'integer',
            'category': 'ck'
        },
        'noc': {
            'name': 'Number of Children',
            'description': 'Number of immediate subclasses',
            'type': 'integer',
            'category': 'ck'
        },
        'cbo': {
            'name': 'Coupling Between Object classes',
            'description': 'Number of classes this class depends on',
            'type': 'integer',
            'category': 'ck'
        },
        'rfc': {
            'name': 'Response For a Class',
            'description': 'Number of methods callable from a class',
            'type': 'integer',
            'category': 'ck'
        },
        'lcom': {
            'name': 'Lack of Cohesion of Methods',
            'description': 'Measure of class cohesion (lower is better)',
            'type': 'float',
            'category': 'ck'
        },
    }
    
    # Structural Metrics
    STRUCTURE_METRICS = {
        'num_classes': {
            'name': 'Number of Classes',
            'description': 'Total number of classes defined',
            'type': 'integer',
            'category': 'structure'
        },
        'num_interfaces': {
            'name': 'Number of Interfaces',
            'description': 'Total number of interfaces defined',
            'type': 'integer',
            'category': 'structure'
        },
        'num_methods': {
            'name': 'Number of Methods',
            'description': 'Total number of methods',
            'type': 'integer',
            'category': 'structure'
        },
        'num_fields': {
            'name': 'Number of Fields',
            'description': 'Total number of instance/class variables',
            'type': 'integer',
            'category': 'structure'
        },
        'num_public_methods': {
            'name': 'Public Methods',
            'description': 'Number of public methods',
            'type': 'integer',
            'category': 'structure'
        },
        'num_private_methods': {
            'name': 'Private Methods',
            'description': 'Number of private methods',
            'type': 'integer',
            'category': 'structure'
        },
        'num_static_methods': {
            'name': 'Static Methods',
            'description': 'Number of static methods',
            'type': 'integer',
            'category': 'structure'
        },
    }
    
    # Quality Metrics
    QUALITY_METRICS = {
        'comment_ratio': {
            'name': 'Comment Ratio',
            'description': 'Percentage of lines that are comments',
            'type': 'float',
            'category': 'quality'
        },
        'has_comments': {
            'name': 'Has Comments',
            'description': 'Whether file contains any comments',
            'type': 'boolean',
            'category': 'quality'
        },
        'avg_method_loc': {
            'name': 'Average Method LOC',
            'description': 'Average lines of code per method',
            'type': 'float',
            'category': 'quality'
        },
        'max_method_loc': {
            'name': 'Maximum Method LOC',
            'description': 'Longest method in lines of code',
            'type': 'integer',
            'category': 'quality'
        },
        'maintainability_index': {
            'name': 'Maintainability Index',
            'description': 'Score from 0-100 indicating code maintainability',
            'type': 'float',
            'category': 'quality'
        },
    }
    
    # Defect/Bug Metrics
    DEFECT_METRICS = {
        'has_defect': {
            'name': 'Has Defect',
            'description': 'Whether file contains known defects',
            'type': 'boolean',
            'category': 'defect'
        },
        'defect_type': {
            'name': 'Defect Type',
            'description': 'Type of defect (bug, vulnerability, etc)',
            'type': 'string',
            'category': 'defect'
        },
        'num_bugs': {
            'name': 'Number of Bugs',
            'description': 'Total bugs found in file',
            'type': 'integer',
            'category': 'defect'
        },
        'bug_severity': {
            'name': 'Bug Severity',
            'description': 'Average severity of bugs (high/medium/low)',
            'type': 'string',
            'category': 'defect'
        },
    }
    
    # Coupling & Cohesion Metrics
    COUPLING_METRICS = {
        'afferent_coupling': {
            'name': 'Afferent Coupling',
            'description': 'Number of classes that depend on this class',
            'type': 'integer',
            'category': 'coupling'
        },
        'efferent_coupling': {
            'name': 'Efferent Coupling',
            'description': 'Number of classes this class depends on',
            'type': 'integer',
            'category': 'coupling'
        },
        'instability': {
            'name': 'Instability',
            'description': 'Measure of how prone class is to change',
            'type': 'float',
            'category': 'coupling'
        },
    }
    
    # Additional Advanced Metrics
    ADVANCED_METRICS = {
        'halstead_volume': {
            'name': 'Halstead Volume',
            'description': 'Program vocabulary size (Halstead metric)',
            'type': 'float',
            'category': 'complexity'
        },
        'halstead_difficulty': {
            'name': 'Halstead Difficulty',
            'description': 'Program difficulty (Halstead metric)',
            'type': 'float',
            'category': 'complexity'
        },
        'technical_debt_hours': {
            'name': 'Technical Debt (Hours)',
            'description': 'Estimated hours to fix maintainability issues',
            'type': 'float',
            'category': 'quality'
        },
        'code_smells': {
            'name': 'Code Smells Count',
            'description': 'Number of code quality issues detected',
            'type': 'integer',
            'category': 'quality'
        },
    }
    
    ALL_METRICS = {
        **SIZE_METRICS,
        **COMPLEXITY_METRICS,
        **CK_METRICS,
        **STRUCTURE_METRICS,
        **QUALITY_METRICS,
        **DEFECT_METRICS,
        **COUPLING_METRICS,
        **ADVANCED_METRICS,
    }
    
    @classmethod
    def get_all_metrics(cls) -> Dict:
        """Get all available metrics"""
        return cls.ALL_METRICS
    
    @classmethod
    def get_metrics_by_category(cls, category: str) -> Dict:
        """Get metrics by category"""
        return {k: v for k, v in cls.ALL_METRICS.items() if v['category'] == category}
    
    @classmethod
    def get_metric_names(cls) -> List[str]:
        """Get all metric names"""
        return list(cls.ALL_METRICS.keys())
    
    @classmethod
    def search_metrics(cls, query: str) -> Dict:
        """Search metrics by name or description"""
        query_lower = query.lower()
        results = {}
        for key, metric in cls.ALL_METRICS.items():
            if (query_lower in key.lower() or 
                query_lower in metric['name'].lower() or 
                query_lower in metric['description'].lower()):
                results[key] = metric
        return results
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all metric categories"""
        categories = set()
        for metric in cls.ALL_METRICS.values():
            categories.add(metric['category'])
        return sorted(list(categories))
    
    @classmethod
    def print_catalog(cls):
        """Print formatted metric catalog"""
        print("\n" + "="*80)
        print("AVAILABLE METRICS CATALOG")
        print("="*80)
        
        for category in cls.get_categories():
            metrics = cls.get_metrics_by_category(category)
            print(f"\n[{category.upper()}]")
            print("-" * 80)
            for key, metric in metrics.items():
                print(f"  {key:30} {metric['name']}")
                print(f"  {' '*30} -> {metric['description']}")


if __name__ == '__main__':
    MetricsCatalog.print_catalog()
