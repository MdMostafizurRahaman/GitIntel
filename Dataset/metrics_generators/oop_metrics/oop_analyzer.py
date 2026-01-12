"""
OOP Metrics Analyzer - Object-Oriented Programming metrics
Analyzes classes, inheritance, polymorphism, encapsulation
"""

import re
from pathlib import Path
from typing import Dict


class OOPAnalyzer:
    """Analyzer for OOP metrics"""
    
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, any]:
        """
        Analyze OOP metrics for a file
        
        Returns metrics like:
        - num_classes
        - num_interfaces  
        - num_abstract_classes
        - num_methods
        - num_public_methods
        - num_private_methods
        - num_protected_methods
        - num_fields
        - num_public_fields
        - num_private_fields
        - inheritance_depth (estimated)
        - polymorphism_factor
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            metrics = {}
            
            # Java-specific OOP metrics
            if file_path.endswith('.java'):
                # Count classes
                metrics['num_classes'] = len(re.findall(r'\bclass\s+\w+', code))
                metrics['num_interfaces'] = len(re.findall(r'\binterface\s+\w+', code))
                metrics['num_abstract_classes'] = len(re.findall(r'\babstract\s+class\s+\w+', code))
                
                # Count methods by visibility
                public_methods = re.findall(r'\bpublic\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(', code)
                private_methods = re.findall(r'\bprivate\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(', code)
                protected_methods = re.findall(r'\bprotected\s+(?:static\s+)?(?:\w+\s+)+\w+\s*\(', code)
                
                metrics['num_public_methods'] = len(public_methods)
                metrics['num_private_methods'] = len(private_methods)
                metrics['num_protected_methods'] = len(protected_methods)
                metrics['num_methods'] = len(public_methods) + len(private_methods) + len(protected_methods)
                
                # Count fields by visibility
                public_fields = re.findall(r'\bpublic\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]', code)
                private_fields = re.findall(r'\bprivate\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]', code)
                protected_fields = re.findall(r'\bprotected\s+(?:static\s+)?(?:final\s+)?(?:\w+\s+)+\w+\s*[;=]', code)
                
                metrics['num_public_fields'] = len(public_fields)
                metrics['num_private_fields'] = len(private_fields)
                metrics['num_protected_fields'] = len(protected_fields)
                metrics['num_fields'] = len(public_fields) + len(private_fields) + len(protected_fields)
                
                # Inheritance (extends keyword)
                extends = re.findall(r'\bextends\s+\w+', code)
                metrics['inheritance_depth'] = min(len(extends), 5)  # Cap at 5
                
                # Polymorphism (implements keyword + overrides)
                implements = re.findall(r'\bimplements\s+\w+', code)
                overrides = re.findall(r'@Override', code)
                metrics['polymorphism_factor'] = len(implements) + len(overrides)
                
                # Encapsulation ratio (private/total)
                total_members = metrics['num_methods'] + metrics['num_fields']
                private_members = metrics['num_private_methods'] + metrics['num_private_fields']
                metrics['encapsulation_ratio'] = round(private_members / total_members, 3) if total_members > 0 else 0
                
            # Python-specific OOP metrics
            elif file_path.endswith('.py'):
                # Count classes
                metrics['num_classes'] = len(re.findall(r'^class\s+\w+', code, re.MULTILINE))
                metrics['num_interfaces'] = 0  # Python doesn't have interfaces
                metrics['num_abstract_classes'] = len(re.findall(r'from\s+abc\s+import|ABC', code))
                
                # Count methods
                all_methods = re.findall(r'^\s+def\s+\w+\s*\(', code, re.MULTILINE)
                private_methods = re.findall(r'^\s+def\s+__\w+\s*\(', code, re.MULTILINE)
                protected_methods = re.findall(r'^\s+def\s+_\w+\s*\(', code, re.MULTILINE)
                
                metrics['num_private_methods'] = len(private_methods)
                metrics['num_protected_methods'] = len(protected_methods)
                metrics['num_public_methods'] = len(all_methods) - len(private_methods) - len(protected_methods)
                metrics['num_methods'] = len(all_methods)
                
                # Count attributes
                all_fields = re.findall(r'^\s+self\.\w+\s*=', code, re.MULTILINE)
                private_fields = re.findall(r'^\s+self\.__\w+\s*=', code, re.MULTILINE)
                protected_fields = re.findall(r'^\s+self\._\w+\s*=', code, re.MULTILINE)
                
                metrics['num_private_fields'] = len(private_fields)
                metrics['num_protected_fields'] = len(protected_fields)
                metrics['num_public_fields'] = len(all_fields) - len(private_fields) - len(protected_fields)
                metrics['num_fields'] = len(all_fields)
                
                # Inheritance
                inheritance = re.findall(r'class\s+\w+\((\w+)\)', code)
                metrics['inheritance_depth'] = min(len(inheritance), 5)
                
                # Polymorphism (method overriding)
                overrides = len(re.findall(r'super\(\)\.', code))
                metrics['polymorphism_factor'] = overrides
                
                # Encapsulation
                total_members = metrics['num_methods'] + metrics['num_fields']
                private_members = metrics['num_private_methods'] + metrics['num_private_fields']
                metrics['encapsulation_ratio'] = round(private_members / total_members, 3) if total_members > 0 else 0
            
            else:
                # Default for unsupported languages
                metrics = {
                    'num_classes': 0,
                    'num_interfaces': 0,
                    'num_abstract_classes': 0,
                    'num_methods': 0,
                    'num_public_methods': 0,
                    'num_private_methods': 0,
                    'num_protected_methods': 0,
                    'num_fields': 0,
                    'num_public_fields': 0,
                    'num_private_fields': 0,
                    'num_protected_fields': 0,
                    'inheritance_depth': 0,
                    'polymorphism_factor': 0,
                    'encapsulation_ratio': 0
                }
            
            return metrics
            
        except Exception as e:
            print(f"[ERROR OOPAnalyzer] {file_path}: {e}")
            return {
                'num_classes': 0,
                'num_interfaces': 0,
                'num_abstract_classes': 0,
                'num_methods': 0,
                'num_public_methods': 0,
                'num_private_methods': 0,
                'num_protected_methods': 0,
                'num_fields': 0,
                'num_public_fields': 0,
                'num_private_fields': 0,
                'num_protected_fields': 0,
                'inheritance_depth': 0,
                'polymorphism_factor': 0,
                'encapsulation_ratio': 0
            }
