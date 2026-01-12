#!/usr/bin/env python3
"""
DIT (Depth of Inheritance Tree) Calculator
Real implementation using Java AST parsing
"""

import javalang
from typing import Dict
from collections import defaultdict


class DITCalculator:
    """Calculate DIT - Depth of Inheritance Tree"""
    
    @staticmethod
    def calculate_from_directory(dir_path: str) -> Dict[str, int]:
        """
        Calculate DIT for all classes in a directory
        DIT = maximum path length from class to root of inheritance hierarchy
        
        Args:
            dir_path: Path to directory containing Java files
            
        Returns:
            Dictionary mapping class names to DIT values
        """
        # First pass: build inheritance tree
        inheritance_tree = defaultdict(str)  # child -> parent
        all_classes = set()
        
        from pathlib import Path
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
                    
                    # Store parent class if extends exists
                    if class_node.extends:
                        parent = class_node.extends.name
                        parent_name = f"{package_name}.{parent}" if package_name else parent
                        inheritance_tree[class_name] = parent_name
            except:
                continue
        
        # Second pass: calculate DIT for each class
        results = {}
        for class_name in all_classes:
            dit = DITCalculator._calculate_depth(class_name, inheritance_tree)
            results[class_name] = dit
        
        return results
    
    @staticmethod
    def _calculate_depth(class_name: str, inheritance_tree: Dict, visited: set = None) -> int:
        """
        Calculate depth recursively
        
        Args:
            class_name: Name of class to calculate DIT for
            inheritance_tree: Dictionary of parent classes
            visited: Set to track visited classes (prevent cycles)
            
        Returns:
            Integer depth of inheritance
        """
        if visited is None:
            visited = set()
        
        if class_name in visited:
            return 0  # Circular inheritance prevention
        
        if class_name not in inheritance_tree:
            return 0  # No parent found
        
        visited.add(class_name)
        parent = inheritance_tree[class_name]
        
        # Recursive: 1 + depth of parent
        return 1 + DITCalculator._calculate_depth(parent, inheritance_tree, visited.copy())
    
    @staticmethod
    def calculate_from_file(file_path: str) -> int:
        """
        Calculate DIT for a single file (returns max DIT from all classes in file)
        
        Args:
            file_path: Path to Java file
            
        Returns:
            Maximum DIT value from all classes in file
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            
            # Build mini inheritance tree for this file
            inheritance_tree = {}
            package_name = tree.package.name if tree.package else ""
            
            for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                class_name = f"{package_name}.{class_node.name}" if package_name else class_node.name
                
                if class_node.extends:
                    parent = class_node.extends.name
                    parent_name = f"{package_name}.{parent}" if package_name else parent
                    inheritance_tree[class_name] = parent_name
            
            # Calculate depths and return max
            if not inheritance_tree:
                return 0
            
            depths = [DITCalculator._calculate_depth(cls, inheritance_tree) 
                     for cls in inheritance_tree.keys()]
            return max(depths) if depths else 0
            
        except Exception as e:
            return 0
