#!/usr/bin/env python3
"""
NOC (Number of Children) Calculator
Real implementation using Java AST parsing
"""

import javalang
from typing import Dict
from collections import defaultdict
from pathlib import Path


class NOCCalculator:
    """Calculate NOC - Number of Children (direct subclasses)"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        """
        Calculate NOC for a single file
        
        Returns:
            Number of subclasses/children (0 for single file analysis)
        """
        # NOC requires analyzing multiple files to find children
        # For single file, return 0
        return 0
    
    @staticmethod
    def calculate_from_directory(dir_path: str) -> Dict[str, int]:
        """
        Calculate NOC for all classes in a directory
        NOC = number of immediate subclasses of a class
        
        Args:
            dir_path: Path to directory containing Java files
            
        Returns:
            Dictionary mapping class names to NOC values
        """
        # Build inheritance tree from all files
        inheritance_tree = defaultdict(list)  # parent -> [children]
        all_classes = set()
        
        java_files = Path(dir_path).rglob('*.java')
        
        for java_file in java_files:
            try:
                with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                tree = javalang.parse.parse(content)
                package_name = tree.package.name if tree.package else ""
                
                for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                    class_name = f"{package_name}.{class_node.name}" if package_name else class_node.name
                    all_classes.add(class_name)
                    
                    # If this class extends another, record relationship
                    if class_node.extends:
                        parent = class_node.extends.name
                        parent_name = f"{package_name}.{parent}" if package_name else parent
                        inheritance_tree[parent_name].append(class_name)
            except:
                continue
        
        # Convert to NOC results (count children for each class)
        results = {}
        for class_name in all_classes:
            noc = len(inheritance_tree.get(class_name, []))
            results[class_name] = noc
        
        return results
