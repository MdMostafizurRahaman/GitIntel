"""
Metrics Generators Package - All 64 metrics organized by category

Structure:
- loc_metrics: Lines of Code metrics (5)
- ck_metrics: Chidamber-Kemerer metrics (6)
- complexity_metrics: Code complexity metrics (4)
- halstead_metrics: Halstead complexity metrics (5)
- defect_metrics: Bug and defect detection (4)
- quality_metrics: Code quality analysis (4)
- change_metrics: Version control metrics (4)
- oop_metrics: Object-oriented design metrics (8)
- coupling_metrics: Coupling and dependencies (4)
- process_metrics: Software process metrics (6)

Total: 64 metrics, all using REAL calculations from actual code
"""

from .loc_metrics import *
from .ck_metrics import *
from .complexity_metrics import *
from .halstead_metrics import *
from .defect_metrics import *
from .quality_metrics import *
from .change_metrics import *
from .oop_metrics import *
from .coupling_metrics import *
from .process_metrics import *
from .master_metrics_generator import MasterMetricsGenerator

__version__ = "1.0.0"
__all__ = [
    'MasterMetricsGenerator',
    # LOC Metrics
    'LOCCalculator',
    'KLOCCalculator',
    'SOCCalculator',
    'CLOCCalculator',
    'BLOCCalculator',
    # CK Metrics
    'WMCCalculator',
    'DITCalculator',
    'NOCCalculator',
    'CBOCalculator',
    'RFCCalculator',
    'LCOMCalculator',
    # Complexity Metrics
    'CyclomaticComplexityCalculator',
    'CognitiveComplexityCalculator',
    'EssentialComplexityCalculator',
    'MaxNestingDepthCalculator',
    # Halstead Metrics
    'HalsteadCalculator',
    # Defect Metrics
    'DefectDetector',
    # Quality Metrics
    'QualityAnalyzer',
    # Change Metrics
    'ChangeAnalyzer',
    # OOP Metrics
    'OOPAnalyzer',
    # Coupling Metrics
    'CouplingAnalyzer',
    # Process Metrics
    'ProcessAnalyzer'
]
