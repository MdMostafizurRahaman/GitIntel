"""
Multi-LLM Jury System for Dynamic Code Generation
- 1 Generator LLM: Writes code for ANY user formula
- 3 Verifier LLMs: Check code correctness
- Temporary execution: Code runs then gets deleted
- ZERO hardcoded formulas
- Auto-fallback: Gemini → AWS Bedrock (when quota exceeded)
"""

import google.generativeai as genai
import tempfile
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import json
import hashlib

# Import AWS provider
try:
    from aws_llm_provider import MultiProviderLLM
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    print("[WARNING] AWS provider not available. Install boto3: pip install boto3")

class LLMCodeJurySystem:
    """
    Multi-LLM system where:
    - Generator creates code dynamically
    - 3 Verifiers check correctness
    - Code executes and self-destructs
    """
    
    def __init__(self, generator_key: str, jury_keys: List[str] = None, use_aws_fallback: bool = True):
        """
        Initialize Multi-LLM Jury System with AWS fallback
        
        Args:
            generator_key: Gemini API key for generator
            jury_keys: List of 3 Gemini API keys for verifiers
            use_aws_fallback: If True, use AWS Bedrock when Gemini quota exceeded
        """
        # Initialize multi-provider (Gemini + AWS fallback)
        self.use_aws_fallback = use_aws_fallback and AWS_AVAILABLE
        
        if self.use_aws_fallback:
            try:
                self.multi_provider = MultiProviderLLM()
                print(f"[OK] Multi-provider enabled: {self.multi_provider.get_active_provider()}")
            except Exception as e:
                print(f"[WARNING] Multi-provider init failed: {e}. Using Gemini only.")
                self.use_aws_fallback = False
        
        # Configure generator with working model
        genai.configure(api_key=generator_key)
        self.generator = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
        self.generator_key = generator_key
        
        # Configure 3 verifiers with separate keys if provided
        if jury_keys and len(jury_keys) >= 3:
            self.verifier_1 = self._create_model_with_key(jury_keys[0])
            self.verifier_2 = self._create_model_with_key(jury_keys[1])
            self.verifier_3 = self._create_model_with_key(jury_keys[2])
            self.jury_keys = jury_keys
        else:
            # Use same key if no separate keys
            self.verifier_1 = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
            self.verifier_2 = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
            self.verifier_3 = genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
            self.jury_keys = [generator_key] * 3
        
        self.temp_code_dir = Path(tempfile.gettempdir()) / 'llm_generated_code'
        self.temp_code_dir.mkdir(exist_ok=True)
        
        print(f"[OK] Multi-LLM Jury System initialized (AWS fallback: {self.use_aws_fallback})")
    
    def _create_model_with_key(self, api_key: str):
        """Create model with specific API key"""
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('models/gemini-2.5-flash-lite-preview-09-2025')
        print(f"   Generator: Ready")
        print(f"   Verifiers: 3 active")
        print(f"   Temp code dir: {self.temp_code_dir}")
    
    def understand_user_request(self, user_query: str) -> Dict[str, Any]:
        """
        LLM understands user's intent and extracts formula requirements
        NO HARDCODING - pure LLM understanding
        """
        print(f"\n Understanding user request with LLM...")
        
        prompt = f"""Analyze this user request and extract information:

User Request:
{user_query}

Extract and return as JSON:
{{
  "intent": "what user wants (dataset/analysis/calculation)",
  "formulas": [
    {{
      "name": "formula_name",
      "description": "what it measures",
      "expression": "mathematical formula",
      "required_columns": ["col1", "col2"]
    }}
  ],
  "data_source": "where to get data (repository/file/mock)",
  "output_format": "csv/json/excel"
}}

Be comprehensive - extract ALL formulas mentioned (even if 100+).
Return ONLY valid JSON."""

        try:
            # Try Gemini first
            response = self.generator.generate_content(prompt)
            
            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                understanding = json.loads(json_match.group())
                print(f" Understood: {understanding.get('intent', 'unknown')}")
                print(f"   Formulas detected: {len(understanding.get('formulas', []))}")
                return understanding
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if quota exceeded
            if ('quota' in error_msg or '429' in error_msg) and self.use_aws_fallback:
                print(f" Gemini quota exceeded. Using AWS Bedrock fallback...")
                try:
                    aws_response = self.multi_provider.generate_content(prompt)
                    import re
                    json_match = re.search(r'\{.*\}', aws_response['text'], re.DOTALL)
                    if json_match:
                        understanding = json.loads(json_match.group())
                        print(f" [AWS] Understood: {understanding.get('intent', 'unknown')}")
                        print(f"   Formulas detected: {len(understanding.get('formulas', []))}")
                        return understanding
                except Exception as aws_error:
                    print(f" AWS fallback failed: {aws_error}")
            
            print(f" Understanding failed: {e}")
        
        return {"intent": "unknown", "formulas": [], "data_source": "unknown"}
    
    def generate_code(self, formulas: List[Dict], available_data: pd.DataFrame) -> str:
        """
        Generator LLM: Creates Python code to calculate formulas
        Code is generated fresh for each request - NO TEMPLATES
        """
        print(f"\n Generator LLM: Writing code for {len(formulas)} formulas...")
        
        # Prepare context
        data_columns = list(available_data.columns)
        sample_row = available_data.iloc[0].to_dict() if len(available_data) > 0 else {}
        
        formulas_text = "\n".join([
            f"{i+1}. {f['name']}: {f['expression']}"
            for i, f in enumerate(formulas)
        ])
        
        prompt = f"""Generate Python code to calculate these formulas on a pandas DataFrame.

Available DataFrame columns: {', '.join(data_columns)}
Sample data: {sample_row}

Formulas to implement:
{formulas_text}

Requirements:
1. Function signature: def calculate_formulas(df: pd.DataFrame) -> pd.DataFrame
2. Add new columns to df for each formula
3. Handle missing columns gracefully (skip or use alternatives)
4. Use numpy for math operations (import numpy as np)
5. Return modified DataFrame with new formula columns

Generate ONLY the function code, no explanation.
Make it production-ready with error handling."""

        try:
            # Try Gemini first
            response = self.generator.generate_content(prompt)
            
            # Extract code from response
            code = self._extract_code_from_response(response.text)
            
            print(f" Code generated ({len(code)} chars)")
            return code
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if quota exceeded
            if ('quota' in error_msg or '429' in error_msg) and self.use_aws_fallback:
                print(f" Gemini quota exceeded. Using AWS Bedrock fallback...")
                try:
                    aws_response = self.multi_provider.generate_content(prompt)
                    code = self._extract_code_from_response(aws_response['text'])
                    print(f" [AWS] Code generated ({len(code)} chars)")
                    return code
                except Exception as aws_error:
                    print(f" AWS fallback failed: {aws_error}")
            
            print(f" Code generation failed: {e}")
            return ""
    
    def verify_code_with_jury(self, code: str, formulas: List[Dict]) -> Dict[str, Any]:
        """
        3 Verifier LLMs check the generated code
        Majority vote decides if code is acceptable
        """
        print(f"\n Jury verification (3 verifiers)...")
        
        formulas_text = "\n".join([f"{f['name']}: {f['expression']}" for f in formulas])
        
        verification_prompt = f"""Verify this generated code for correctness and safety.

Required formulas:
{formulas_text}

Generated code:
```python
{code}
```

Check:
1. All formulas correctly implemented?
2. Safe to execute (no malicious code)?
3. Proper error handling?
4. Logic is sound?

Return JSON:
{{
  "verdict": "APPROVE" or "REJECT",
  "confidence": 0.0 to 1.0,
  "issues": ["list of issues if any"],
  "reasoning": "brief explanation"
}}

Return ONLY valid JSON."""

        verifiers = [
            ("Verifier 1 (Correctness)", self.verifier_1),
            ("Verifier 2 (Safety)", self.verifier_2),
            ("Verifier 3 (Logic)", self.verifier_3)
        ]
        
        votes = []
        for name, verifier in verifiers:
            try:
                # Try Gemini verifier first
                response = verifier.generate_content(verification_prompt)
                
                # Parse verdict
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    verdict = json.loads(json_match.group())
                    votes.append((name, verdict))
                    
                    status = "" if verdict['verdict'] == 'APPROVE' else ""
                    print(f"  {status} {name}: {verdict['verdict']} (confidence: {verdict['confidence']:.2f})")
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if quota exceeded, try AWS fallback
                if ('quota' in error_msg or '429' in error_msg) and self.use_aws_fallback:
                    print(f"  {name}: Gemini quota exceeded, using AWS...")
                    try:
                        aws_response = self.multi_provider.generate_content(verification_prompt)
                        import re
                        json_match = re.search(r'\{.*\}', aws_response['text'], re.DOTALL)
                        if json_match:
                            verdict = json.loads(json_match.group())
                            votes.append((name, verdict))
                            status = "" if verdict['verdict'] == 'APPROVE' else ""
                            print(f"  {status} {name} [AWS]: {verdict['verdict']} (confidence: {verdict['confidence']:.2f})")
                        else:
                            raise Exception("Could not parse AWS response")
                    except Exception as aws_error:
                        print(f"  {name}: AWS fallback failed - {aws_error}")
                        votes.append((name, {"verdict": "REJECT", "confidence": 0.0, "issues": [str(aws_error)]}))
                else:
                    print(f"   {name}: Verification error - {e}")
                    votes.append((name, {"verdict": "REJECT", "confidence": 0.0, "issues": [str(e)]}))
        
        # Majority vote
        approvals = sum(1 for _, v in votes if v['verdict'] == 'APPROVE')
        total = len(votes)
        
        jury_result = {
            "approved": approvals >= 2,  # Need 2/3 approval
            "votes": votes,
            "approval_rate": approvals / total if total > 0 else 0
        }
        
        print(f"\n   Jury Result: {approvals}/{total} approved")
        
        return jury_result
    
    def execute_temporary_code(self, code: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute generated code in temporary file
        Code is deleted immediately after execution
        """
        print(f"\n Executing temporary code...")
        
        # Create unique temporary file
        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        temp_file = self.temp_code_dir / f"temp_formulas_{code_hash}.py"
        
        try:
            # Write code to temp file
            with open(temp_file, 'w') as f:
                f.write("import pandas as pd\n")
                f.write("import numpy as np\n\n")
                f.write(code)
            
            print(f"   Temp file: {temp_file.name}")
            
            # Execute code
            import importlib.util
            spec = importlib.util.spec_from_file_location("temp_module", temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Call the generated function
            result_df = module.calculate_formulas(df.copy())
            
            print(f"   Execution successful")
            print(f"   New columns added: {len(result_df.columns) - len(df.columns)}")
            
            return result_df
            
        except Exception as e:
            print(f"   Execution failed: {e}")
            return df
        
        finally:
            # ALWAYS delete temporary code
            if temp_file.exists():
                temp_file.unlink()
                print(f"   Temporary code deleted")
    
    def process_user_request(self, user_query: str, data: pd.DataFrame) -> pd.DataFrame:
        """
        Complete workflow:
        1. LLM understands request
        2. Generator creates code
        3. 3 Verifiers check code
        4. Execute and delete code
        5. Return enhanced data
        """
        print(f"="*80)
        print(f"MULTI-LLM JURY SYSTEM - DYNAMIC CODE GENERATION")
        print(f"="*80)
        
        # Step 1: Understand request
        understanding = self.understand_user_request(user_query)
        
        formulas = understanding.get('formulas', [])
        if not formulas:
            print(f" No formulas detected in request")
            return data
        
        # Step 2: Generate code
        code = self.generate_code(formulas, data)
        
        if not code:
            print(f" Code generation failed")
            return data
        
        # Step 3: Jury verification
        jury_result = self.verify_code_with_jury(code, formulas)
        
        if not jury_result['approved']:
            print(f"\n Jury REJECTED code - not safe to execute")
            return data
        
        print(f"\n Jury APPROVED code ({jury_result['approval_rate']:.0%} approval)")
        
        # Step 4: Execute and self-destruct
        enhanced_data = self.execute_temporary_code(code, data)
        
        print(f"\n{'='*80}")
        print(f" COMPLETE - No code persisted, all temporary files deleted")
        print(f"{'='*80}")
        
        return enhanced_data
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Extract Python code from LLM response"""
        import re
        
        # Try to find code between ```python and ```
        code_match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Try to find code between ``` and ```
        code_match = re.search(r'```\n(.*?)```', response_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # If no code blocks, try to find function definition
        func_match = re.search(r'(def calculate_formulas.*)', response_text, re.DOTALL)
        if func_match:
            return func_match.group(1).strip()
        
        return response_text.strip()


# Example usage
if __name__ == '__main__':
    # Get API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print(" GOOGLE_API_KEY not set")
        exit(1)
    
    # Initialize system
    jury = LLMCodeJurySystem(api_key)
    
    # Sample data
    sample_data = pd.DataFrame({
        'lines_of_code': [100, 200, 150, 300],
        'cbo': [5, 8, 6, 10],
        'wmc': [10, 15, 12, 20],
        'bug_count': [2, 5, 3, 8],
        'commit_count': [50, 100, 75, 150]
    })
    
    # User request (completely dynamic)
    user_request = """
I want these quality metrics:

1. Bug Density: bug_count / (lines_of_code / 1000)
2. Coupling Risk: cbo / 10
3. Complexity Score: wmc / lines_of_code * 100
4. Bug Fix Rate: bug_count / commit_count
"""
    
    # Process request
    result = jury.process_user_request(user_request, sample_data)
    
    print(f"\n Result DataFrame:")
    print(result)
