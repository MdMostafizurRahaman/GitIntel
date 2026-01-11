#!/usr/bin/env python3
"""
Coupling Metrics Calculator - Real implementation using AST parsing
Measures coupling between classes and packages
"""

import javalang
from typing import Dict, Set
from collections import defaultdict
from pathlib import Path


class CouplingAnalyzer:
    """Analyze coupling metrics between classes"""
    
    @staticmethod
    def analyze_directory(dir_path: str) -> Dict[str, Dict[str, int]]:
        """
        Analyze coupling metrics for all Java files in directory
        
        Args:
            dir_path: Path to directory containing Java files
            
        Returns:
            Dictionary with coupling metrics
        """
        metrics = {}
        
        java_files = Path(dir_path).rglob('*.java')
        
        for java_file in java_files:
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                tree = javalang.parse.parse(content)
                package_name = tree.package.name if tree.package else ""
                
                for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                    class_name = f"{package_name}.{class_node.name}" if package_name else class_node.name
                    
                    # Afferent coupling - classes that depend on this
                    afferent = CouplingAnalyzer._calculate_afferent(class_name, dir_path)
                    
                    # Efferent coupling - classes this depends on
                    efferent = CouplingAnalyzer._calculate_efferent(class_node, package_name)
                    
                    # Instability
                    total = afferent + efferent
                    instability = (efferent / total) if total > 0 else 0
                    
                    # Abstractness (for package)
                    is_abstract = 'abstract' in class_node.modifiers
                    
                    metrics[class_name] = {
                        'afferent_coupling': afferent,
                        'efferent_coupling': efferent,
                        'instability': round(instability, 2),
                        'is_abstract': is_abstract
                    }
            except:
                continue
        
        return metrics
    
    @staticmethod
    def _calculate_afferent(class_name: str, dir_path: str) -> int:
        """Count classes that depend on this class (incoming dependencies)"""
        count = 0
        
        java_files = Path(dir_path).rglob('*.java')
        
        for java_file in java_files:
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check if file imports or references the class
                if class_name.split('.')[-1] in content:
                    count += 1
            except:
                continue
        
        return count
    
    @staticmethod
    def _calculate_efferent(class_node, package_name: str) -> int:
        """Count classes this class depends on (outgoing dependencies)"""
        dependencies = set()
        
        try:
            # Check imports
            if hasattr(class_node, 'extends') and class_node.extends:
                dependencies.add(class_node.extends.name)
            
            # Check implemented interfaces
            if hasattr(class_node, 'implements') and class_node.implements:
                for interface in class_node.implements:
                    dependencies.add(interface.name)
            
            # Check field types and method signatures
            if hasattr(class_node, 'body'):
                for member in class_node.body:
                    if hasattr(member, 'type'):
                        if hasattr(member.type, 'name'):
                            dependencies.add(member.type.name)
        except:
            pass
        
        return len(dependencies)
