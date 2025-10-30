#!/usr/bin/env python3
"""
LLM-Powered Git Repository Analysis Engine
Supports natural language commands for automated analysis and reporting.
"""

import os
import json
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from pathlib import Path
import subprocess
import tempfile
import traceback
from pydriller import Repository
import re
import javalang
import radon.complexity as radon_cc
from radon.raw import analyze
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional

class LLMGitAnalyzer:
    def __init__(self):
        self.setup_environment()
        self.setup_gemini()
        self.current_repo_path = None
        self.available_tools = {
            'package_churn': 'Analyze package-level code changes and churn',
            'loc_analysis': 'Lines of code analysis by package/file',
            'complexity_analysis': 'Cyclomatic complexity analysis',
            'commit_analysis': 'Detailed commit history analysis',
            'release_analysis': 'Release-based change analysis',
            'loc_time_ratio': 'LOC to time ratio analysis',
            'complexity_time_ratio': 'Complexity to time ratio analysis',
            'combined_analysis': 'Combined metrics analysis (LOC + complexity + time)',
            'custom_analysis': 'Custom formula-based analysis',
            'visualization': 'Generate charts and visualizations'
        }
        
    def setup_environment(self):
        """Setup environment variables"""
        from dotenv import load_dotenv
        load_dotenv()
        
    def setup_gemini(self):
        """Setup Google Gemini AI"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        # Try different model names for compatibility
        model_names = ['gemini-pro-latest', 'gemini-flash-latest', 'gemini-1.5-flash-latest', 'gemini-1.5-pro-latest']
        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(model_name)
                print(f"✅ Gemini model set: {model_name}")
                break
            except Exception as e:
                print(f"Model {model_name} not available: {e}")
                continue
        if not self.model:
            print("⚠️ No Gemini model available, using fallback analysis.")
            # List available models for debugging
            try:
                available_models = genai.list_models()
                print("Available Gemini models:")
                for m in available_models:
                    print(f"- {m.name} (methods: {m.supported_generation_methods})")
            except Exception as e:
                print(f"Error listing Gemini models: {e}")
            self.model = None
        
    def process_natural_language_command(self, user_command: str) -> Dict[str, Any]:
        """Process natural language command using Gemini AI"""
        
        system_prompt = f"""
        You are an expert Git repository analysis assistant that understands Bengali and English commands naturally.
        
        Available analysis tools and their purposes:
        - package_churn: Analyzes code changes (additions/removals) by Java package, filtered by threshold
        - loc_analysis: Counts lines of code (LOC) for each package and file
        - complexity_analysis: Measures cyclomatic complexity and code complexity metrics
        - release_analysis: Analyzes changes between Git release tags
        - loc_time_ratio: Calculates LOC per day ratio for packages over time
        - complexity_time_ratio: Calculates complexity per day ratio for packages over time
        - combined_analysis: Combines multiple metrics (LOC, complexity, time ratios) in one analysis
        - file_class_analysis: Lists files by package and counts classes/interfaces in each file
        - custom_analysis: Executes custom calculations or formulas
        
        Current repository: {self.current_repo_path or "Not set"}
        
        User command: "{user_command}"
        
        UNDERSTAND the user's intent completely. Map natural language to the correct analysis_type:
        
        Combined/Time Ratio Analysis:
        - Commands about "complexity ratio with time", "LOC and complexity over time", "multiple metrics with time"
        - Commands combining metrics: "complexity r time ratio", "LOC r complexity dekhao"
        - Bengali: "complexity r time er ratio", "LOC complexity milaye dekhao"
        
        LOC/Time Analysis:
        - Commands about "ratio of LOC to time", "LOC per day", "lines of code over time", "development speed"
        - Bengali: "LOC er time ratio", "din proti LOC", "code development speed"
        
        Complexity/Time Analysis:
        - Commands about "complexity over time", "complexity per day", "complexity ratio with time"
        - Bengali: "complexity time ratio", "din proti complexity"
        
        Package Churn Analysis:
        - Commands about "code changes", "churn", "additions/removals", "package modifications"
        - Bengali: "code change", "package er modification", "add/remove analysis"
        
        LOC Analysis:
        - Commands about "lines of code", "LOC count", "code size", "package sizes"
        - Bengali: "line of code", "code er size", "package wise LOC"
        
        File/Class Analysis:
        - Commands about "files in package", "class count", "files and classes", "file names with class count"
        - Bengali: "package wise files", "file e kota class", "files name r class count", "file class analysis"
        
        Complexity Analysis:
        - Commands about "complexity", "code complexity", "cyclomatic complexity"
        - Bengali: "complexity", "code er complexity", "jati complexity"
        
        Release Analysis:
        - Commands about "releases", "versions", "tags", "version changes"
        - Bengali: "release", "version", "tag analysis"
        
        Custom Analysis:
        - Commands with formulas, calculations, or specific metrics
        - Bengali: "custom calculation", "formula apply", "specific metric"
        
        Return ONLY valid JSON with this exact structure:
        {{
            "analysis_type": "MUST be one of: package_churn, loc_analysis, complexity_analysis, release_analysis, loc_time_ratio, complexity_time_ratio, combined_analysis, custom_analysis",
            "parameters": {{
                "threshold": 500,
                "output_format": "excel",
                "custom_formula": "if custom analysis",
                "time_range": "if applicable",
                "combine_metrics": ["loc", "complexity"] // for combined analysis
            }},
            "description": "Clear description in English of what will be analyzed",
            "code_to_execute": null
        }}
        
        Examples:
        - "Show me the ratio of LOC to time for each package" → {{"analysis_type": "loc_time_ratio"}}
        - "Package wise code changes over 500 lines" → {{"analysis_type": "package_churn", "parameters": {{"threshold": 500}}}}
        - "How many lines of code in each package?" → {{"analysis_type": "loc_analysis"}}
        - "Analyze code complexity" → {{"analysis_type": "complexity_analysis"}}
        - "Changes between releases" → {{"analysis_type": "release_analysis"}}
        - "Show complexity ratio with time" → {{"analysis_type": "complexity_time_ratio"}}
        - "Show LOC and complexity together with time ratios" → {{"analysis_type": "combined_analysis", "parameters": {{"combine_metrics": ["loc", "complexity", "time"]}}}}
        - "Calculate custom metric: additions - deletions" → {{"analysis_type": "custom_analysis", "parameters": {{"custom_formula": "additions - deletions"}}}}
        
        THINK STEP BY STEP:
        1. Identify the main topic (LOC, churn, complexity, releases, time ratios)
        2. Map to the correct analysis_type
        3. Extract any parameters (thresholds, formulas, etc.)
        4. Provide clear description
        
        If unsure, choose the closest matching analysis_type rather than failing.
        """
        
        try:
            if not self.model:
                raise Exception("No Gemini model available")
            response = self.model.generate_content(system_prompt)
            # Clean the response - remove markdown code blocks
            raw_text = response.text.strip()
            if raw_text.startswith('```json'):
                raw_text = raw_text[7:]
            if raw_text.endswith('```'):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()
            
            result = json.loads(raw_text)
            return result
        except json.JSONDecodeError as je:
            print(f"JSON Parse Error: {je}")
            print(f"Raw response: '{response.text}'")
            raise Exception(f"LLM returned invalid JSON. Please try rephrasing your request.")
        except Exception as e:
            print(f"LLM processing error: {e}")
            # No fallback - let the user know LLM failed
            raise Exception(f"LLM could not process command. Please try rephrasing your request.")
    
    def set_repository(self, repo_path: str):
        """Set the repository path for analysis"""
        if os.path.exists(repo_path) and os.path.exists(os.path.join(repo_path, '.git')):
            self.current_repo_path = repo_path
            print(f"✅ Repository set: {repo_path}")
            return True
        else:
            print(f"❌ Invalid repository path: {repo_path}")
            return False
    
    def detect_package_from_source(self, src_text: str) -> Optional[str]:
        """Extract package name from Java source code"""
        if not src_text:
            return None
        
        # Try regex first for speed
        m = re.search(r'^\s*package\s+([a-zA-Z0-9_.]+)\s*;', src_text, re.MULTILINE)
        if m:
            return m.group(1)
        
        # Fallback to javalang for robustness
        try:
            tree = javalang.parse.parse(src_text)
            if getattr(tree, 'package', None):
                return tree.package.name
        except Exception:
            pass
        
        return None
    
    def package_from_filepath(self, filepath: str) -> str:
        """Infer package name from file path"""
        if not filepath:
            return '<<unknown>>'
        
        # Normalize path separators
        parts = filepath.replace('\\', '/').split('/')
        
        # Look for standard Java patterns
        if 'src' in parts:
            try:
                src_idx = parts.index('src')
                if len(parts) > src_idx + 2 and parts[src_idx + 1] == 'main' and parts[src_idx + 2] == 'java':
                    pkg_parts = parts[src_idx + 3:-1]  # exclude filename
                else:
                    pkg_parts = parts[src_idx + 1:-1]
                
                if pkg_parts:
                    return '.'.join(pkg_parts)
            except ValueError:
                pass
        
        # Fallback: use directory structure
        dir_path = os.path.dirname(filepath)
        if dir_path:
            return dir_path.replace('/', '.').replace('\\', '.')
        
        return '<<unknown>>'
    
    def analyze_package_churn(self, threshold: int = 500, output_format: str = 'excel') -> str:
        """Analyze package-level code churn"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print(f"🔍 Analyzing package churn (threshold: {threshold} lines)...")
        
        rows = []
        commit_count = 0
        
        try:
            for commit in Repository(self.current_repo_path).traverse_commits():
                commit_count += 1
                if commit_count % 50 == 0:
                    print(f"  Processed {commit_count} commits...")
                
                commit_hash = commit.hash
                commit_date = commit.author_date.isoformat()
                author = commit.author.name
                message = commit.msg.replace('\n', ' ').replace('\r', ' ')[:200]
                
                per_pkg = {}
                
                for mod in commit.modified_files:
                    if not (mod.filename and mod.filename.endswith('.java')):
                        continue
                    
                    added = mod.added_lines or 0
                    removed = mod.deleted_lines or 0  # Changed from removed_lines to deleted_lines
                    churn = added + removed
                    
                    if churn == 0:
                        continue
                    
                    # Determine package name
                    pkg = None
                    if mod.source_code:
                        pkg = self.detect_package_from_source(mod.source_code)
                    
                    if not pkg:
                        file_path = mod.new_path or mod.old_path or mod.filename
                        pkg = self.package_from_filepath(file_path)
                    
                    if not pkg:
                        pkg = '<<unknown>>'
                    
                    # Aggregate by package
                    if pkg not in per_pkg:
                        per_pkg[pkg] = {
                            'added': 0, 'removed': 0, 'churn': 0, 'files': set()
                        }
                    
                    per_pkg[pkg]['added'] += added
                    per_pkg[pkg]['removed'] += removed
                    per_pkg[pkg]['churn'] += churn
                    per_pkg[pkg]['files'].add(mod.new_path or mod.old_path or mod.filename)
                
                # Filter by threshold
                for pkg, metrics in per_pkg.items():
                    if metrics['churn'] >= threshold:
                        rows.append({
                            'repository': os.path.basename(self.current_repo_path),
                            'commit': commit_hash,
                            'date': commit_date,
                            'author': author,
                            'message': message,
                            'package': pkg,
                            'lines_added': metrics['added'],
                            'lines_removed': metrics['removed'],
                            'churn': metrics['churn'],
                            'num_files': len(metrics['files']),
                            'files_changed': '|'.join(list(metrics['files'])[:10]),  # Limit for Excel
                            'threshold_exceeded': True
                        })
            
            print(f"✅ Processed {commit_count} commits, found {len(rows)} packages exceeding threshold")
            
            # Create output
            if rows:
                df = pd.DataFrame(rows)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"package_churn_analysis_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    filename = f"package_churn_analysis_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Analysis complete! Report saved: {filename}"
            else:
                return f"❌ No packages found exceeding {threshold} line threshold"
                
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"
    
    def analyze_loc(self, output_format: str = 'excel') -> str:
        """Analyze lines of code by package"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing lines of code...")
        
        loc_data = []
        
        try:
            # Walk through all Java files
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Get package name
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            # Simple LOC counting instead of radon (which is for Python)
                            lines = content.split('\n')
                            loc_count = len([line for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*') and not line.strip().startswith('*')])
                            
                            loc_data.append({
                                'file_path': rel_path,
                                'package': pkg,
                                'loc': loc_count,
                                'lloc': loc_count,  # Simplified
                                'sloc': loc_count,  # Simplified
                                'comments': len([line for line in lines if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*')]),
                                'multi': len([line for line in lines if '/*' in line or '*/' in line]),
                                'blank': len([line for line in lines if not line.strip()])
                            })
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if loc_data:
                df = pd.DataFrame(loc_data)
                
                # Package-level summary
                package_summary = df.groupby('package').agg({
                    'loc': 'sum',
                    'lloc': 'sum', 
                    'sloc': 'sum',
                    'comments': 'sum',
                    'blank': 'sum',
                    'file_path': 'count'
                }).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"loc_analysis_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                else:
                    filename = f"loc_analysis_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ LOC analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ LOC analysis failed: {str(e)}"
    
    def analyze_complexity(self, output_format: str = 'excel') -> str:
        """Analyze cyclomatic complexity"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing complexity...")
        
        complexity_data = []
        
        try:
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Get package name
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            # Analyze complexity (simplified for Java)
                            # Count decision points as proxy for complexity
                            decisions = len(re.findall(r'\b(if|while|for|switch|catch|&&|\|\|)\b', content))
                            methods = len(re.findall(r'\b(public|private|protected)\s+.*?\(.*?\)\s*{', content))
                            classes = len(re.findall(r'\bclass\s+\w+', content))
                            
                            complexity_data.append({
                                'file_path': rel_path,
                                'package': pkg,
                                'decision_points': decisions,
                                'methods': methods,
                                'classes': classes,
                                'complexity_score': decisions + methods * 2 + classes
                            })
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if complexity_data:
                df = pd.DataFrame(complexity_data)
                
                # Package-level summary
                package_summary = df.groupby('package').agg({
                    'decision_points': 'sum',
                    'methods': 'sum',
                    'classes': 'sum',
                    'complexity_score': 'sum',
                    'file_path': 'count'
                }).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"complexity_analysis_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                else:
                    filename = f"complexity_analysis_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Complexity analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ Complexity analysis failed: {str(e)}"
    
    def analyze_releases(self, output_format: str = 'excel') -> str:
        """Analyze changes by release tags"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing release changes...")
        
        try:
            # Get git tags
            result = subprocess.run(['git', 'tag', '--sort=-version:refname'], 
                                 cwd=self.current_repo_path, 
                                 capture_output=True, text=True)
            
            if result.returncode != 0:
                return "❌ Could not fetch git tags"
            
            tags = result.stdout.strip().split('\n')[:10]  # Last 10 releases
            if not tags or tags == ['']:
                return "❌ No git tags found in repository"
            
            release_data = []
            
            for i, tag in enumerate(tags):
                if i == len(tags) - 1:
                    # Last tag, compare with first commit
                    rev_range = tag
                else:
                    # Compare with previous tag
                    rev_range = f"{tags[i+1]}..{tag}"
                
                # Get commits in this range
                result = subprocess.run(['git', 'rev-list', '--count', rev_range], 
                                     cwd=self.current_repo_path, 
                                     capture_output=True, text=True)
                
                if result.returncode == 0:
                    commit_count = int(result.stdout.strip())
                else:
                    commit_count = 0
                
                # Get file changes
                result = subprocess.run(['git', 'diff', '--numstat', rev_range], 
                                     cwd=self.current_repo_path, 
                                     capture_output=True, text=True)
                
                total_added = total_removed = java_files = 0
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                try:
                                    added = int(parts[0]) if parts[0] != '-' else 0
                                    removed = int(parts[1]) if parts[1] != '-' else 0
                                    filepath = parts[2]
                                    
                                    total_added += added
                                    total_removed += removed
                                    
                                    if filepath.endswith('.java'):
                                        java_files += 1
                                except ValueError:
                                    continue
                
                release_data.append({
                    'release_tag': tag,
                    'commits': commit_count,
                    'lines_added': total_added,
                    'lines_removed': total_removed,
                    'total_churn': total_added + total_removed,
                    'java_files_changed': java_files
                })
            
            if release_data:
                df = pd.DataFrame(release_data)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"release_analysis_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    filename = f"release_analysis_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Release analysis complete! Report saved: {filename}"
            else:
                return "❌ No release data found"
                
        except Exception as e:
            return f"❌ Release analysis failed: {str(e)}"
    
    def analyze_complexity_time_ratio(self, output_format: str = 'excel') -> str:
        """Analyze complexity to time ratio for each package"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing complexity/time ratio...")
        
        package_data = {}
        
        try:
            # Get all commits to track package evolution over time
            for commit in Repository(self.current_repo_path).traverse_commits():
                commit_date = commit.author_date
                
                for mod in commit.modified_files:
                    if not (mod.filename and mod.filename.endswith('.java')):
                        continue
                    
                    # Get package name
                    pkg = None
                    if mod.source_code:
                        pkg = self.detect_package_from_source(mod.source_code)
                    
                    if not pkg:
                        file_path = mod.new_path or mod.old_path or mod.filename
                        pkg = self.package_from_filepath(file_path)
                    
                    if not pkg:
                        pkg = '<<unknown>>'
                    
                    # Track package metrics
                    if pkg not in package_data:
                        package_data[pkg] = {
                            'first_commit': commit_date,
                            'last_commit': commit_date,
                            'total_complexity': 0,
                            'files': set(),
                            'commits': 0
                        }
                    
                    # Update time range
                    if commit_date < package_data[pkg]['first_commit']:
                        package_data[pkg]['first_commit'] = commit_date
                    if commit_date > package_data[pkg]['last_commit']:
                        package_data[pkg]['last_commit'] = commit_date
                    
                    # Add current complexity if available
                    if mod.source_code:
                        try:
                            content = mod.source_code
                            decisions = len(re.findall(r'\b(if|while|for|switch|catch|&&|\|\|)\b', content))
                            methods = len(re.findall(r'\b(public|private|protected)\s+.*?\(.*?\)\s*{', content))
                            classes = len(re.findall(r'\bclass\s+\w+', content))
                            complexity_score = decisions + methods * 2 + classes
                            package_data[pkg]['total_complexity'] = max(package_data[pkg]['total_complexity'], complexity_score)
                        except:
                            pass
                    
                    package_data[pkg]['files'].add(mod.new_path or mod.old_path or mod.filename)
                    package_data[pkg]['commits'] += 1
            
            # Calculate ratios
            ratio_data = []
            for pkg, data in package_data.items():
                time_span_days = (data['last_commit'] - data['first_commit']).days
                if time_span_days == 0:
                    time_span_days = 1  # Avoid division by zero
                
                complexity_per_day = data['total_complexity'] / time_span_days
                
                ratio_data.append({
                    'package': pkg,
                    'total_complexity': data['total_complexity'],
                    'time_span_days': time_span_days,
                    'first_commit': data['first_commit'].isoformat(),
                    'last_commit': data['last_commit'].isoformat(),
                    'complexity_per_day': round(complexity_per_day, 2),
                    'num_files': len(data['files']),
                    'num_commits': data['commits']
                })
            
            if ratio_data:
                df = pd.DataFrame(ratio_data)
                df = df.sort_values('complexity_per_day', ascending=False)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"complexity_time_ratio_analysis_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    filename = f"complexity_time_ratio_analysis_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Complexity/time ratio analysis complete! Report saved: {filename}"
            else:
                return "❌ No package data found for ratio analysis"
                
        except Exception as e:
            return f"❌ Complexity/time ratio analysis failed: {str(e)}"
        """Analyze LOC to time ratio for each package"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing LOC/time ratio...")
        
        package_data = {}
        
        try:
            # Get all commits to track package evolution over time
            for commit in Repository(self.current_repo_path).traverse_commits():
                commit_date = commit.author_date
                
                for mod in commit.modified_files:
                    if not (mod.filename and mod.filename.endswith('.java')):
                        continue
                    
                    # Get package name
                    pkg = None
                    if mod.source_code:
                        pkg = self.detect_package_from_source(mod.source_code)
                    
                    if not pkg:
                        file_path = mod.new_path or mod.old_path or mod.filename
                        pkg = self.package_from_filepath(file_path)
                    
                    if not pkg:
                        pkg = '<<unknown>>'
                    
                    # Track package metrics
                    if pkg not in package_data:
                        package_data[pkg] = {
                            'first_commit': commit_date,
                            'last_commit': commit_date,
                            'total_loc': 0,
                            'files': set(),
                            'commits': 0
                        }
                    
                    # Update time range
                    if commit_date < package_data[pkg]['first_commit']:
                        package_data[pkg]['first_commit'] = commit_date
                    if commit_date > package_data[pkg]['last_commit']:
                        package_data[pkg]['last_commit'] = commit_date
                    
                    # Add current LOC if available (simple line counting)
                    if mod.source_code:
                        try:
                            lines = mod.source_code.split('\n')
                            loc_count = len([line for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*') and not line.strip().startswith('*')])
                            package_data[pkg]['total_loc'] = max(package_data[pkg]['total_loc'], loc_count)
                        except:
                            pass
                    
                    package_data[pkg]['files'].add(mod.new_path or mod.old_path or mod.filename)
                    package_data[pkg]['commits'] += 1
            
            # Calculate ratios
            ratio_data = []
            for pkg, data in package_data.items():
                time_span_days = (data['last_commit'] - data['first_commit']).days
                if time_span_days == 0:
                    time_span_days = 1  # Avoid division by zero
                
                loc_per_day = data['total_loc'] / time_span_days
                
                ratio_data.append({
                    'package': pkg,
                    'total_loc': data['total_loc'],
                    'time_span_days': time_span_days,
                    'first_commit': data['first_commit'].isoformat(),
                    'last_commit': data['last_commit'].isoformat(),
                    'loc_per_day': round(loc_per_day, 2),
                    'num_files': len(data['files']),
                    'num_commits': data['commits']
                })
            
            if ratio_data:
                df = pd.DataFrame(ratio_data)
                df = df.sort_values('loc_per_day', ascending=False)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"loc_time_ratio_analysis_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    filename = f"loc_time_ratio_analysis_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ LOC/time ratio analysis complete! Report saved: {filename}"
            else:
                return "❌ No package data found for ratio analysis"
                
        except Exception as e:
            return f"❌ Complexity/time ratio analysis failed: {str(e)}"
    
    def analyze_combined_analysis(self, combine_metrics: List[str] = None, output_format: str = 'excel') -> str:
        """Combined analysis of multiple metrics"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        if not combine_metrics:
            combine_metrics = ['loc', 'complexity']
        
        print(f"🔍 Analyzing combined metrics: {', '.join(combine_metrics)}...")
        
        combined_data = []
        
        try:
            # Walk through all Java files
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Get package name
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            row = {
                                'file_path': rel_path,
                                'package': pkg
                            }
                            
                            # Add requested metrics
                            if 'loc' in combine_metrics:
                                lines = content.split('\n')
                                loc_count = len([line for line in lines if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*') and not line.strip().startswith('*')])
                                row['loc'] = loc_count
                                row['comments'] = len([line for line in lines if line.strip().startswith('//') or line.strip().startswith('/*') or line.strip().startswith('*')])
                                row['blank'] = len([line for line in lines if not line.strip()])
                            
                            if 'complexity' in combine_metrics:
                                decisions = len(re.findall(r'\b(if|while|for|switch|catch|&&|\|\|)\b', content))
                                methods = len(re.findall(r'\b(public|private|protected)\s+.*?\(.*?\)\s*{', content))
                                classes = len(re.findall(r'\bclass\s+\w+', content))
                                row['decision_points'] = decisions
                                row['methods'] = methods
                                row['classes'] = classes
                                row['complexity_score'] = decisions + methods * 2 + classes
                            
                            combined_data.append(row)
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if combined_data:
                df = pd.DataFrame(combined_data)
                
                # Package-level summary
                agg_dict = {'file_path': 'count'}
                for metric in combine_metrics:
                    if metric == 'loc':
                        agg_dict.update({'loc': 'sum', 'comments': 'sum', 'blank': 'sum'})
                    elif metric == 'complexity':
                        agg_dict.update({'decision_points': 'sum', 'methods': 'sum', 'classes': 'sum', 'complexity_score': 'sum'})
                
                package_summary = df.groupby('package').agg(agg_dict).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"combined_analysis_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                else:
                    filename = f"combined_analysis_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Combined analysis complete! Metrics: {', '.join(combine_metrics)} | Report saved: {filename}"
            else:
                return "❌ No data found for combined analysis"
                
        except Exception as e:
            return f"❌ Combined analysis failed: {str(e)}"
    
    def analyze_file_class_count(self, output_format: str = 'excel') -> str:
        """Analyze files by package and count classes/interfaces in each file"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing files and class counts...")
        
        try:
            file_data = []
            
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Get package name
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            # Count classes and interfaces
                            classes = len(re.findall(r'\bclass\s+\w+', content))
                            interfaces = len(re.findall(r'\binterface\s+\w+', content))
                            enums = len(re.findall(r'\benum\s+\w+', content))
                            total_types = classes + interfaces + enums
                            
                            file_data.append({
                                'package': pkg,
                                'file_name': file,
                                'file_path': rel_path,
                                'classes': classes,
                                'interfaces': interfaces,
                                'enums': enums,
                                'total_types': total_types
                            })
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if file_data:
                df = pd.DataFrame(file_data)
                
                # Sort by package then by file name
                df = df.sort_values(['package', 'file_name'])
                
                if output_format == 'excel':
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"file_class_analysis_{timestamp}.xlsx"
                    df.to_excel(filename, index=False)
                    
                    # Also create a package summary
                    package_summary = df.groupby('package').agg({
                        'file_name': 'count',
                        'classes': 'sum',
                        'interfaces': 'sum',
                        'enums': 'sum',
                        'total_types': 'sum'
                    }).rename(columns={'file_name': 'file_count'}).reset_index()
                    
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='File Details', index=False)
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                    
                    print(f"✅ File/Class analysis complete! Report saved: {filename}")
                    
                    # Print summary
                    print(f"\n📋 Summary:")
                    print(package_summary.to_string(index=False))
                    
                    return f"✅ Analysis complete! Report saved: {filename}"
                else:
                    return df.to_string()
            else:
                return "❌ No Java files found in repository"
                
        except Exception as e:
            return f"❌ File/Class analysis failed: {str(e)}"
    
    def execute_custom_analysis(self, formula: str, output_format: str = 'excel') -> str:
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print(f"🔍 Executing custom analysis: {formula}")
        
        # This is a simplified implementation
        # In practice, you'd want more sophisticated formula parsing
        try:
            # Get basic metrics first
            churn_result = self.analyze_package_churn(threshold=1, output_format='csv')
            loc_result = self.analyze_loc(output_format='csv')
            
            return f"✅ Custom analysis executed. Formula: {formula}\nResults: {churn_result}"
            
        except Exception as e:
            return f"❌ Custom analysis failed: {str(e)}"
    
    def process_command(self, user_command: str) -> str:
        """Main method to process user commands"""
        print(f"🤖 Processing: {user_command}")
        
        # Use LLM to understand the command
        analysis_plan = self.process_natural_language_command(user_command)
        
        print(f"📋 Analysis plan: {analysis_plan['description']}")
        
        # Execute the appropriate analysis
        analysis_type = analysis_plan.get('analysis_type', 'package_churn')
        parameters = analysis_plan.get('parameters', {})
        
        if analysis_type == 'package_churn':
            threshold = parameters.get('threshold', 500)
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_package_churn(threshold, output_format)
            
        elif analysis_type == 'loc_analysis':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_loc(output_format)
            
        elif analysis_type == 'complexity_analysis':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_complexity(output_format)
            
        elif analysis_type == 'release_analysis':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_releases(output_format)
            
        elif analysis_type == 'loc_time_ratio':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_loc_time_ratio(output_format)
            
        elif analysis_type == 'complexity_time_ratio':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_complexity_time_ratio(output_format)
            
        elif analysis_type == 'combined_analysis':
            combine_metrics = parameters.get('combine_metrics', ['loc', 'complexity'])
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_combined_analysis(combine_metrics, output_format)
            
        elif analysis_type == 'file_class_analysis':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_file_class_count(output_format)
            
        elif analysis_type == 'custom_analysis':
            formula = parameters.get('custom_formula', 'lines_added + lines_removed')
            output_format = parameters.get('output_format', 'excel')
            return self.execute_custom_analysis(formula, output_format)
            
        else:
            return f"❌ Unknown analysis type: {analysis_type}"

def main():
    """Interactive CLI for LLM-powered Git analysis"""
    analyzer = LLMGitAnalyzer()
    
    print("🚀 LLM-Powered Git Repository Analyzer")
    print("=" * 50)
    print("Available commands:")
    print("  set_repo <path>       - Set repository path")
    print("  <natural_command>     - Natural language analysis request")
    print("  help                  - Show this help")
    print("  quit                  - Exit")
    print()
    
    while True:
        try:
            user_input = input(">>> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            elif user_input.lower() == 'help':
                print(f"Available tools: {list(analyzer.available_tools.keys())}")
                print(f"Current repo: {analyzer.current_repo_path}")
                continue
                
            elif user_input.startswith('set_repo '):
                repo_path = user_input[9:].strip()
                analyzer.set_repository(repo_path)
                continue
                
            elif user_input:
                result = analyzer.process_command(user_input)
                print(result)
                print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

if __name__ == "__main__":
    main()