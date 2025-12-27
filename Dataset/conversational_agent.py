#!/usr/bin/env python3
"""
Conversational Agentic Dataset Generator
Uses Gemini to iteratively understand user intent and generate datasets
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import os

# LLM imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════════
# METRICS DATABASE - 64 Metrics
# ═══════════════════════════════════════════════════════════════════════════════

METRICS_DATABASE = {
    # CK Metrics (6)
    "WMC": {"name": "Weighted Methods per Class", "category": "CK", "description": "Sum of method complexities"},
    "DIT": {"name": "Depth of Inheritance Tree", "category": "CK", "description": "Maximum inheritance depth"},
    "NOC": {"name": "Number of Children", "category": "CK", "description": "Direct subclass count"},
    "CBO": {"name": "Coupling Between Objects", "category": "CK", "description": "Class dependencies"},
    "RFC": {"name": "Response For a Class", "category": "CK", "description": "Methods directly/indirectly invoked"},
    "LCOM": {"name": "Lack of Cohesion of Methods", "category": "CK", "description": "Method cohesion measure"},
    
    # Complexity (4)
    "CC": {"name": "Cyclomatic Complexity", "category": "Complexity", "description": "Cyclomatic path complexity"},
    "MCC": {"name": "Modified Cyclomatic Complexity", "category": "Complexity", "description": "Modified CC version"},
    "COGNITIVE": {"name": "Cognitive Complexity", "category": "Complexity", "description": "Code readability metric"},
    "COGNITIVE_WEIGHTED": {"name": "Cognitive Complexity Weighted", "category": "Complexity", "description": "Weighted cognitive complexity"},
    
    # Size (5)
    "KLOC": {"name": "Kilo Lines of Code", "category": "Size", "description": "Code size in thousands"},
    "LOC": {"name": "Lines of Code", "category": "Size", "description": "Total lines of code"},
    "SLOC": {"name": "Source Lines of Code", "category": "Size", "description": "Non-comment source lines"},
    "CLOC": {"name": "Comment Lines of Code", "category": "Size", "description": "Comment line count"},
    "LLOC": {"name": "Logical Lines of Code", "category": "Size", "description": "Logical code statements"},
    
    # Coupling (5)
    "AFFERENT_COUPLING": {"name": "Afferent Coupling", "category": "Coupling", "description": "Incoming dependencies (fan-in)"},
    "EFFERENT_COUPLING": {"name": "Efferent Coupling", "category": "Coupling", "description": "Outgoing dependencies (fan-out)"},
    "INSTABILITY": {"name": "Instability", "category": "Coupling", "description": "EC / (EC + AC)"},
    "ABSTRACTNESS": {"name": "Abstractness", "category": "Coupling", "description": "Abstract classes / Total classes"},
    "DISTANCE": {"name": "Normalized Distance from Main Sequence", "category": "Coupling", "description": "|A + I - 1|"},
    
    # Cohesion (6)
    "COHESION": {"name": "General Cohesion", "category": "Cohesion", "description": "Method cohesion"},
    "LCOM1": {"name": "LCOM1", "category": "Cohesion", "description": "LCOM variant 1"},
    "LCOM2": {"name": "LCOM2", "category": "Cohesion", "description": "LCOM variant 2"},
    "LCOM3": {"name": "LCOM3", "category": "Cohesion", "description": "LCOM variant 3"},
    "LCOM4": {"name": "LCOM4", "category": "Cohesion", "description": "LCOM variant 4"},
    "LCOM5": {"name": "LCOM5", "category": "Cohesion", "description": "LCOM variant 5"},
    
    # Function Metrics (8)
    "PARAMETERS": {"name": "Function Parameters", "category": "Function", "description": "Parameter count"},
    "VARIABLES": {"name": "Local Variables", "category": "Function", "description": "Local variable count"},
    "RETURN_STATEMENTS": {"name": "Return Statements", "category": "Function", "description": "Return count"},
    "CALLS": {"name": "Function Calls", "category": "Function", "description": "Outgoing calls"},
    "CALLED_BY": {"name": "Called By Count", "category": "Function", "description": "Incoming calls"},
    "DEPTH": {"name": "Nesting Depth", "category": "Function", "description": "Maximum nesting depth"},
    "RECURSION": {"name": "Recursion Count", "category": "Function", "description": "Recursive calls"},
    "TYPE_REFERENCES": {"name": "Type References", "category": "Function", "description": "Unique types used"},
    
    # Halstead (7)
    "HALSTEAD_VOLUME": {"name": "Halstead Volume", "category": "Halstead", "description": "Program volume"},
    "HALSTEAD_DIFFICULTY": {"name": "Halstead Difficulty", "category": "Halstead", "description": "Program difficulty"},
    "HALSTEAD_EFFORT": {"name": "Halstead Effort", "category": "Halstead", "description": "Program effort"},
    "HALSTEAD_TIME": {"name": "Halstead Time", "category": "Halstead", "description": "Implementation time"},
    "HALSTEAD_VOCABULARY": {"name": "Halstead Vocabulary", "category": "Halstead", "description": "Unique operators + operands"},
    "HALSTEAD_LENGTH": {"name": "Halstead Length", "category": "Halstead", "description": "Total operators + operands"},
    "HALSTEAD_OPERAND_COUNT": {"name": "Halstead Operand Count", "category": "Halstead", "description": "Total operands"},
    
    # Defect (10)
    "CHURN": {"name": "Code Churn", "category": "Defect", "description": "Lines changed"},
    "COMPLEXITY_INCREASE": {"name": "Complexity Increase", "category": "Defect", "description": "Complexity delta"},
    "PATH_COUNT": {"name": "Path Count", "category": "Defect", "description": "Execution paths"},
    "PREVIOUS_DEFECTS": {"name": "Previous Defects", "category": "Defect", "description": "Historical bug count"},
    "REVIEWER_COUNT": {"name": "Reviewer Count", "category": "Defect", "description": "Code reviewers"},
    "DEVELOPER_COUNT": {"name": "Developer Count", "category": "Defect", "description": "Contributing developers"},
    "FILE_AGE": {"name": "File Age", "category": "Defect", "description": "Days since creation"},
    "DEVELOPER_EXPERIENCE": {"name": "Developer Experience", "category": "Defect", "description": "Developer skill level"},
    "LOC_ADDED": {"name": "Lines of Code Added", "category": "Defect", "description": "Added lines"},
    "LOC_DELETED": {"name": "Lines of Code Deleted", "category": "Defect", "description": "Deleted lines"},
    
    # Quality (8)
    "TEST_COVERAGE": {"name": "Test Coverage", "category": "Quality", "description": "Code coverage percentage"},
    "MUTANT_KILL_RATE": {"name": "Mutant Kill Rate", "category": "Quality", "description": "Mutation testing score"},
    "CODE_DUPLICATION": {"name": "Code Duplication", "category": "Quality", "description": "Duplicate code ratio"},
    "COMMENT_DENSITY": {"name": "Comment Density", "category": "Quality", "description": "Comment percentage"},
    "BUG_DENSITY": {"name": "Bug Density", "category": "Quality", "description": "Bugs per KLOC"},
    "MAINTAINABILITY_INDEX": {"name": "Maintainability Index", "category": "Quality", "description": "Maintainability score"},
    "TECHNICAL_DEBT": {"name": "Technical Debt", "category": "Quality", "description": "Code debt ratio"},
    "ARCHITECTURAL_VIOLATIONS": {"name": "Architectural Violations", "category": "Quality", "description": "Architecture issues"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# CONVERSATIONAL AGENT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationalDatasetAgent:
    """Intelligent agent that iteratively understands user intent and generates datasets"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.conversation_history = []
        self.detected_config = None
        self.confirmed_config = None
        
        # Initialize Gemini
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel("gemini-2.5-flash")
                print("[OK] Gemini initialized")
            except Exception as e:
                print(f"[WARN] Gemini init failed: {e}")
                self.client = None
    
    def get_metrics_by_keyword(self, keyword: str) -> List[str]:
        """Find metrics similar to keyword"""
        keyword_lower = keyword.lower()
        matches = []
        
        for metric_id, metric_info in METRICS_DATABASE.items():
            name_lower = metric_info['name'].lower()
            if keyword_lower in name_lower or metric_id.lower() in keyword_lower:
                matches.append(metric_id)
        
        return matches
    
    def is_valid_formula(self, formula: str, available_metrics: List[str]) -> Tuple[bool, str]:
        """Validate formula syntax and metric references"""
        try:
            # Check if all metric references in formula are available
            formula_upper = formula.upper()
            for metric in available_metrics:
                if metric in formula_upper:
                    formula_upper = formula_upper.replace(metric, "1")
            
            # Remove operators and parentheses
            clean = re.sub(r'[\+\-\*/\(\)\s]', '', formula_upper)
            
            # If any alphanumeric left, it's an unknown metric
            if re.search(r'[A-Z_]', clean):
                return False, f"Unknown metric references in formula"
            
            # Try to evaluate (with dummy values)
            test_formula = formula
            for metric in available_metrics:
                test_formula = test_formula.replace(metric, "5")
            
            eval(test_formula)
            return True, "Formula is valid"
        except Exception as e:
            return False, f"Formula error: {str(e)}"
    
    def start_conversation(self, user_query: str) -> Dict:
        """Start interactive conversation to understand dataset requirements"""
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_query
        })
        
        # Step 1: Use Gemini to understand initial intent
        print("\n[AGENT] Analyzing your request...")
        clarification = self._get_clarification_questions(user_query)
        
        print(f"\n[AGENT]\n{clarification}")
        
        # Store response in history
        self.conversation_history.append({
            "role": "assistant",
            "content": clarification
        })
        
        return {
            "status": "awaiting_feedback",
            "questions": clarification,
            "conversation_id": datetime.now().isoformat()
        }
    
    def _get_clarification_questions(self, user_query: str) -> str:
        """Generate clarification questions using Gemini or fallback"""
        
        if self.client:
            try:
                system_prompt = """You are a helpful data science assistant. User is requesting a dataset generation.
Your job is to ask SPECIFIC clarifying questions to understand:
1. Which metrics they need (choose from available metrics or describe unknown ones)
2. How to combine metrics (formula, weights, operations)
3. Data sources and constraints
4. Dataset size and format

Be conversational, not robotic. Ask 3-5 targeted questions.
Reference the 64 available metrics if relevant."""
                
                response = self.client.generate_content(
                    f"{system_prompt}\n\nUser request: {user_query}"
                )
                return response.text
            except Exception as e:
                print(f"[FALLBACK] Gemini failed: {e}")
                return self._get_fallback_questions(user_query)
        else:
            return self._get_fallback_questions(user_query)
    
    def _get_fallback_questions(self, user_query: str) -> str:
        """Fallback questions when Gemini unavailable"""
        return """[AGENT] I'd like to clarify your requirements:

1. METRICS: Which of these metric categories interest you?
   - CK Metrics (WMC, DIT, NOC, CBO, RFC, LCOM)
   - Complexity (CC, MCC, Cognitive)
   - Size (LOC, KLOC, SLOC)
   - Coupling (Afferent, Efferent, Instability)
   - Quality (Coverage, Duplication, Bug Density)
   - Other? (describe...)

2. FORMULA: Do you want to:
   - Use metrics as-is (just columns)?
   - Combine them? (sum, average, custom formula?)

3. DATA: 
   - How many records?
   - Any filters? (e.g., WMC > 5)?

Please provide these details and I'll generate your dataset!"""
    
    def refine_with_feedback(self, feedback: str) -> Dict:
        """Process user feedback and refine understanding"""
        
        self.conversation_history.append({
            "role": "user",
            "content": feedback
        })
        
        print("\n[AGENT] Processing your feedback...")
        
        # Parse feedback to extract config
        config = self._parse_user_intent(feedback)
        
        # Validate metrics - Handle known + unknown
        unknown_metrics = []
        known_metrics = []
        
        for metric in config['metrics']:
            if metric in METRICS_DATABASE:
                known_metrics.append(metric)
            else:
                # Check if similar exists
                matches = self.get_metrics_by_keyword(metric)
                if matches:
                    print(f"[INFO] '{metric}' → suggesting {matches}")
                    # Ask user if they meant these
                    return {
                        "status": "clarify_similar",
                        "original": metric,
                        "suggestions": matches,
                        "message": f"Did you mean one of these for '{metric}'?\n" + 
                                  "\n".join([f"  - {m}: {METRICS_DATABASE[m]['name']}" for m in matches[:3]])
                    }
                else:
                    unknown_metrics.append(metric)
        
        # Handle unknown metrics with Gemini
        if unknown_metrics:
            print(f"[AGENT] Unknown metrics detected: {unknown_metrics}")
            print(f"[AGENT] Querying Gemini for definitions...")
            
            enriched_metrics = self._enrich_unknown_metrics(unknown_metrics)
            
            if not enriched_metrics:
                return {
                    "status": "unknown_metrics_failed",
                    "message": f"Could not understand these metrics: {unknown_metrics}\n" +
                              "Please describe what they measure or provide calculation methods."
                }
            
            # Add enriched unknown metrics to config
            config['unknown_metrics'] = enriched_metrics
            print(f"[OK] Successfully enriched {len(enriched_metrics)} unknown metrics")
        
        # Validate formula
        if config.get('formula'):
            all_metrics = config['metrics']
            is_valid, msg = self.is_valid_formula(config['formula'], all_metrics)
            if not is_valid:
                return {
                    "status": "clarify_formula",
                    "message": f"Formula issue: {msg}\n\nPlease correct the formula."
                }
        
        self.confirmed_config = config
        
        confirmation_msg = self._generate_confirmation(config)
        print(f"\n[AGENT]\n{confirmation_msg}")
        
        return {
            "status": "ready_to_generate",
            "config": config,
            "confirmation": confirmation_msg
        }
    
    def _parse_user_intent(self, feedback: str) -> Dict:
        """Extract metrics, formula, and parameters from feedback"""
        config = {
            "metrics": [],
            "formula": None,
            "records": 100,
            "filters": None
        }
        
        feedback_lower = feedback.lower()
        
        # Extract known metrics from database
        for metric_id in METRICS_DATABASE.keys():
            if metric_id.lower() in feedback_lower:
                config['metrics'].append(metric_id)
        
        # Extract unknown metrics (capitalized phrases not in database)
        # Look for patterns like "Code Smell Density", "Technical Debt Ratio"
        import re
        potential_metrics = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', feedback)
        for metric in potential_metrics:
            metric_upper = metric.replace(' ', '_').upper()
            if metric_upper not in METRICS_DATABASE and metric_upper not in config['metrics']:
                config['metrics'].append(metric_upper)
        
        # Also look for lowercase multi-word patterns
        lowercase_patterns = re.findall(r'([a-z]+\s+[a-z]+\s+(?:density|ratio|index|score|count|time|coverage))', feedback_lower)
        for pattern in lowercase_patterns:
            metric_upper = pattern.replace(' ', '_').upper()
            if metric_upper not in METRICS_DATABASE and metric_upper not in config['metrics']:
                config['metrics'].append(metric_upper)
        
        # Extract formula
        formula_match = re.search(r'\(([^)]+)\)', feedback)
        if formula_match:
            config['formula'] = formula_match.group(1)
        
        # Extract record count
        num_match = re.search(r'(\d+)\s*records?', feedback_lower)
        if num_match:
            config['records'] = int(num_match.group(1))
        
        return config
    
    def _enrich_unknown_metrics(self, unknown_metrics: List[str]) -> Dict:
        """Query Gemini to get definitions and calculation methods for unknown metrics"""
        if not self.client:
            print("[WARN] Gemini not available for unknown metric enrichment")
            return self._fallback_metric_enrichment(unknown_metrics)
        
        enriched = {}
        
        for metric in unknown_metrics:
            try:
                prompt = f"""You are a software engineering metrics expert. 
                
A user wants to include '{metric}' in their dataset.

Please provide:
1. Definition: What does this metric measure?
2. Calculation: How is it calculated? (formula or method)
3. Range: What are realistic values? (min-max, average)
4. Unit: What unit is it measured in? (percentage, count, ratio, etc.)

Respond in JSON format:
{{
    "definition": "...",
    "calculation": "...",
    "range": {{"min": 0, "max": 100, "average": 50}},
    "unit": "percentage"
}}
"""
                
                response = self.client.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                metric_info = json.loads(response.text)
                enriched[metric] = metric_info
                
                print(f"[OK] Enriched '{metric}':")
                print(f"     Definition: {metric_info['definition'][:60]}...")
                print(f"     Range: {metric_info['range']}")
                
            except Exception as e:
                print(f"[WARN] Failed to enrich '{metric}': {e}")
                # Use fallback
                enriched[metric] = self._fallback_single_metric(metric)
        
        return enriched
    
    def _fallback_metric_enrichment(self, unknown_metrics: List[str]) -> Dict:
        """Fallback enrichment when Gemini unavailable"""
        enriched = {}
        for metric in unknown_metrics:
            enriched[metric] = self._fallback_single_metric(metric)
        return enriched
    
    def _fallback_single_metric(self, metric: str) -> Dict:
        """Generate fallback info for a single unknown metric"""
        metric_lower = metric.lower()
        
        # Pattern matching for common metric types
        if 'density' in metric_lower or 'ratio' in metric_lower:
            return {
                "definition": f"{metric} (ratio-based metric)",
                "calculation": "Calculated as a percentage or ratio",
                "range": {"min": 0, "max": 100, "average": 50},
                "unit": "percentage"
            }
        elif 'time' in metric_lower or 'duration' in metric_lower:
            return {
                "definition": f"{metric} (time-based metric)",
                "calculation": "Measured in time units",
                "range": {"min": 0, "max": 1000, "average": 100},
                "unit": "hours"
            }
        elif 'count' in metric_lower or 'number' in metric_lower:
            return {
                "definition": f"{metric} (count-based metric)",
                "calculation": "Simple count or enumeration",
                "range": {"min": 0, "max": 100, "average": 10},
                "unit": "count"
            }
        else:
            return {
                "definition": f"{metric} (custom metric)",
                "calculation": "User-defined calculation",
                "range": {"min": 0, "max": 100, "average": 50},
                "unit": "units"
            }
    
    def _suggest_metrics(self, unknown_metric: str) -> str:
        """Suggest similar metrics"""
        matches = self.get_metrics_by_keyword(unknown_metric)
        if matches:
            suggestions = "\n   - ".join(
                [f"{m}: {METRICS_DATABASE[m]['name']}" for m in matches[:5]]
            )
            return f"Similar metrics:\n   - {suggestions}"
        return "No similar metrics found. Check METRICS_DATABASE for available options."
    
    def _generate_confirmation(self, config: Dict) -> str:
        """Generate confirmation message"""
        metrics_str = ", ".join(config['metrics'])
        formula_str = f"Formula: {config['formula']}" if config['formula'] else "Individual columns"
        records_str = f"{config['records']} records"
        
        return f"""CONFIRMATION:
✓ Metrics: {metrics_str}
✓ {formula_str}
✓ {records_str}

Ready to generate? [YES/NO/MODIFY]"""
    
    def generate_dataset(self, config: Dict) -> str:
        """Generate the final dataset based on confirmed config"""
        print(f"\n[AGENT] Generating dataset with config: {config}")
        
        # Create output directory
        output_dir = Path(__file__).parent / "generated_datasets"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agentic_{timestamp}.csv"
        filepath = output_dir / filename
        
        # Generate dataset
        num_records = config.get('records', 100)
        metrics = config['metrics']
        formula = config.get('formula')
        unknown_metrics = config.get('unknown_metrics', {})
        
        csv_columns = metrics.copy()
        if formula:
            csv_columns.append("Formula_Result")
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_columns)
            writer.writeheader()
            
            for i in range(num_records):
                row = {}
                metric_values = {}
                
                # Generate metric values (known + unknown)
                for metric in metrics:
                    if metric in METRICS_DATABASE:
                        # Known metric - use built-in generation
                        value = self._generate_metric_value(metric, i)
                    elif metric in unknown_metrics:
                        # Unknown metric - use Gemini-enriched info
                        value = self._generate_unknown_metric_value(
                            metric, 
                            unknown_metrics[metric], 
                            i
                        )
                    else:
                        # Fallback
                        value = round(i * 0.5 + 1, 2)
                    
                    row[metric] = str(value)
                    metric_values[metric] = value
                
                # Calculate formula if provided
                if formula:
                    try:
                        eval_expr = formula
                        for metric, val in metric_values.items():
                            eval_expr = eval_expr.replace(metric, str(val))
                        result = eval(eval_expr)
                        row["Formula_Result"] = str(round(result, 2))
                    except:
                        row["Formula_Result"] = "0"
                
                writer.writerow(row)
        
        return str(filepath)
    
    def _generate_unknown_metric_value(self, metric_name: str, metric_info: Dict, index: int) -> float:
        """Generate realistic value for unknown metric based on Gemini enrichment"""
        import random
        
        range_info = metric_info.get('range', {"min": 0, "max": 100, "average": 50})
        min_val = range_info.get('min', 0)
        max_val = range_info.get('max', 100)
        avg_val = range_info.get('average', 50)
        
        # Generate with variation around average
        variation = (max_val - min_val) * 0.2
        value = avg_val + random.uniform(-variation, variation)
        
        # Clamp to range
        value = max(min_val, min(max_val, value))
        
        return round(value, 2)
    
    def _generate_metric_value(self, metric: str, index: int) -> float:
        """Generate realistic value for metric"""
        if metric in ["WMC", "RFC", "CBO"]:
            return (index % 20) + 1
        elif metric in ["DIT", "NOC"]:
            return index % 5
        elif metric == "LCOM":
            return round((index % 100) / 100, 2)
        elif metric in ["CC", "MCC"]:
            return round(index * 0.1 + 1, 2)
        elif metric in ["LOC", "SLOC"]:
            return (index % 500) + 50
        elif metric == "KLOC":
            return round((index % 500 + 50) / 1000, 2)
        else:
            return round(index * 0.5 + 1, 2)

# ═══════════════════════════════════════════════════════════════════════════════
# CLI DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    """Interactive CLI demo"""
    print("="*80)
    print("CONVERSATIONAL AGENTIC DATASET GENERATOR")
    print("="*80)
    
    agent = ConversationalDatasetAgent()
    
    # Initial request
    user_query = input("\n[YOU] Describe the dataset you want:\n> ")
    
    # Start conversation
    result = agent.start_conversation(user_query)
    
    # Iterative feedback loop
    while result['status'] == 'awaiting_feedback':
        feedback = input("\n[YOU] ")
        result = agent.refine_with_feedback(feedback)
    
    # Generate if ready
    if result['status'] == 'ready_to_generate':
        confirm = input("\n[Agent asked] Ready to generate? (yes/no): ").lower()
        if confirm == 'yes':
            filepath = agent.generate_dataset(result['config'])
            print(f"\n[SUCCESS] Dataset generated: {filepath}")
        else:
            print("[Agent] Understood. Let's refine...")
            feedback = input("\n[YOU] What to modify?\n> ")
            result = agent.refine_with_feedback(feedback)

if __name__ == "__main__":
    demo()
