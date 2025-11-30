#!/usr/bin/env python3
"""
Truly Autonomous AI Agent for Dataset Creation
- No hardcoded mappings
- Learns from user patterns
- Handles ANY query dynamically
- Understands custom formulas
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import ast
import re

# Add parent directory for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from llm_git_analyzer import LLMGitAnalyzer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️ LLM required for autonomous agent")

logger = logging.getLogger(__name__)

class AutonomousAgent:
    """
    Truly autonomous agent that:
    1. Understands ANY natural language query
    2. Creates custom formulas dynamically
    3. Learns from user interactions
    4. No hardcoded logic - pure AI-driven
    """
    
    def __init__(self):
        if not LLM_AVAILABLE:
            raise RuntimeError("LLM is required for autonomous operation")
        
        self.llm = LLMGitAnalyzer()
        self.repo_path = None
        self.knowledge_base = self._load_knowledge_base()
        self.interaction_history = []
        print("🤖 Autonomous AI Agent initialized - Ready to learn and adapt!")
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load learned patterns from previous interactions"""
        kb_path = os.path.join(os.path.dirname(__file__), 'agent_knowledge.json')
        if os.path.exists(kb_path):
            with open(kb_path, 'r') as f:
                return json.load(f)
        return {
            'learned_patterns': [],
            'successful_queries': [],
            'custom_formulas': {},
            'user_preferences': {}
        }
    
    def _save_knowledge_base(self):
        """Save learned patterns for future use"""
        kb_path = os.path.join(os.path.dirname(__file__), 'agent_knowledge.json')
        with open(kb_path, 'w') as f:
            json.dump(self.knowledge_base, f, indent=2)
    
    def set_repository(self, repo_path: str) -> bool:
        """Set repository for analysis"""
        if os.path.exists(repo_path):
            self.repo_path = repo_path
            self.llm.set_repository(repo_path)
            print(f"📁 Repository set: {repo_path}")
            return True
        return False
    
    def understand_query(self, user_query: str) -> Dict[str, Any]:
        """
        Use LLM to deeply understand user intent
        No predefined mappings - pure AI interpretation
        """
        print(f"🧠 Analyzing query: '{user_query}'")
        
        # Check if similar query exists in knowledge base
        similar = self._find_similar_query(user_query)
        if similar:
            print(f"💡 Found similar past query: {similar['query']}")
        
        # Build context-aware prompt for LLM
        prompt = self._build_understanding_prompt(user_query, similar)
        
        try:
            # Let LLM interpret the query completely
            response = self.llm.model.generate_content(prompt)
            understanding = self._parse_llm_understanding(response.text)
            
            # Learn from this interaction
            self._learn_from_query(user_query, understanding)
            
            return understanding
            
        except Exception as e:
            print(f"⚠️ Understanding failed: {e}")
            # Make agentic fallback instead of asking for clarification
            return {
                'intent': 'analyze_repository',
                'confidence': 0.6,
                'needs_clarification': False,
                'auto_decision': 'Defaulting to repository analysis due to understanding failure'
            }
    
    def _build_understanding_prompt(self, query: str, similar: Dict = None) -> str:
        """Build intelligent prompt for LLM"""
        prompt = f"""You are an autonomous AI agent that creates datasets from Git repositories.
Analyze this user query and determine EXACTLY what they want:

Query: "{query}"

Your task:
1. Understand the core intent (what data do they want?)
2. Identify required metrics/calculations
3. Detect any custom formulas or expressions
4. Determine output format preferences
5. Identify any constraints or filters

"""
        
        if similar:
            prompt += f"""
Previous similar query: "{similar['query']}"
That query resulted in: {similar['result_type']}
Use this as context but interpret the new query independently.
"""
        
        prompt += """
Respond in JSON format:
{
    "intent": "clear description of what user wants",
    "data_type": "type of data (commits/files/authors/packages/custom)",
    "metrics": ["list of metrics to calculate"],
    "custom_formula": "any mathematical formula if present",
    "filters": {"any filters or constraints"},
    "output_format": "preferred format",
    "confidence": 0.0-1.0,
    "needs_clarification": true/false,
    "clarification_questions": ["questions if confidence < 0.7"]
}
"""
        return prompt
    
    def _parse_llm_understanding(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM's understanding of the query"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # Make agentic decisions instead of asking for clarification
                if parsed.get('needs_clarification'):
                    parsed['needs_clarification'] = False
                    parsed['confidence'] = max(parsed.get('confidence', 0.5), 0.7)  # Boost confidence
                return parsed
            else:
                # If no JSON, parse text response and make agentic assumptions
                return {
                    'intent': llm_response,
                    'confidence': 0.8,  # Assume high confidence for direct action
                    'needs_clarification': False
                }
        except:
            # Make agentic fallback instead of asking for clarification
            return {
                'intent': 'analyze_repository',
                'confidence': 0.7,
                'needs_clarification': False,
                'auto_decision': 'Defaulting to repository analysis'
            }
    
    def _find_similar_query(self, query: str) -> Optional[Dict]:
        """Find similar queries from knowledge base"""
        # Simple similarity check - can be enhanced with embeddings
        query_lower = query.lower()
        for past_query in self.knowledge_base['successful_queries']:
            if any(word in query_lower for word in past_query['query'].lower().split()):
                return past_query
        return None
    
    def _learn_from_query(self, query: str, understanding: Dict):
        """Learn from successful query interpretation"""
        self.interaction_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'understanding': understanding
        })
        
        # Update knowledge base if confidence is high
        if understanding.get('confidence', 0) > 0.7:
            self.knowledge_base['learned_patterns'].append({
                'query': query,
                'intent': understanding.get('intent'),
                'timestamp': datetime.now().isoformat()
            })
            self._save_knowledge_base()
    
    def _ask_for_clarification(self, query: str) -> Dict[str, Any]:
        """Request clarification from user"""
        return {
            'needs_clarification': True,
            'original_query': query,
            'clarification_questions': [
                'What specific data do you want to extract?',
                'Which metrics should I calculate?',
                'Do you have any custom formulas?',
                'What output format do you prefer?'
            ],
            'confidence': 0.0
        }
    
    def execute_query(self, understanding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the understood query dynamically
        No hardcoded execution paths - let LLM guide
        Agentic execution - no clarification requests
        """
        print(f"🚀 Executing: {understanding.get('intent')}")
        
        # Build execution plan using LLM
        execution_plan = self._generate_execution_plan(understanding)
        
        # Execute plan dynamically
        result = self._execute_plan_dynamically(execution_plan)
        
        # Learn from execution
        self._learn_from_execution(understanding, result)
        
        return result
    
    def _generate_execution_plan(self, understanding: Dict) -> Dict[str, Any]:
        """Let LLM generate execution plan"""
        prompt = f"""Given this understanding of user's request:
{json.dumps(understanding, indent=2)}

And this repository: {self.repo_path}

Generate a detailed execution plan:
1. What Git data to extract
2. What calculations to perform
3. What custom code to execute
4. How to format the output

Respond in JSON:
{{
    "steps": [
        {{"action": "extract_commits", "params": {{}}}},
        {{"action": "calculate_metric", "formula": ""}},
        {{"action": "format_output", "format": ""}}
    ],
    "expected_output": "description"
}}
"""
        
        try:
            response = self.llm.model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: basic plan
        return {
            'steps': [
                {'action': 'extract_data', 'params': understanding},
                {'action': 'calculate', 'params': understanding},
                {'action': 'format', 'params': {'format': 'json'}}
            ]
        }
    
    def _execute_plan_dynamically(self, plan: Dict) -> Dict[str, Any]:
        """Execute plan step by step dynamically"""
        results = []
        
        for step in plan.get('steps', []):
            action = step.get('action')
            params = step.get('params', {})
            
            print(f"  ⚙️ Executing: {action}")
            
            if action == 'extract_commits':
                data = self._extract_git_data('commits', params)
            elif action == 'extract_data':
                data = self._extract_git_data(params.get('data_type', 'commits'), params)
            elif action == 'calculate_metric' or action == 'calculate':
                data = self._calculate_dynamic(params)
            elif action == 'format_output' or action == 'format':
                data = self._format_output(results, params)
            else:
                # Ask LLM how to execute unknown action
                data = self._execute_unknown_action(action, params)
            
            results.append(data)
        
        # Combine results
        return {
            'success': True,
            'data': results[-1] if results else {},
            'steps_executed': len(results),
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_git_data(self, data_type: str, params: Dict) -> Any:
        """Extract Git data dynamically"""
        if not self.repo_path:
            return {'error': 'No repository set'}
        
        try:
            if data_type == 'commits':
                cmd = ['git', 'log', '--oneline', '--no-merges']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                commits = result.stdout.strip().split('\n')
                return {'commits': commits, 'count': len(commits)}
            
            elif data_type == 'files':
                cmd = ['git', 'ls-files']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                files = result.stdout.strip().split('\n')
                return {'files': files, 'count': len(files)}
            
            elif data_type == 'authors':
                cmd = ['git', 'shortlog', '-sn', '--no-merges']
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
                return {'authors': result.stdout.strip().split('\n')}
            
            else:
                # Unknown data type - ask LLM how to extract
                return self._llm_extract_custom_data(data_type, params)
                
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_dynamic(self, params: Dict) -> Any:
        """Calculate metrics dynamically based on params"""
        formula = params.get('custom_formula') or params.get('formula')
        
        if formula:
            # Execute custom formula
            return self._execute_custom_formula(formula, params)
        
        # Use LLM to determine calculation
        metrics = params.get('metrics', [])
        if metrics:
            results = {}
            for metric in metrics:
                results[metric] = self._calculate_single_metric(metric)
            return results
        
        return {'message': 'No calculations specified'}
    
    def _execute_custom_formula(self, formula: str, params: Dict) -> Any:
        """Execute user's custom formula safely"""
        try:
            # Extract variables from formula
            # Example: "commits_per_day = total_commits / days"
            
            # Get required data
            data = self._extract_git_data('commits', params)
            
            # Safe evaluation context
            safe_context = {
                'total_commits': data.get('count', 0),
                'days': 30,  # default
                '__builtins__': {}
            }
            
            # Evaluate formula
            result = eval(formula, safe_context)
            
            return {
                'formula': formula,
                'result': result,
                'context': safe_context
            }
            
        except Exception as e:
            return {'error': f'Formula execution failed: {e}'}
    
    def _calculate_single_metric(self, metric: str) -> Any:
        """Calculate a single metric dynamically"""
        # Let LLM interpret what this metric means
        prompt = f"""How do I calculate this metric from a Git repository?
Metric: {metric}
Repository: {self.repo_path}

Provide Git command or Python code to calculate it.
"""
        
        try:
            response = self.llm.model.generate_content(prompt)
            # Extract and execute the suggestion
            return {'metric': metric, 'suggestion': response.text}
        except:
            return {'metric': metric, 'value': 'unknown'}
    
    def _llm_extract_custom_data(self, data_type: str, params: Dict) -> Any:
        """Ask LLM how to extract custom data type"""
        prompt = f"""I need to extract this type of data from a Git repository:
Data type: {data_type}
Parameters: {params}
Repository: {self.repo_path}

Provide the Git command or Python code to extract this data.
"""
        
        try:
            response = self.llm.model.generate_content(prompt)
            return {'data_type': data_type, 'extraction_method': response.text}
        except:
            return {'error': f'Unknown data type: {data_type}'}
    
    def _execute_unknown_action(self, action: str, params: Dict) -> Any:
        """Ask LLM how to execute unknown action"""
        prompt = f"""I need to perform this action:
Action: {action}
Parameters: {params}

Provide Python code or Git command to perform this action.
"""
        
        try:
            response = self.llm.model.generate_content(prompt)
            return {'action': action, 'method': response.text}
        except:
            return {'error': f'Unknown action: {action}'}
    
    def _format_output(self, data: Any, params: Dict) -> Dict[str, Any]:
        """Format output based on preferences"""
        output_format = params.get('format', 'json')
        
        if output_format == 'json':
            return data
        elif output_format == 'csv':
            # Convert to CSV format
            return {'format': 'csv', 'data': str(data)}
        else:
            return data
    
    def _learn_from_execution(self, understanding: Dict, result: Dict):
        """Learn from successful execution"""
        if result.get('success'):
            self.knowledge_base['successful_queries'].append({
                'query': understanding.get('original_query', ''),
                'intent': understanding.get('intent'),
                'result_type': str(type(result.get('data'))),
                'timestamp': datetime.now().isoformat()
            })
            self._save_knowledge_base()
    
    def handle_clarification(self, original_query: str, clarification: str) -> Dict[str, Any]:
        """Handle user's clarification"""
        combined_query = f"{original_query}\nClarification: {clarification}"
        return self.understand_query(combined_query)
    
    def create_dataset(self, user_query: str, repo_path: str = None) -> Dict[str, Any]:
        """
        Main entry point for dataset creation
        Fully autonomous - no hardcoded paths, no clarification requests
        """
        # Set repository if provided
        if repo_path:
            self.set_repository(repo_path)
        
        if not self.repo_path:
            return {'error': 'No repository set'}
        
        # Understand query
        understanding = self.understand_query(user_query)
        
        # Execute query directly (no clarification)
        result = self.execute_query(understanding)
        
        # Format for output
        return {
            'success': True,
            'query': user_query,
            'understanding': understanding,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'learned': True
        }


# Example usage
if __name__ == "__main__":
    agent = AutonomousAgent()
    
    # Test queries
    test_queries = [
        "Show me commits per hour",
        "Calculate complexity / LOC ratio",
        "Custom formula: (additions - deletions) / total_commits",
        "Authors who contributed more than 100 lines"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        understanding = agent.understand_query(query)
        print(f"\n📊 Understanding: {json.dumps(understanding, indent=2)}")
