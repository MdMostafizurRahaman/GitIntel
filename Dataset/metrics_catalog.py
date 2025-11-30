"""
Comprehensive Metrics Catalog - 63+ Metrics
সব metrics predefined - user সিলেক্ট করে dataset বানাবে
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class MetricsCatalog:
    """Complete catalog of all 63+ available metrics"""
    
    # ============ LINES OF CODE METRICS (5) ============
    LOC_METRICS = {
        'kloc': {
            'name': 'KLOC (Thousands of Lines)',
            'description': 'Lines of code in thousands (LOC/1000)',
            'type': 'float',
            'category': 'loc'
        },
        'loc': {
            'name': 'LOC (Lines of Code)',
            'description': 'Total lines of code excluding comments and blanks',
            'type': 'integer',
            'category': 'loc'
        },
        'soc': {
            'name': 'SOC (Source Lines of Code)',
            'description': 'Source lines excluding non-executable statements',
            'type': 'integer',
            'category': 'loc'
        },
        'cloc': {
            'name': 'CLOC (Comment Lines)',
            'description': 'Number of comment lines',
            'type': 'integer',
            'category': 'loc'
        },
        'bloc': {
            'name': 'BLOC (Blank Lines)',
            'description': 'Number of blank lines',
            'type': 'integer',
            'category': 'loc'
        },
    }
    
    # ============ SIZE METRICS (4) ============
    SIZE_METRICS = {
        'num_files': {
            'name': 'Number of Files',
            'description': 'Total number of source files',
            'type': 'integer',
            'category': 'size'
        },
        'num_classes': {
            'name': 'Number of Classes',
            'description': 'Total number of classes defined',
            'type': 'integer',
            'category': 'size'
        },
        'num_methods': {
            'name': 'Number of Methods',
            'description': 'Total number of methods/functions',
            'type': 'integer',
            'category': 'size'
        },
        'num_statements': {
            'name': 'Number of Statements',
            'description': 'Total executable statements',
            'type': 'integer',
            'category': 'size'
        },
    }
    
    # ============ COMPLEXITY METRICS (4) ============
    COMPLEXITY_METRICS = {
        'cyclomatic_complexity': {
            'name': 'Cyclomatic Complexity',
            'description': 'Number of independent paths through code (McCabe)',
            'type': 'integer',
            'category': 'complexity'
        },
        'cognitive_complexity': {
            'name': 'Cognitive Complexity',
            'description': 'How difficult code is to understand',
            'type': 'integer',
            'category': 'complexity'
        },
        'essential_complexity': {
            'name': 'Essential Complexity',
            'description': 'Measure of unstructured constructs',
            'type': 'integer',
            'category': 'complexity'
        },
        'max_nesting_depth': {
            'name': 'Maximum Nesting Depth',
            'description': 'Maximum depth of nested blocks',
            'type': 'integer',
            'category': 'complexity'
        },
    }
    
    # ============ CHANGE/CHURN METRICS (4) ============
    CHANGE_METRICS = {
        'churn': {
            'name': 'Code Churn',
            'description': 'Total lines added + deleted over time',
            'type': 'integer',
            'category': 'change'
        },
        'additions': {
            'name': 'Lines Added',
            'description': 'Number of lines added',
            'type': 'integer',
            'category': 'change'
        },
        'deletions': {
            'name': 'Lines Deleted',
            'description': 'Number of lines deleted',
            'type': 'integer',
            'category': 'change'
        },
        'changes': {
            'name': 'Total Changes',
            'description': 'Total number of modifications',
            'type': 'integer',
            'category': 'change'
        },
    }
    
    # ============ CK METRICS (6) ============
    CK_METRICS = {
        'wmc': {
            'name': 'WMC (Weighted Methods per Class)',
            'description': 'Sum of complexities of all methods in a class',
            'type': 'integer',
            'category': 'ck'
        },
        'dit': {
            'name': 'DIT (Depth of Inheritance Tree)',
            'description': 'Maximum inheritance depth in class hierarchy',
            'type': 'integer',
            'category': 'ck'
        },
        'noc': {
            'name': 'NOC (Number of Children)',
            'description': 'Number of immediate subclasses',
            'type': 'integer',
            'category': 'ck'
        },
        'cbo': {
            'name': 'CBO (Coupling Between Objects)',
            'description': 'Number of classes this class depends on',
            'type': 'integer',
            'category': 'ck'
        },
        'rfc': {
            'name': 'RFC (Response For a Class)',
            'description': 'Number of methods callable from a class',
            'type': 'integer',
            'category': 'ck'
        },
        'lcom': {
            'name': 'LCOM (Lack of Cohesion of Methods)',
            'description': 'Measure of class cohesion (lower is better)',
            'type': 'float',
            'category': 'ck'
        },
    }
    
    # ============ MAINTAINABILITY METRICS (3) ============
    MAINTAINABILITY_METRICS = {
        'maintainability_index': {
            'name': 'Maintainability Index',
            'description': 'Score from 0-100 indicating code maintainability',
            'type': 'float',
            'category': 'maintainability'
        },
        'technical_debt': {
            'name': 'Technical Debt',
            'description': 'Estimated hours to fix maintainability issues',
            'type': 'float',
            'category': 'maintainability'
        },
        'code_smells': {
            'name': 'Code Smells',
            'description': 'Number of code quality issues detected',
            'type': 'integer',
            'category': 'maintainability'
        },
    }
    
    # ============ HALSTEAD METRICS (5) ============
    HALSTEAD_METRICS = {
        'halstead_volume': {
            'name': 'Halstead Volume',
            'description': 'Size of implementation (operators + operands)',
            'type': 'float',
            'category': 'halstead'
        },
        'halstead_difficulty': {
            'name': 'Halstead Difficulty',
            'description': 'How difficult the program is to understand',
            'type': 'float',
            'category': 'halstead'
        },
        'halstead_effort': {
            'name': 'Halstead Effort',
            'description': 'Mental effort required to develop',
            'type': 'float',
            'category': 'halstead'
        },
        'halstead_time': {
            'name': 'Halstead Time',
            'description': 'Estimated time to program (seconds)',
            'type': 'float',
            'category': 'halstead'
        },
        'halstead_bugs': {
            'name': 'Halstead Bugs',
            'description': 'Estimated number of delivered bugs',
            'type': 'float',
            'category': 'halstead'
        },
    }
    
    # ============ DEFECT METRICS (4) ============
    DEFECT_METRICS = {
        'bug_density': {
            'name': 'Bug Density',
            'description': 'Bugs per thousand lines of code',
            'type': 'float',
            'category': 'defect'
        },
        'num_bugs': {
            'name': 'Number of Bugs',
            'description': 'Total bugs found in file/module',
            'type': 'integer',
            'category': 'defect'
        },
        'vulnerabilities': {
            'name': 'Vulnerabilities',
            'description': 'Security vulnerabilities detected',
            'type': 'integer',
            'category': 'defect'
        },
        'has_defect': {
            'name': 'Has Defect (Label)',
            'description': 'Binary label: whether file contains defects',
            'type': 'boolean',
            'category': 'defect'
        },
    }
    
    # ============ QUALITY METRICS (4) ============
    QUALITY_METRICS = {
        'duplication': {
            'name': 'Code Duplication',
            'description': 'Percentage of duplicated code',
            'type': 'float',
            'category': 'quality'
        },
        'test_coverage': {
            'name': 'Test Coverage',
            'description': 'Percentage of code covered by tests',
            'type': 'float',
            'category': 'quality'
        },
        'documentation': {
            'name': 'Documentation Coverage',
            'description': 'Percentage of documented code',
            'type': 'float',
            'category': 'quality'
        },
        'comment_ratio': {
            'name': 'Comment Ratio',
            'description': 'Ratio of comments to code lines',
            'type': 'float',
            'category': 'quality'
        },
    }
    
    # ============ AUTHOR/TIME METRICS (4) ============
    AUTHOR_METRICS = {
        'num_authors': {
            'name': 'Number of Authors',
            'description': 'Number of unique contributors',
            'type': 'integer',
            'category': 'author'
        },
        'num_commits': {
            'name': 'Number of Commits',
            'description': 'Total commits affecting file/module',
            'type': 'integer',
            'category': 'author'
        },
        'code_age': {
            'name': 'Code Age (Days)',
            'description': 'Days since first commit',
            'type': 'integer',
            'category': 'author'
        },
        'change_frequency': {
            'name': 'Change Frequency',
            'description': 'Average changes per month',
            'type': 'float',
            'category': 'author'
        },
    }
    
    # ============ OOP METRICS (8) ============
    OOP_METRICS = {
        'npm': {
            'name': 'NPM (Public Methods)',
            'description': 'Number of public methods',
            'type': 'integer',
            'category': 'oop'
        },
        'nprm': {
            'name': 'NPRM (Private Methods)',
            'description': 'Number of private methods',
            'type': 'integer',
            'category': 'oop'
        },
        'npa': {
            'name': 'NPA (Public Attributes)',
            'description': 'Number of public attributes',
            'type': 'integer',
            'category': 'oop'
        },
        'npra': {
            'name': 'NPRA (Private Attributes)',
            'description': 'Number of private attributes',
            'type': 'integer',
            'category': 'oop'
        },
        'fanin': {
            'name': 'Fan-In',
            'description': 'Number of modules calling this module',
            'type': 'integer',
            'category': 'oop'
        },
        'fanout': {
            'name': 'Fan-Out',
            'description': 'Number of modules called by this module',
            'type': 'integer',
            'category': 'oop'
        },
        'noi': {
            'name': 'NOI (Number of Interfaces)',
            'description': 'Number of interfaces implemented',
            'type': 'integer',
            'category': 'oop'
        },
        'nop': {
            'name': 'NOP (Number of Packages)',
            'description': 'Number of packages/namespaces',
            'type': 'integer',
            'category': 'oop'
        },
    }
    
    # ============ COUPLING METRICS (4) ============
    COUPLING_METRICS = {
        'afferent_coupling': {
            'name': 'Afferent Coupling (Ca)',
            'description': 'Number of classes that depend on this class',
            'type': 'integer',
            'category': 'coupling'
        },
        'efferent_coupling': {
            'name': 'Efferent Coupling (Ce)',
            'description': 'Number of classes this class depends on',
            'type': 'integer',
            'category': 'coupling'
        },
        'instability': {
            'name': 'Instability',
            'description': 'Ce / (Ca + Ce) - proneness to change',
            'type': 'float',
            'category': 'coupling'
        },
        'abstractness': {
            'name': 'Abstractness',
            'description': 'Ratio of abstract classes to total classes',
            'type': 'float',
            'category': 'coupling'
        },
    }
    
    # ============ PROCESS METRICS (6) ============
    PROCESS_METRICS = {
        'pre_release_bugs': {
            'name': 'Pre-Release Bugs',
            'description': 'Bugs found before release',
            'type': 'integer',
            'category': 'process'
        },
        'post_release_bugs': {
            'name': 'Post-Release Bugs',
            'description': 'Bugs found after release',
            'type': 'integer',
            'category': 'process'
        },
        'bug_fix_time': {
            'name': 'Bug Fix Time (Hours)',
            'description': 'Average time to fix bugs',
            'type': 'float',
            'category': 'process'
        },
        'revision_count': {
            'name': 'Revision Count',
            'description': 'Number of revisions/versions',
            'type': 'integer',
            'category': 'process'
        },
        'loc_added': {
            'name': 'LOC Added per Revision',
            'description': 'Lines added per revision',
            'type': 'float',
            'category': 'process'
        },
        'loc_deleted': {
            'name': 'LOC Deleted per Revision',
            'description': 'Lines deleted per revision',
            'type': 'float',
            'category': 'process'
        },
    }
    
    # ============ LABEL METRICS (3) ============
    LABEL_METRICS = {
        'defect_type': {
            'name': 'Defect Type',
            'description': 'Type of defect (bug, vulnerability, smell)',
            'type': 'string',
            'category': 'label'
        },
        'severity': {
            'name': 'Defect Severity',
            'description': 'Severity level (low, medium, high, critical)',
            'type': 'string',
            'category': 'label'
        },
        'priority': {
            'name': 'Defect Priority',
            'description': 'Fix priority (P1, P2, P3, P4)',
            'type': 'string',
            'category': 'label'
        },
    }
    
    # Combine ALL metrics (63 total)
    ALL_METRICS = {
        **LOC_METRICS,           # 5
        **SIZE_METRICS,          # 4
        **COMPLEXITY_METRICS,    # 4
        **CHANGE_METRICS,        # 4
        **CK_METRICS,            # 6
        **MAINTAINABILITY_METRICS,  # 3
        **HALSTEAD_METRICS,      # 5
        **DEFECT_METRICS,        # 4
        **QUALITY_METRICS,       # 4
        **AUTHOR_METRICS,        # 4
        **OOP_METRICS,           # 8
        **COUPLING_METRICS,      # 4
        **PROCESS_METRICS,       # 6
        **LABEL_METRICS,         # 3
    }  # Total: 64 metrics
    
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
    def get_metrics_count(cls) -> int:
        """Get total number of metrics"""
        return len(cls.ALL_METRICS)
    
    @classmethod
    def get_category_counts(cls) -> Dict[str, int]:
        """Get count of metrics per category"""
        counts = {}
        for metric in cls.ALL_METRICS.values():
            cat = metric['category']
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    @classmethod
    def print_catalog(cls):
        """Print formatted metric catalog"""
        print("\n" + "="*80)
        print(f"AVAILABLE METRICS CATALOG ({cls.get_metrics_count()} METRICS)")
        print("="*80)
        
        for category in cls.get_categories():
            metrics = cls.get_metrics_by_category(category)
            print(f"\n[{category.upper()}] ({len(metrics)} metrics)")
            print("-" * 80)
            for key, metric in metrics.items():
                print(f"  {key:30} {metric['name']}")
                print(f"  {' '*30} -> {metric['description']}")
        
        # Summary
        print("\n" + "="*80)
        print(f" Total Metrics Available: {cls.get_metrics_count()}")
        print(f" Categories: {len(cls.get_categories())}")
        print(" Metrics by Category:")
        for cat, count in sorted(cls.get_category_counts().items()):
            print(f"   {cat.upper()}: {count} metrics")
        print("="*80)


if __name__ == '__main__':
    MetricsCatalog.print_catalog()
