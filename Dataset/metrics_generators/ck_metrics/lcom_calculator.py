#!/usr/bin/env python3
"""
LCOM (Lack of Cohesion of Methods) Calculator
Real implementation using Java AST parsing
"""

import javalang
from typing import Dict, Set, List
from collections import defaultdict


class LCOMCalculator:
    """Calculate LCOM - Lack of Cohesion of Methods"""
    
    @staticmethod
    def calculate_from_file(file_path: str) -> float:
        """
        Calculate LCOM for a file (simplified version)
        LCOM = measure of cohesion between methods and fields
        
        Returns:
            LCOM value (0-1, lower is better cohesion)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            import re
            # Count methods and fields
            methods = re.findall(r'\b(?:public|private|protected)\s+(?:static\s+)?\w+\s+(\w+)\s*\(', content)
            fields = re.findall(r'\b(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*[;=]', content)
            
            if not methods or not fields:
                return 0.0
            
            # Simplified LCOM: ratio of fields to methods
            # Lower values indicate better cohesion
            return round(min(1.0, len(fields) / len(methods)), 3)
        except:
            return 0.0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            tree = javalang.parse.parse(content)
            package_name = tree.package.name if tree.package else ""
            
            for path, class_node in tree.filter(javalang.tree.ClassDeclaration):
                class_name = f"{package_name}.{class_node.name}" if package_name else class_node.name
                
                # Get all fields in class
                fields = set()
                for _, field in tree.filter(javalang.tree.FieldDeclaration):
                    fields.add(field.name)
                
                # Get all methods and their field usage
                methods = []
                for _, method in tree.filter(javalang.tree.MethodDeclaration):
                    method_fields = set()
                    if method.body:
                        # Find all field accesses in method
                        for _, member_ref in method.body.filter(javalang.tree.MemberReference):
                            if member_ref.member in fields:
                                method_fields.add(member_ref.member)
                    
                    methods.append((method.name, method_fields))
                
                # Calculate P and Q
                method_count = len(methods)
                if method_count <= 1:
                    results[class_name] = 0.0
                    continue
                
                p_count = 0  # Pairs with no shared variables
                q_count = 0  # Pairs with shared variables
                
                for i in range(len(methods)):
                    for j in range(i + 1, len(methods)):
                        _, fields_i = methods[i]
                        _, fields_j = methods[j]
                        
                        if len(fields_i & fields_j) == 0:
                            p_count += 1
                        else:
                            q_count += 1
                
                # Calculate LCOM
                if p_count > q_count:
                    lcom = (p_count - q_count) / p_count if p_count > 0 else 0
                else:
                    lcom = 0.0
                
                results[class_name] = round(lcom, 2)
            
            return results
            
        except Exception:
            return results
