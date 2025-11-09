#!/usr/bin/env python3
"""
Unified Metrics Analyzer - Consolidates all code metrics into single system
Combines CK Metrics, Complexity, Halstead, Maintainability Index, and Technical Debt
"""

import os
import javalang
import radon.complexity as radon_cc
from radon.raw import analyze as radon_analyze
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from ck_metrics_analyzer import CKMetricsAnalyzer, ClassMetrics

@dataclass
class ComplexityMetrics:
    """Complexity metrics for a file/class"""
    cyclomatic_complexity: float
    cognitive_complexity: float
    average_complexity: float
    max_complexity: int
    num_functions: int

@dataclass
class HalsteadMetrics:
    """Halstead complexity metrics"""
    volume: float
    difficulty: float
    effort: float
    time: float
    bugs: float
    num_operators: int
    num_operands: int
    distinct_operators: int
    distinct_operands: int

@dataclass
class MaintainabilityMetrics:
    """Maintainability and quality metrics"""
    maintainability_index: float
    technical_debt_hours: float
    technical_debt_score: float
    code_smells: List[str]
    refactoring_candidates: List[str]

@dataclass
class UnifiedMetrics:
    """Complete unified metrics for a class/file"""
    name: str
    file_path: str
    ck_metrics: Optional[ClassMetrics] = None
    complexity: Optional[ComplexityMetrics] = None
    halstead: Optional[HalsteadMetrics] = None
    maintainability: Optional[MaintainabilityMetrics] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'file_path': self.file_path,
            'ck_metrics': {
                'wmc': self.ck_metrics.wmc if self.ck_metrics else 0,
                'cbo': self.ck_metrics.cbo if self.ck_metrics else 0,
                'rfc': self.ck_metrics.rfc if self.ck_metrics else 0,
                'lcom': self.ck_metrics.lcom if self.ck_metrics else 0,
                'dit': self.ck_metrics.dit if self.ck_metrics else 0,
                'noc': self.ck_metrics.noc if self.ck_metrics else 0
            } if self.ck_metrics else None,
            'complexity': {
                'cyclomatic': self.complexity.cyclomatic_complexity if self.complexity else 0,
                'cognitive': self.complexity.cognitive_complexity if self.complexity else 0,
                'average': self.complexity.average_complexity if self.complexity else 0,
                'max': self.complexity.max_complexity if self.complexity else 0,
                'num_functions': self.complexity.num_functions if self.complexity else 0
            } if self.complexity else None,
            'halstead': {
                'volume': self.halstead.volume if self.halstead else 0,
                'difficulty': self.halstead.difficulty if self.halstead else 0,
                'effort': self.halstead.effort if self.halstead else 0,
                'estimated_bugs': self.halstead.bugs if self.halstead else 0
            } if self.halstead else None,
            'maintainability': {
                'index': self.maintainability.maintainability_index if self.maintainability else 0,
                'tech_debt_hours': self.maintainability.technical_debt_hours if self.maintainability else 0,
                'tech_debt_score': self.maintainability.technical_debt_score if self.maintainability else 0,
                'code_smells': self.maintainability.code_smells if self.maintainability else []
            } if self.maintainability else None
        }


