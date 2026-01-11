"""
OOP Analysis Module - Complete Object-Oriented Programming Metrics
Analyzes Java code for comprehensive OOP characteristics
"""

import re
from typing import Dict, Optional

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False


class OOPAnalyzer:
    """Analyzes Java code for OOP metrics using Javalang AST"""
    
    @staticmethod
    def analyze(code: str) -> Dict:
        """
        Perform complete OOP analysis on Java code
        
        Args:
            code: Java source code as string
            
        Returns:
            Dictionary containing OOP metrics:
            - num_classes: Number of classes
            - num_interfaces: Number of interfaces
            - num_enums: Number of enums
            - num_methods: Total methods (including constructors)
            - num_fields: Number of fields (encapsulation)
            - num_abstract_methods: Abstract methods
            - num_static_methods: Static methods
            - inheritance_depth: Max inheritance depth
            - implements_count: Number of implemented interfaces
            - num_constructors: Number of constructors
        """
        
        result = {
            "num_classes": 0,
            "num_interfaces": 0,
            "num_enums": 0,
            "num_methods": 0,
            "num_fields": 0,
            "num_abstract_methods": 0,
            "num_static_methods": 0,
            "num_constructors": 0,
            "inheritance_depth": 0,
            "implements_count": 0,
            "extraction_method": "javalang_ast" if JAVALANG_AVAILABLE else "regex_fallback"
        }
        
        if not code or not code.strip():
            return result
        
        if JAVALANG_AVAILABLE:
            try:
                tree = javalang.parse.parse(code)
                
                # Count classes
                class_nodes = list(tree.filter(javalang.tree.ClassDeclaration))
                result["num_classes"] = len(class_nodes)
                
                # Count interfaces
                interface_nodes = list(tree.filter(javalang.tree.InterfaceDeclaration))
                result["num_interfaces"] = len(interface_nodes)
                
                # Count enums
                enum_nodes = list(tree.filter(javalang.tree.EnumDeclaration))
                result["num_enums"] = len(enum_nodes)
                
                # OOP Analysis: Inheritance and Implementation
                for path, node in class_nodes:
                    # Check inheritance (extends)
                    if node.extends:
                        result["inheritance_depth"] = max(result["inheritance_depth"], 1)
                    
                    # Check interface implementation (implements)
                    if node.implements:
                        result["implements_count"] += len(node.implements)
                
                # Count methods
                method_nodes = list(tree.filter(javalang.tree.MethodDeclaration))
                result["num_methods"] = len(method_nodes)
                
                # Count constructors
                constructor_nodes = list(tree.filter(javalang.tree.ConstructorDeclaration))
                result["num_constructors"] = len(constructor_nodes)
                result["num_methods"] += len(constructor_nodes)
                
                # OOP Analysis: Method types (polymorphism)
                for path, node in method_nodes:
                    if node.modifiers:
                        if 'abstract' in node.modifiers:
                            result["num_abstract_methods"] += 1
                        if 'static' in node.modifiers:
                            result["num_static_methods"] += 1
                
                # OOP Analysis: Fields (encapsulation)
                field_nodes = list(tree.filter(javalang.tree.FieldDeclaration))
                result["num_fields"] = len(field_nodes)
                
            except Exception as e:
                # Fallback to regex if AST parsing fails
                result.update(OOPAnalyzer._regex_fallback(code))
                result["extraction_method"] = "regex_fallback"
        else:
            # No Javalang available, use regex
            result.update(OOPAnalyzer._regex_fallback(code))
            result["extraction_method"] = "regex_fallback"
        
        return result
    
    @staticmethod
    def _regex_fallback(code: str) -> Dict:
        """Fallback regex-based OOP analysis (less accurate)"""
        return {
            "num_classes": len(re.findall(r'\bclass\s+\w+', code)),
            "num_interfaces": len(re.findall(r'\binterface\s+\w+', code)),
            "num_enums": len(re.findall(r'\benum\s+\w+', code)),
            "num_methods": len(re.findall(r'(public|private|protected|static)\s+[\w<>\[\]]+\s+\w+\s*\(', code)),
            "num_fields": len(re.findall(r'(private|protected|public)\s+[\w<>\[\]]+\s+\w+\s*[;=]', code)),
            "num_abstract_methods": len(re.findall(r'abstract\s+[\w<>\[\]]+\s+\w+\s*\(', code)),
            "num_static_methods": len(re.findall(r'static\s+[\w<>\[\]]+\s+\w+\s*\(', code)),
            "num_constructors": 0,  # Hard to detect with regex
            "inheritance_depth": 1 if re.search(r'extends\s+\w+', code) else 0,
            "implements_count": len(re.findall(r'implements\s+[\w,\s]+', code))
        }
    
    @staticmethod
    def get_oop_summary(metrics: Dict) -> str:
        """Generate human-readable OOP summary"""
        summary_parts = []
        
        if metrics.get("num_classes", 0) > 0:
            summary_parts.append(f"{metrics['num_classes']} class(es)")
        if metrics.get("num_interfaces", 0) > 0:
            summary_parts.append(f"{metrics['num_interfaces']} interface(s)")
        if metrics.get("num_enums", 0) > 0:
            summary_parts.append(f"{metrics['num_enums']} enum(s)")
        
        summary = ", ".join(summary_parts) if summary_parts else "No OOP structures"
        
        # Add inheritance info
        if metrics.get("inheritance_depth", 0) > 0:
            summary += f" [Inheritance: depth {metrics['inheritance_depth']}]"
        if metrics.get("implements_count", 0) > 0:
            summary += f" [Implements: {metrics['implements_count']} interface(s)]"
        
        return summary


# Convenience function for quick analysis
def analyze_oop(code: str) -> Dict:
    """Quick OOP analysis"""
    return OOPAnalyzer.analyze(code)


if __name__ == "__main__":
    # Test with sample Java code
    sample_code = """
    package com.example;
    
    import java.util.List;
    
    public class Employee extends Person implements Serializable, Comparable<Employee> {
        private String name;
        private int age;
        private static int employeeCount = 0;
        
        public Employee(String name) {
            this.name = name;
            employeeCount++;
        }
        
        public String getName() {
            return name;
        }
        
        public static int getEmployeeCount() {
            return employeeCount;
        }
        
        @Override
        public int compareTo(Employee other) {
            return this.name.compareTo(other.name);
        }
    }
    
    interface Serializable {
        void serialize();
    }
    """
    
    analyzer = OOPAnalyzer()
    result = analyzer.analyze(sample_code)
    
    print("OOP Analysis Results:")
    print(f"  Classes: {result['num_classes']}")
    print(f"  Interfaces: {result['num_interfaces']}")
    print(f"  Methods: {result['num_methods']}")
    print(f"  Fields: {result['num_fields']}")
    print(f"  Static methods: {result['num_static_methods']}")
    print(f"  Inheritance depth: {result['inheritance_depth']}")
    print(f"  Implements count: {result['implements_count']}")
    print(f"\nSummary: {OOPAnalyzer.get_oop_summary(result)}")
