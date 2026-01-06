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
        
        # Identify what types of metrics are needed
        git_metrics = ['lines_added', 'lines_deleted', 'commit_count', 'commits_per_file', 'author_count']
        code_metrics = ['code_smells', 'cyclomatic_complexity', 'cognitive_complexity']
        
        # Check which metrics are needed for each formula
        metrics_needed = set()
        for formula in formulas:
            expr = formula.get('expression', '') + formula.get('name', '')
            required = formula.get('required_columns', [])
            
            # Check which metrics are mentioned in expression
            for metric in data_columns + git_metrics + code_metrics:
                if metric.lower() in expr.lower():
                    metrics_needed.add(metric)
            metrics_needed.update(required)
        
        # Separate by type
        needed_git = [m for m in metrics_needed if m in git_metrics]
        needed_code = [m for m in metrics_needed if m in code_metrics]
        needed_other = [m for m in metrics_needed if m not in git_metrics and m not in code_metrics]
        
        formulas_text = "\n".join([
            f"{i+1}. {f['name']}: {f['expression']}"
            for i, f in enumerate(formulas)
        ])
        
        git_section = ""
        if needed_git:
            git_section = f"\n**CRITICAL: This formula requires git-based metrics: {needed_git}**\nYou MUST use subprocess to query the git repository for these metrics!"
        
        prompt = f"""Generate Python code to calculate these formulas on a pandas DataFrame.

Available DataFrame columns: {', '.join(data_columns)}
Sample data: {sample_row}

Metrics needed for formulas: {sorted(metrics_needed)}{git_section}

Formulas to implement:
{formulas_text}

CRITICAL REQUIREMENTS:
1. Function signature: def calculate_formulas(df: pd.DataFrame, repo_path: str = None, progress_callback=None) -> pd.DataFrame

2. **MUST CREATE ALL COLUMNS USED IN FORMULAS** before calculating them!
   - For COMPLEX formulas: Break into STEPS and create INTERMEDIATE columns!
   - Example: "code_smells / (lines_of_code / 1000)"
     STEP 1: Create 'code_smells' column
     STEP 2: Create 'lines_of_code' column
     STEP 3: Create 'lines_of_code_per_1000' = lines_of_code / 1000 (INTERMEDIATE)
     STEP 4: Create 'code_smell_density' = code_smells / lines_of_code_per_1000 (FINAL)
   - Each intermediate calculation MUST have its own column in the DataFrame
   - Naming: Use descriptive names like 'metric_name_step_description'
   - Example: 'loc_normalized', 'complexity_scaled', 'ratio_calculated'
   - Do NOT discard intermediate values - they become visible columns in CSV

3. **For metrics like 'lines_added' and 'lines_deleted', MUST query git:**
   
   EXAMPLE - Extract lines added/deleted from git numstat:
   ```python
   def extract_lines_added_deleted(file_path, repo_path):
       '''Extract total lines added and deleted from git history'''
       try:
           result = subprocess.run(
               ['git', 'log', '--numstat', '--follow', '--', file_path],
               cwd=repo_path,
               capture_output=True,
               text=True,
               timeout=10
           )
           
           if result.returncode == 0:
               added = deleted = 0
               for line in result.stdout.strip().split('\\n'):
                   if '\\t' in line:
                       parts = line.split('\\t')
                       if len(parts) >= 2:
                           try:
                               added += int(parts[0]) if parts[0] != '-' else 0
                               deleted += int(parts[1]) if parts[1] != '-' else 0
                           except:
                               pass
               return added, deleted
       except:
           pass
       
       return 0, 0
   
   # In main function:
   for idx, row in df.iterrows():
       added, deleted = extract_lines_added_deleted(row['file'], repo_path)
       df.at[idx, 'lines_added'] = added
       df.at[idx, 'lines_deleted'] = deleted
   ```

4. For git-based metrics, use PARALLEL execution for speed (100 files in seconds, not minutes):
   
   EXAMPLE - Parallel git query with ThreadPoolExecutor:
   ```python
   import subprocess
   import os
   from concurrent.futures import ThreadPoolExecutor, as_completed
   
   def query_git_for_file(idx, file_path, repo_path):
       '''Query git for single file - runs in parallel thread'''
       try:
           result = subprocess.run(
               ['git', 'log', '--oneline', '--follow', '--', file_path],
               cwd=repo_path,
               capture_output=True,
               text=True,
               timeout=10
           )
           if result.returncode == 0 and result.stdout.strip():
               commits = [line for line in result.stdout.strip().split('\\n') if line]
               return idx, len(commits)
           return idx, 0
       except Exception:
           return idx, 0
   
   # Run git queries in parallel (FAST!)
   with ThreadPoolExecutor(max_workers=10) as executor:
       futures = {{executor.submit(query_git_for_file, idx, row['file'], repo_path): idx 
                  for idx, row in df.iterrows()}}
       
       completed = 0
       for future in as_completed(futures):
           idx, commit_count = future.result()
           df.at[idx, 'commit_count'] = commit_count
           completed += 1
           
           # Progress update every 10 files
           if progress_callback and completed % 10 == 0:
               progress_callback(completed, len(df), f"Processed {{completed}} files")
   
   if progress_callback:
       progress_callback(len(df), len(df), "Complete!")
   ```
   
   EXAMPLE - Multiple git queries per file (authors + commits):
   ```python
   def query_git_multi(idx, file_path, repo_path):
       commits = authors = 0
       try:
           # Query 1: Total commits
           r1 = subprocess.run(['git', 'log', '--oneline', '--', file_path],
                             cwd=repo_path, capture_output=True, text=True, timeout=10)
           if r1.returncode == 0 and r1.stdout.strip():
               commits = len([l for l in r1.stdout.strip().split('\\n') if l])
           
           # Query 2: Author count
           r2 = subprocess.run(['git', 'shortlog', '-s', '--', file_path],
                             cwd=repo_path, capture_output=True, text=True, timeout=10)
           if r2.returncode == 0 and r2.stdout.strip():
               authors = len([l for l in r2.stdout.strip().split('\\n') if l])
       except Exception:
           pass
       return idx, commits, authors
   
   with ThreadPoolExecutor(max_workers=10) as executor:
       futures = [executor.submit(query_git_multi, idx, row['file'], repo_path) 
                  for idx, row in df.iterrows()]
       for future in as_completed(futures):
           idx, commits, authors = future.result()
           df.at[idx, 'commits'] = commits
           df.at[idx, 'authors'] = authors
   ```

3. ALWAYS use ThreadPoolExecutor with max_workers=10 for git queries (parallel = FAST!)
4. Each git query runs in separate thread - no blocking!
5. Progress updates via progress_callback(current, total, message)
6. Timeout=10 for each subprocess call
7. Handle errors gracefully, return 0/NaN on failures
8. Import: import subprocess, os, numpy as np, from concurrent.futures import ThreadPoolExecutor, as_completed

9. **CRITICAL: Return df with ALL required columns created!**
   - Before applying any formula, ALL columns referenced must exist in df
   - If formula uses col_a / col_b → Both col_a AND col_b must be columns in returned df
   - Do NOT try to compute formula on columns that don't exist yet
   - Sequence: Create columns → Apply formula → Return df

Generate ONLY the function code. NO explanations. Just Python code.
MUST use parallel execution - DO NOT use iterrows() loop with blocking subprocess!"""

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
1. **CRITICAL: All columns used in formulas exist in DataFrame BEFORE formula is applied?**
   - For formula "a / b" → both 'a' and 'b' must be created as df columns first
   - For complex formulas: ALL intermediate steps must be columns too!
   - Example: "x / (y / 1000)" should create: 'x', 'y', 'y_normalized', 'result'
   - REJECT if code tries to use undefined columns
   
2. **CRITICAL: All non-standard metrics properly extracted?**
   - If formula contains 'lines_added', 'lines_deleted', 'commit_count': MUST use git commands
   - If formula contains 'code_smells', 'cyclomatic_complexity': MUST extract from code analysis
   - REJECT if code creates columns with all zeros without actual extraction
   
3. All formulas correctly implemented?
4. Safe to execute (no malicious code)?
5. Proper error handling for git/file operations?
6. Logic is sound?
7. Returns df with all required columns populated (including intermediates)?

Return JSON:
{{
  "verdict": "APPROVE" or "REJECT",
  "confidence": 0.0 to 1.0,
  "issues": ["list of issues if any"],
  "reasoning": "brief explanation - note what metrics are being extracted"
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