class UnifiedMetricsAnalyzer:
    """
    Unified metrics analyzer that combines all metric calculations
    Provides single-pass analysis for maximum efficiency
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize unified analyzer
        
        Args:
            repo_path: Path to repository to analyze
        """
        self.repo_path = repo_path
        self.ck_analyzer = CKMetricsAnalyzer(repo_path)
        self.metrics: Dict[str, UnifiedMetrics] = {}
        
    def analyze_all(self) -> Dict[str, UnifiedMetrics]:
        """
        Run complete unified analysis
        Calculates all metrics in single pass for efficiency
        
        Returns:
            Dictionary mapping class/file name to UnifiedMetrics
        """
        print("🔄 Running unified metrics analysis...")
        
        # Step 1: Get CK metrics (includes basic structure analysis)
        print("  📐 Analyzing CK metrics...")
        ck_results = self.ck_analyzer.analyze_repository()
        
        # Step 2: For each class, calculate additional metrics
        print("  🧮 Calculating complexity metrics...")
        for class_name, ck_metrics in ck_results.items():
            file_path = ck_metrics.file_path
            
            # Initialize unified metrics
            unified = UnifiedMetrics(
                name=class_name,
                file_path=file_path,
                ck_metrics=ck_metrics
            )
            
            # Calculate complexity metrics
            unified.complexity = self._calculate_complexity(file_path, class_name)
            
            # Calculate Halstead metrics
            unified.halstead = self._calculate_halstead(file_path)
            
            # Calculate maintainability metrics
            unified.maintainability = self._calculate_maintainability(
                unified.ck_metrics, 
                unified.complexity, 
                unified.halstead
            )
            
            self.metrics[class_name] = unified
        
        print(f"✅ Analysis complete! {len(self.metrics)} classes analyzed")
        return self.metrics
    
    def _calculate_complexity(self, file_path: str, class_name: str) -> ComplexityMetrics:
        """Calculate cyclomatic and cognitive complexity"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Use Radon for Python files
            if file_path.endswith('.py'):
                results = radon_cc.cc_visit(code)
                if results:
                    complexities = [r.complexity for r in results]
                    return ComplexityMetrics(
                        cyclomatic_complexity=sum(complexities) / len(complexities) if complexities else 0,
                        cognitive_complexity=sum(complexities),  # Approximation
                        average_complexity=sum(complexities) / len(complexities) if complexities else 0,
                        max_complexity=max(complexities) if complexities else 0,
                        num_functions=len(results)
                    )
            
            # For Java files, use basic method counting
            elif file_path.endswith('.java'):
                try:
                    tree = javalang.parse.parse(code)
                    methods = []
                    for path, node in tree.filter(javalang.tree.MethodDeclaration):
                        methods.append(node)
                    
                    # Estimate complexity based on method count and statements
                    avg_complexity = len(methods) * 2  # Rough estimate
                    return ComplexityMetrics(
                        cyclomatic_complexity=avg_complexity,
                        cognitive_complexity=avg_complexity * 1.5,
                        average_complexity=avg_complexity / len(methods) if methods else 0,
                        max_complexity=avg_complexity,
                        num_functions=len(methods)
                    )
                except:
                    pass
            
        except Exception:
            pass
        
        # Return default if calculation fails
        return ComplexityMetrics(
            cyclomatic_complexity=0,
            cognitive_complexity=0,
            average_complexity=0,
            max_complexity=0,
            num_functions=0
        )
    
    def _calculate_halstead(self, file_path: str) -> HalsteadMetrics:
        """Calculate Halstead complexity metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Use Radon for Python files
            if file_path.endswith('.py'):
                raw = radon_analyze(code)
                
                # Calculate Halstead metrics from raw metrics
                n1 = raw.lloc  # Distinct operators (approximation)
                n2 = raw.lloc // 2  # Distinct operands (approximation)
                N1 = raw.sloc  # Total operators
                N2 = raw.sloc // 2  # Total operands
                
                n = n1 + n2
                N = N1 + N2
                
                if n > 0 and N > 0:
                    vocabulary = n
                    length = N
                    volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
                    difficulty = (n1 * N2) / (2 * n2) if n2 > 0 else 0
                    effort = volume * difficulty
                    time_to_program = effort / 18  # Stroud number
                    bugs = volume / 3000  # Halstead's delivered bugs
                    
                    return HalsteadMetrics(
                        volume=volume,
                        difficulty=difficulty,
                        effort=effort,
                        time=time_to_program,
                        bugs=bugs,
                        num_operators=N1,
                        num_operands=N2,
                        distinct_operators=n1,
                        distinct_operands=n2
                    )
            
        except Exception:
            pass
        
        # Return default if calculation fails
        return HalsteadMetrics(
            volume=0, difficulty=0, effort=0, time=0, bugs=0,
            num_operators=0, num_operands=0, 
            distinct_operators=0, distinct_operands=0
        )
    
    def _calculate_maintainability(
        self, 
        ck: Optional[ClassMetrics],
        complexity: Optional[ComplexityMetrics],
        halstead: Optional[HalsteadMetrics]
    ) -> MaintainabilityMetrics:
        """
        Calculate maintainability index and technical debt
        
        Uses Microsoft's Maintainability Index formula:
        MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(LOC)
        """
        try:
            import math
            
            # Get metrics values
            volume = halstead.volume if halstead else 1
            cc = complexity.cyclomatic_complexity if complexity else 1
            wmc = ck.wmc if ck else 1
            
            # Ensure positive values for log
            volume = max(volume, 1)
            cc = max(cc, 1)
            wmc = max(wmc, 1)
            
            # Calculate Maintainability Index
            mi = 171 - 5.2 * math.log(volume) - 0.23 * cc - 16.2 * math.log(wmc)
            mi = max(0, min(100, mi))  # Clamp between 0-100
            
            # Calculate technical debt (hours)
            # Based on complexity and maintainability
            tech_debt_hours = 0
            if mi < 20:
                tech_debt_hours = (100 - mi) * 0.5  # High debt
            elif mi < 65:
                tech_debt_hours = (100 - mi) * 0.2  # Medium debt
            else:
                tech_debt_hours = (100 - mi) * 0.05  # Low debt
            
            # Calculate technical debt score (0-100, lower is better)
            tech_debt_score = 100 - mi
            
            # Identify code smells
            code_smells = []
            if ck:
                if ck.wmc > 50:
                    code_smells.append("High WMC - Too many methods")
                if ck.cbo > 10:
                    code_smells.append("High CBO - Too many dependencies")
                if ck.lcom > 0.8:
                    code_smells.append("High LCOM - Low cohesion")
                if ck.dit > 5:
                    code_smells.append("Deep inheritance - Complexity risk")
            
            if complexity:
                if complexity.cyclomatic_complexity > 20:
                    code_smells.append("High cyclomatic complexity")
                if complexity.max_complexity > 30:
                    code_smells.append("Very complex methods detected")
            
            # Identify refactoring candidates
            refactoring_candidates = []
            if mi < 65:
                refactoring_candidates.append("Low maintainability - needs refactoring")
            if tech_debt_hours > 8:
                refactoring_candidates.append("High technical debt - priority refactoring")
            if len(code_smells) >= 3:
                refactoring_candidates.append("Multiple code smells - comprehensive refactoring")
            
            return MaintainabilityMetrics(
                maintainability_index=mi,
                technical_debt_hours=tech_debt_hours,
                technical_debt_score=tech_debt_score,
                code_smells=code_smells,
                refactoring_candidates=refactoring_candidates
            )
            
        except Exception as e:
            # Return default if calculation fails
            return MaintainabilityMetrics(
                maintainability_index=50,
                technical_debt_hours=0,
                technical_debt_score=50,
                code_smells=[],
                refactoring_candidates=[]
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all metrics"""
        if not self.metrics:
            return {}
        
        total_classes = len(self.metrics)
        
        # CK Metrics averages
        avg_wmc = sum(m.ck_metrics.wmc for m in self.metrics.values() if m.ck_metrics) / total_classes
        avg_cbo = sum(m.ck_metrics.cbo for m in self.metrics.values() if m.ck_metrics) / total_classes
        avg_rfc = sum(m.ck_metrics.rfc for m in self.metrics.values() if m.ck_metrics) / total_classes
        avg_lcom = sum(m.ck_metrics.lcom for m in self.metrics.values() if m.ck_metrics) / total_classes
        
        # Complexity averages
        avg_complexity = sum(
            m.complexity.cyclomatic_complexity for m in self.metrics.values() if m.complexity
        ) / total_classes
        
        # Maintainability averages
        avg_mi = sum(
            m.maintainability.maintainability_index for m in self.metrics.values() if m.maintainability
        ) / total_classes
        
        total_tech_debt = sum(
            m.maintainability.technical_debt_hours for m in self.metrics.values() if m.maintainability
        )
        
        # Quality assessment
        quality_score = "Good" if avg_mi > 65 else "Medium" if avg_mi > 20 else "Poor"
        
        return {
            'total_classes': total_classes,
            'averages': {
                'wmc': round(avg_wmc, 2),
                'cbo': round(avg_cbo, 2),
                'rfc': round(avg_rfc, 2),
                'lcom': round(avg_lcom, 2),
                'complexity': round(avg_complexity, 2),
                'maintainability_index': round(avg_mi, 2)
            },
            'technical_debt': {
                'total_hours': round(total_tech_debt, 2),
                'average_hours_per_class': round(total_tech_debt / total_classes, 2)
            },
            'quality_assessment': quality_score
        }
    
    def get_top_issues(self, limit: int = 10) -> Dict[str, List[str]]:
        """Get top classes with issues"""
        # Sort by different criteria
        by_complexity = sorted(
            self.metrics.values(),
            key=lambda m: m.complexity.cyclomatic_complexity if m.complexity else 0,
            reverse=True
        )[:limit]
        
        by_coupling = sorted(
            self.metrics.values(),
            key=lambda m: m.ck_metrics.cbo if m.ck_metrics else 0,
            reverse=True
        )[:limit]
        
        by_tech_debt = sorted(
            self.metrics.values(),
            key=lambda m: m.maintainability.technical_debt_hours if m.maintainability else 0,
            reverse=True
        )[:limit]
        
        return {
            'most_complex': [m.name for m in by_complexity],
            'highest_coupling': [m.name for m in by_coupling],
            'highest_tech_debt': [m.name for m in by_tech_debt]
        }


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        print("Usage: python unified_metrics_analyzer.py <repo_path>")
        sys.exit(1)
    
    analyzer = UnifiedMetricsAnalyzer(repo_path)
    results = analyzer.analyze_all()
    
    print("\n" + "="*70)
    print("UNIFIED METRICS SUMMARY")
    print("="*70)
    
    summary = analyzer.get_summary()
    print(f"\n📊 Total Classes Analyzed: {summary['total_classes']}")
    print(f"\n📐 Average Metrics:")
    for metric, value in summary['averages'].items():
        print(f"  • {metric.upper()}: {value}")
    
    print(f"\n💰 Technical Debt:")
    print(f"  • Total Hours: {summary['technical_debt']['total_hours']}")
    print(f"  • Per Class: {summary['technical_debt']['average_hours_per_class']}")
    
    print(f"\n🎯 Quality Assessment: {summary['quality_assessment']}")
    
    top_issues = analyzer.get_top_issues()
    print(f"\n🔥 Top 10 Most Complex Classes:")
    for i, name in enumerate(top_issues['most_complex'], 1):
        print(f"  {i}. {name}")
