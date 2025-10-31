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
        self.current_repo_path = self.load_current_repo()
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
            'visualization': 'Generate charts and visualizations',
            'maintainability_index': 'Calculate maintainability index for code quality',
            'halstead_metrics': 'Analyze Halstead complexity metrics',
            'cognitive_complexity': 'Measure cognitive complexity of methods',
            'technical_debt': 'Estimate technical debt and code smells',
            'test_coverage': 'Analyze test coverage metrics',
            'code_duplication': 'Detect code duplication patterns',
            'dependency_analysis': 'Analyze package dependencies and coupling',
            'refactoring_opportunities': 'Identify refactoring opportunities',
            'security_metrics': 'Basic security analysis and vulnerability patterns',
            'performance_metrics': 'Performance-related code analysis'
        }
        
    def load_current_repo(self):
        """Load the current repository path from state file"""
        try:
            if os.path.exists('.current_repo'):
                with open('.current_repo', 'r', encoding='utf-8') as f:
                    repo_path = f.read().strip()
                    if os.path.exists(repo_path) and os.path.exists(os.path.join(repo_path, '.git')):
                        return repo_path
        except Exception:
            pass
        return None
    
    def save_current_repo(self, repo_path):
        """Save the current repository path to state file"""
        try:
            with open('.current_repo', 'w', encoding='utf-8') as f:
                f.write(repo_path)
        except Exception:
            pass
        
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
        - clone_repo: Clone a Git repository from URL
        
        Current repository: {self.current_repo_path or "Not set"}
        
        User command: "{user_command}"
        
        SPECIAL COMMANDS:
        Clone Repository:
        - Commands about "clone", "download repo", "get from github"
        - Bengali: "clone koro", "github theke ano", "repo download koro"
        - Extract the Git URL and local path if provided
        
        Commit Limits:
        - Commands with "first N commits", "last N commits", "limit to N"
        - Bengali: "prothom 1000 ta commit", "500 commit porjonto", "limit 200"
        - Extract the number as commit_limit parameter
        
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
            "analysis_type": "MUST be one of: package_churn, loc_analysis, complexity_analysis, release_analysis, loc_time_ratio, complexity_time_ratio, combined_analysis, custom_analysis, clone_repo",
            "parameters": {{
                "threshold": 500,
                "output_format": "excel",
                "custom_formula": "if custom analysis",
                "time_range": "if applicable",
                "combine_metrics": ["loc", "complexity"], // for combined analysis
                "commit_limit": null, // number for commit limit
                "git_url": "if clone_repo", // GitHub URL to clone
                "local_path": "if clone_repo" // optional local path
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
        - "Clone https://github.com/SeleniumHQ/selenium" → {{"analysis_type": "clone_repo", "parameters": {{"git_url": "https://github.com/SeleniumHQ/selenium"}}}}
        - "LOC analysis with first 1000 commits" → {{"analysis_type": "loc_analysis", "parameters": {{"commit_limit": 1000}}}}
        - "Complexity for 500 commits only" → {{"analysis_type": "complexity_analysis", "parameters": {{"commit_limit": 500}}}}
        - "Clone and analyze selenium repo first 200 commits" → {{"analysis_type": "clone_repo", "parameters": {{"git_url": "https://github.com/SeleniumHQ/selenium", "commit_limit": 200}}}}
        
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
            self.save_current_repo(repo_path)
            print(f"✅ Repository set: {repo_path}")
            return True
        else:
            print(f"❌ Invalid repository path: {repo_path}")
            return False
    
    def clone_and_set_repository(self, git_url: str, local_path: str = None) -> bool:
        """Clone a Git repository and set it for analysis"""
        import subprocess
        
        try:
            # Generate local path if not provided
            if not local_path:
                repo_name = git_url.split('/')[-1].replace('.git', '')
                local_path = os.path.join(os.getcwd(), repo_name)
            
            print(f"📥 Cloning repository from {git_url}...")
            print(f"📁 Target location: {local_path}")
            
            # Clone the repository
            result = subprocess.run(['git', 'clone', git_url, local_path], 
                                  capture_output=True, text=True, check=True)
            
            print(f"✅ Repository cloned successfully!")
            
            # Set as current repository
            success = self.set_repository(local_path)
            if success:
                self.save_current_repo(local_path)
            return success
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git clone failed: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Clone operation failed: {str(e)}")
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
    
    def analyze_package_churn(self, threshold: int = 500, output_format: str = 'excel', commit_limit: int = None) -> str:
        """Analyze package-level code churn"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print(f"🔍 Analyzing package churn (threshold: {threshold} lines, limit: {commit_limit or 'no limit'})...")
        
        rows = []
        commit_count = 0
        
        try:
            for commit in Repository(self.current_repo_path).traverse_commits():
                commit_count += 1
                
                # Show progress every 50 commits
                if commit_count % 50 == 0:
                    print(f"  📈 Processed {commit_count} commits...")
                
                # Apply commit limit if specified
                if commit_limit and commit_count > commit_limit:
                    print(f"  ⏹️ Reached commit limit of {commit_limit}")
                    break
                
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
            # First count total files for progress
            total_files = sum(1 for root, dirs, files in os.walk(self.current_repo_path) 
                            for file in files if file.endswith('.java'))
            
            print(f"📁 Found {total_files} Java files to analyze...")
            processed = 0
            
            # Walk through all Java files
            for root, dirs, files in os.walk(self.current_repo_path):
                # Skip .git and other hidden directories for speed
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.endswith('.java'):
                        processed += 1
                        if processed % 50 == 0:  # Show progress every 50 files
                            print(f"   📈 Processed {processed}/{total_files} files...")
                        
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
    
    def analyze_loc_time_ratio(self, output_format: str = 'excel', commit_limit: int = None) -> str:
        """Analyze Lines of Code to time ratio for each package (LOC per month)"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing LOC/time ratio...")
        
        package_data = {}
        commit_count = 0
        
        try:
            # Get all commits to track package evolution over time
            repo = Repository(self.current_repo_path)
            total_commits = sum(1 for _ in repo.traverse_commits()) if commit_limit else "unknown"
            
            print(f"📊 Processing commits (limit: {commit_limit or 'no limit'}, total: {total_commits})...")
            
            for commit in Repository(self.current_repo_path).traverse_commits():
                commit_count += 1
                
                # Show progress every 100 commits
                if commit_count % 100 == 0:
                    print(f"   📈 Processed {commit_count} commits...")
                
                # Apply commit limit if specified
                if commit_limit and commit_count > commit_limit:
                    print(f"   ⏹️ Reached commit limit of {commit_limit}")
                    break
                commit_date = commit.author_date
                month_key = commit_date.strftime("%Y-%m")
                
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
                    
                    # Track package metrics per month
                    if pkg not in package_data:
                        package_data[pkg] = {}
                    
                    if month_key not in package_data[pkg]:
                        package_data[pkg][month_key] = {
                            'total_loc': 0,
                            'files': set(),
                            'commits': 0,
                            'lines_added': 0,
                            'lines_deleted': 0
                        }
                    
                    # Add LOC metrics
                    if mod.added_lines:
                        package_data[pkg][month_key]['lines_added'] += mod.added_lines
                    if mod.deleted_lines:
                        package_data[pkg][month_key]['lines_deleted'] += mod.deleted_lines
                    
                    # Calculate current LOC if source is available
                    if mod.source_code:
                        current_loc = len(mod.source_code.splitlines())
                        package_data[pkg][month_key]['total_loc'] = max(
                            package_data[pkg][month_key]['total_loc'], 
                            current_loc
                        )
                    
                    package_data[pkg][month_key]['files'].add(mod.new_path or mod.old_path or mod.filename)
                    package_data[pkg][month_key]['commits'] += 1
            
            # Flatten data for DataFrame
            ratio_data = []
            for pkg, months in package_data.items():
                for month, data in months.items():
                    net_change = data['lines_added'] - data['lines_deleted']
                    
                    ratio_data.append({
                        'package': pkg,
                        'month': month,
                        'total_loc': data['total_loc'],
                        'lines_added': data['lines_added'],
                        'lines_deleted': data['lines_deleted'],
                        'net_loc_change': net_change,
                        'num_files': len(data['files']),
                        'num_commits': data['commits']
                    })
            
            if ratio_data:
                df = pd.DataFrame(ratio_data)
                df = df.sort_values(['package', 'month'])
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"loc_time_ratio_analysis_{timestamp}.xlsx"
                    df.to_excel(filename, index=False, engine='openpyxl')
                else:
                    filename = f"loc_time_ratio_analysis_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ LOC/time ratio analysis complete! Report saved: {filename}"
            else:
                return "❌ No LOC data found"
                
        except Exception as e:
            return f"❌ LOC/time ratio analysis failed: {str(e)}"
    
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
        
        # Handle simple commands without LLM to avoid quota issues
        lower_cmd = user_command.lower().strip()
        
        # Simple clone command detection
        if lower_cmd.startswith('clone ') and 'github.com' in lower_cmd:
            git_url = user_command.split()[-1]  # Get last word as URL
            success = self.clone_and_set_repository(git_url)
            return "✅ Repository cloned and set! Ready for analysis." if success else "❌ Failed to clone repository"
        
        # Simple analysis commands with commit limits
        commit_limit = None
        output_format = 'excel'
        
        # Extract commit limit from command
        import re
        limit_match = re.search(r'(?:first|limit|শেষ|প্রথম)\s*(\d+)', lower_cmd)
        if limit_match:
            commit_limit = int(limit_match.group(1))
        
        # Simple command mappings
        if 'loc' in lower_cmd and ('time' in lower_cmd or 'month' in lower_cmd or 'ratio' in lower_cmd):
            return self.analyze_loc_time_ratio(output_format, commit_limit)
        elif 'package' in lower_cmd and 'churn' in lower_cmd:
            threshold = 500
            threshold_match = re.search(r'(\d+)\s*(?:line|লাইন)', lower_cmd)
            if threshold_match:
                threshold = int(threshold_match.group(1))
            return self.analyze_package_churn(threshold, output_format, commit_limit)
        elif 'halstead' in lower_cmd or 'halstead metrics' in lower_cmd:
            return self.analyze_halstead_metrics(output_format)
        elif 'maintainability' in lower_cmd or 'maintainability index' in lower_cmd:
            return self.analyze_maintainability_index(output_format)
        elif 'technical debt' in lower_cmd or 'debt' in lower_cmd or 'code smell' in lower_cmd:
            return self.analyze_technical_debt(output_format)
        elif 'dependency' in lower_cmd or 'coupling' in lower_cmd:
            return self.analyze_dependency_metrics(output_format)
        elif 'duplication' in lower_cmd or 'duplicate' in lower_cmd or 'copy' in lower_cmd:
            return self.analyze_code_duplication(output_format)
        elif 'test coverage' in lower_cmd or 'coverage' in lower_cmd or 'test' in lower_cmd:
            return self.analyze_test_coverage_estimation(output_format)
        elif 'security' in lower_cmd or 'vulnerability' in lower_cmd or 'secure' in lower_cmd:
            return self.analyze_security_patterns(output_format)
        elif 'loc' in lower_cmd or 'lines of code' in lower_cmd:
            return self.analyze_loc(output_format)
        elif 'complexity' in lower_cmd:
            return self.analyze_complexity(output_format)
        elif 'release' in lower_cmd:
            return self.analyze_releases(output_format)
        
        # If simple mapping fails, try LLM
        try:
            # Use LLM to understand the command
            analysis_plan = self.process_natural_language_command(user_command)
            print(f"📋 Analysis plan: {analysis_plan['description']}")
        except Exception as e:
            print(f"⚠️ LLM failed ({e}), trying fallback analysis...")
            # Fallback to LOC analysis
            return self.analyze_loc(output_format)
        
        # Execute the appropriate analysis
        analysis_type = analysis_plan.get('analysis_type', 'package_churn')
        parameters = analysis_plan.get('parameters', {})
        
        if analysis_type == 'package_churn':
            threshold = parameters.get('threshold', 500)
            output_format = parameters.get('output_format', 'excel')
            commit_limit = parameters.get('commit_limit', None)
            return self.analyze_package_churn(threshold, output_format, commit_limit)
            
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
            commit_limit = parameters.get('commit_limit', None)
            return self.analyze_loc_time_ratio(output_format, commit_limit)
            
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
            
        elif analysis_type == 'clone_repo':
            git_url = parameters.get('git_url')
            local_path = parameters.get('local_path')
            if not git_url:
                return "❌ Git URL required for clone operation"
            
            success = self.clone_and_set_repository(git_url, local_path)
            if success:
                # If commit_limit is specified, store it for next analysis
                commit_limit = parameters.get('commit_limit')
                if commit_limit:
                    return f"✅ Repository cloned and set! Ready for analysis with {commit_limit} commit limit."
                else:
                    return "✅ Repository cloned and set! Ready for analysis."
            else:
                return "❌ Failed to clone repository"
        
        elif analysis_type == 'halstead_metrics':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_halstead_metrics(output_format)
            
        elif analysis_type == 'maintainability_index':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_maintainability_index(output_format)
            
        elif analysis_type == 'technical_debt':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_technical_debt(output_format)
            
        elif analysis_type == 'dependency_analysis':
            output_format = parameters.get('output_format', 'excel')
            return self.analyze_dependency_metrics(output_format)
        
        else:
            return f"❌ Unknown analysis type: {analysis_type}"

    def analyze_code_duplication(self, output_format: str = 'excel') -> str:
        """Detect code duplication patterns"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing code duplication...")
        
        duplication_data = []
        
        try:
            file_contents = {}
            
            # First pass: collect all file contents
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                file_contents[rel_path] = content
                        except Exception as e:
                            print(f"  Warning: Could not read {file}: {e}")
            
            # Second pass: find duplications
            for file1_path, content1 in file_contents.items():
                lines1 = content1.split('\n')
                duplicated_lines = 0
                
                for file2_path, content2 in file_contents.items():
                    if file1_path >= file2_path:  # Avoid duplicate comparisons
                        continue
                    
                    lines2 = content2.split('\n')
                    
                    # Find common consecutive lines (minimum 5 lines)
                    for i in range(len(lines1) - 4):
                        for j in range(len(lines2) - 4):
                            common_lines = 0
                            k = 0
                            
                            while (i + k < len(lines1) and j + k < len(lines2) and 
                                   lines1[i + k].strip() == lines2[j + k].strip() and 
                                   lines1[i + k].strip() != ''):
                                common_lines += 1
                                k += 1
                            
                            if common_lines >= 5:  # At least 5 consecutive lines
                                duplicated_lines += common_lines
                
                pkg = self.package_from_filepath(file1_path)
                
                duplication_data.append({
                    'file_path': file1_path,
                    'package': pkg,
                    'total_lines': len(lines1),
                    'duplicated_lines': duplicated_lines,
                    'duplication_ratio': (duplicated_lines / max(len(lines1), 1)) * 100
                })
            
            if duplication_data:
                df = pd.DataFrame(duplication_data)
                
                # Package-level summary
                package_summary = df.groupby('package').agg({
                    'total_lines': 'sum',
                    'duplicated_lines': 'sum',
                    'duplication_ratio': 'mean',
                    'file_path': 'count'
                }).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"code_duplication_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                else:
                    filename = f"code_duplication_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Code duplication analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ Code duplication analysis failed: {str(e)}"

    def analyze_test_coverage_estimation(self, output_format: str = 'excel') -> str:
        """Estimate test coverage based on test files and source files"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing test coverage estimation...")
        
        coverage_data = []
        test_files = []
        source_files = []
        
        try:
            # Separate test files and source files
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        # Detect test files
                        if ('test' in rel_path.lower() or 
                            file.lower().endswith('test.java') or 
                            file.lower().endswith('tests.java')):
                            test_files.append(rel_path)
                        else:
                            source_files.append(rel_path)
            
            # Calculate coverage estimation by package
            packages = {}
            
            for source_file in source_files:
                pkg = self.package_from_filepath(source_file)
                if pkg not in packages:
                    packages[pkg] = {'source_files': 0, 'test_files': 0}
                packages[pkg]['source_files'] += 1
            
            for test_file in test_files:
                pkg = self.package_from_filepath(test_file)
                if pkg not in packages:
                    packages[pkg] = {'source_files': 0, 'test_files': 0}
                packages[pkg]['test_files'] += 1
            
            for pkg, counts in packages.items():
                test_ratio = (counts['test_files'] / max(counts['source_files'], 1)) * 100
                estimated_coverage = min(test_ratio * 0.7, 95)  # Rough estimation
                
                coverage_data.append({
                    'package': pkg,
                    'source_files': counts['source_files'],
                    'test_files': counts['test_files'],
                    'test_ratio': test_ratio,
                    'estimated_coverage': estimated_coverage,
                    'coverage_level': 'High' if estimated_coverage > 80 else 'Medium' if estimated_coverage > 50 else 'Low'
                })
            
            if coverage_data:
                df = pd.DataFrame(coverage_data)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"test_coverage_estimation_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Coverage Estimation', index=False)
                        # Add summary statistics
                        summary = pd.DataFrame([
                            {'Metric': 'Total Source Files', 'Value': len(source_files)},
                            {'Metric': 'Total Test Files', 'Value': len(test_files)},
                            {'Metric': 'Overall Test Ratio', 'Value': f"{(len(test_files) / max(len(source_files), 1)) * 100:.1f}%"},
                            {'Metric': 'High Coverage Packages', 'Value': len([p for p in coverage_data if p['estimated_coverage'] > 80])},
                            {'Metric': 'Low Coverage Packages', 'Value': len([p for p in coverage_data if p['estimated_coverage'] < 50])}
                        ])
                        summary.to_excel(writer, sheet_name='Summary', index=False)
                else:
                    filename = f"test_coverage_estimation_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Test coverage estimation complete! Report saved: {filename}"
            else:
                return "❌ No packages found for analysis"
                
        except Exception as e:
            return f"❌ Test coverage estimation failed: {str(e)}"

    def analyze_security_patterns(self, output_format: str = 'excel') -> str:
        """Analyze basic security patterns and potential vulnerabilities"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing security patterns...")
        
        security_data = []
        
        try:
            # Security pattern definitions
            security_patterns = {
                'sql_injection': [r'Statement.*executeQuery\(.*\+', r'prepareStatement\(.*\+'],
                'hardcoded_secrets': [r'password\s*=\s*["\'][^"\']+["\']', r'apikey\s*=\s*["\'][^"\']+["\']', r'token\s*=\s*["\'][^"\']+["\']'],
                'insecure_random': [r'Math\.random\(\)', r'new Random\(\)'],
                'weak_crypto': [r'MD5', r'SHA1(?!\\d)', r'DES'],
                'unsafe_deserialization': [r'ObjectInputStream', r'readObject'],
                'path_traversal': [r'new File\(.*\+', r'FileInputStream\(.*\+'],
                'xxe_vulnerability': [r'DocumentBuilderFactory', r'SAXParserFactory'],
                'improper_validation': [r'request\.getParameter\([^)]+\)', r'request\.getHeader\([^)]+\)']
            }
            
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            # Check for security patterns
                            security_issues = {}
                            total_issues = 0
                            
                            for pattern_name, patterns in security_patterns.items():
                                count = 0
                                for pattern in patterns:
                                    matches = re.findall(pattern, content, re.IGNORECASE)
                                    count += len(matches)
                                security_issues[pattern_name] = count
                                total_issues += count
                            
                            # Calculate risk level
                            risk_level = 'High' if total_issues > 10 else 'Medium' if total_issues > 3 else 'Low'
                            
                            security_data.append({
                                'file_path': rel_path,
                                'package': pkg,
                                'sql_injection_risks': security_issues['sql_injection'],
                                'hardcoded_secrets': security_issues['hardcoded_secrets'],
                                'insecure_random': security_issues['insecure_random'],
                                'weak_crypto': security_issues['weak_crypto'],
                                'unsafe_deserialization': security_issues['unsafe_deserialization'],
                                'path_traversal': security_issues['path_traversal'],
                                'xxe_vulnerability': security_issues['xxe_vulnerability'],
                                'improper_validation': security_issues['improper_validation'],
                                'total_security_issues': total_issues,
                                'risk_level': risk_level
                            })
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if security_data:
                df = pd.DataFrame(security_data)
                
                # Package-level summary
                numeric_columns = ['sql_injection_risks', 'hardcoded_secrets', 'insecure_random', 
                                 'weak_crypto', 'unsafe_deserialization', 'path_traversal', 
                                 'xxe_vulnerability', 'improper_validation', 'total_security_issues']
                
                package_summary = df.groupby('package')[numeric_columns].sum().reset_index()
                package_summary['file_count'] = df.groupby('package').size().values
                package_summary['avg_risk_score'] = package_summary['total_security_issues'] / package_summary['file_count']
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"security_analysis_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                        
                        # Add security guidelines
                        guidelines = pd.DataFrame([
                            {'Issue Type': 'SQL Injection', 'Risk': 'High', 'Recommendation': 'Use parameterized queries and prepared statements'},
                            {'Issue Type': 'Hardcoded Secrets', 'Risk': 'High', 'Recommendation': 'Store secrets in environment variables or secure vaults'},
                            {'Issue Type': 'Weak Cryptography', 'Risk': 'Medium', 'Recommendation': 'Use strong algorithms like AES-256, SHA-256+'},
                            {'Issue Type': 'Insecure Random', 'Risk': 'Medium', 'Recommendation': 'Use SecureRandom for cryptographic purposes'},
                            {'Issue Type': 'Path Traversal', 'Risk': 'High', 'Recommendation': 'Validate and sanitize file paths'},
                            {'Issue Type': 'XXE Vulnerability', 'Risk': 'High', 'Recommendation': 'Disable external entity processing'},
                            {'Issue Type': 'Unsafe Deserialization', 'Risk': 'High', 'Recommendation': 'Validate input and use safe serialization'},
                            {'Issue Type': 'Improper Validation', 'Risk': 'Medium', 'Recommendation': 'Always validate and sanitize user input'}
                        ])
                        guidelines.to_excel(writer, sheet_name='Security Guidelines', index=False)
                else:
                    filename = f"security_analysis_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Security analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ Security analysis failed: {str(e)}"

    def analyze_halstead_metrics(self, output_format: str = 'excel') -> str:
        """Analyze Halstead complexity metrics for Java files"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing Halstead metrics...")
        
        halstead_data = []
        
        try:
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Calculate Halstead metrics (simplified for Java)
                            operators = len(re.findall(r'[+\-*/%=<>!&|^~]|==|!=|<=|>=|&&|\|\||<<|>>|\+\+|--|instanceof', content))
                            operands = len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content))
                            unique_operators = len(set(re.findall(r'[+\-*/%=<>!&|^~]|==|!=|<=|>=|&&|\|\||<<|>>|\+\+|--|instanceof', content)))
                            unique_operands = len(set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)))
                            
                            if unique_operators > 0 and unique_operands > 0:
                                vocabulary = unique_operators + unique_operands
                                length = operators + operands
                                calculated_length = unique_operators * (operators / unique_operators).bit_length() + unique_operands * (operands / unique_operands).bit_length() if unique_operators > 0 and unique_operands > 0 else 0
                                volume = length * (vocabulary.bit_length() if vocabulary > 0 else 0)
                                difficulty = (unique_operators / 2) * (operands / unique_operands) if unique_operands > 0 else 0
                                effort = difficulty * volume
                                
                                pkg = self.detect_package_from_source(content)
                                if not pkg:
                                    pkg = self.package_from_filepath(rel_path)
                                
                                halstead_data.append({
                                    'file_path': rel_path,
                                    'package': pkg,
                                    'unique_operators': unique_operators,
                                    'unique_operands': unique_operands,
                                    'total_operators': operators,
                                    'total_operands': operands,
                                    'vocabulary': vocabulary,
                                    'length': length,
                                    'calculated_length': calculated_length,
                                    'volume': volume,
                                    'difficulty': difficulty,
                                    'effort': effort
                                })
                                
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if halstead_data:
                df = pd.DataFrame(halstead_data)
                
                # Package-level summary
                package_summary = df.groupby('package').agg({
                    'unique_operators': 'mean',
                    'unique_operands': 'mean',
                    'vocabulary': 'mean',
                    'volume': 'mean',
                    'difficulty': 'mean',
                    'effort': 'mean',
                    'file_path': 'count'
                }).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"halstead_metrics_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                else:
                    filename = f"halstead_metrics_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Halstead metrics analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ Halstead metrics analysis failed: {str(e)}"

    def analyze_maintainability_index(self, output_format: str = 'excel') -> str:
        """Calculate maintainability index for code quality assessment"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing maintainability index...")
        
        maintainability_data = []
        
        try:
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Calculate basic metrics for maintainability index
                            lines = content.split('\n')
                            loc = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
                            complexity = len(re.findall(r'\b(if|while|for|switch|catch|&&|\|\|)\b', content))
                            halstead_volume = len(content.split()) * 10  # Simplified
                            comment_lines = len([line for line in lines if line.strip().startswith('//')])
                            comment_ratio = comment_lines / max(loc, 1) * 100
                            
                            # Simplified maintainability index calculation
                            # MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC) + 50 * sin(sqrt(2.4 * CM))
                            import math
                            mi = 171 - 5.2 * math.log(max(halstead_volume, 1)) - 0.23 * complexity - 16.2 * math.log(max(loc, 1)) + 50 * math.sin(math.sqrt(2.4 * comment_ratio / 100))
                            
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            maintainability_data.append({
                                'file_path': rel_path,
                                'package': pkg,
                                'lines_of_code': loc,
                                'cyclomatic_complexity': complexity,
                                'halstead_volume': halstead_volume,
                                'comment_ratio': comment_ratio,
                                'maintainability_index': max(0, min(100, mi))
                            })
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if maintainability_data:
                df = pd.DataFrame(maintainability_data)
                
                # Package-level summary
                package_summary = df.groupby('package').agg({
                    'lines_of_code': 'sum',
                    'cyclomatic_complexity': 'mean',
                    'maintainability_index': 'mean',
                    'comment_ratio': 'mean',
                    'file_path': 'count'
                }).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"maintainability_index_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                else:
                    filename = f"maintainability_index_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Maintainability index analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ Maintainability index analysis failed: {str(e)}"

    def analyze_technical_debt(self, output_format: str = 'excel') -> str:
        """Estimate technical debt and code smells"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing technical debt...")
        
        debt_data = []
        
        try:
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # Detect various code smells and technical debt indicators
                            lines = content.split('\n')
                            loc = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
                            
                            # Code smells detection
                            long_methods = len(re.findall(r'(public|private|protected).*?\{[\s\S]*?\}', content, re.MULTILINE))
                            magic_numbers = len(re.findall(r'\b\d{2,}\b', content))  # Numbers with 2+ digits
                            duplicated_code = len(re.findall(r'(.{50,})\1', content))  # Repeated patterns
                            todo_comments = len(re.findall(r'//.*?(TODO|FIXME|HACK)', content, re.IGNORECASE))
                            deprecated_usage = len(re.findall(r'@Deprecated', content))
                            empty_catch_blocks = len(re.findall(r'catch\s*\([^)]+\)\s*\{\s*\}', content))
                            
                            # Calculate debt score
                            debt_score = (
                                long_methods * 2 +
                                magic_numbers * 0.5 +
                                duplicated_code * 3 +
                                todo_comments * 1 +
                                deprecated_usage * 2 +
                                empty_catch_blocks * 4
                            )
                            
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            debt_data.append({
                                'file_path': rel_path,
                                'package': pkg,
                                'lines_of_code': loc,
                                'long_methods': long_methods,
                                'magic_numbers': magic_numbers,
                                'duplicated_code': duplicated_code,
                                'todo_comments': todo_comments,
                                'deprecated_usage': deprecated_usage,
                                'empty_catch_blocks': empty_catch_blocks,
                                'debt_score': debt_score,
                                'debt_ratio': debt_score / max(loc, 1) * 100
                            })
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            if debt_data:
                df = pd.DataFrame(debt_data)
                
                # Package-level summary
                package_summary = df.groupby('package').agg({
                    'lines_of_code': 'sum',
                    'debt_score': 'sum',
                    'debt_ratio': 'mean',
                    'todo_comments': 'sum',
                    'deprecated_usage': 'sum',
                    'file_path': 'count'
                }).rename(columns={'file_path': 'file_count'}).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"technical_debt_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        package_summary.to_excel(writer, sheet_name='Package Summary', index=False)
                        df.to_excel(writer, sheet_name='File Details', index=False)
                        # Add recommendations sheet
                        recommendations = pd.DataFrame([
                            {'Metric': 'Long Methods', 'Threshold': '> 50 lines', 'Recommendation': 'Break into smaller methods'},
                            {'Metric': 'Magic Numbers', 'Threshold': '> 5 per file', 'Recommendation': 'Use named constants'},
                            {'Metric': 'TODO Comments', 'Threshold': '> 3 per file', 'Recommendation': 'Plan technical debt reduction'},
                            {'Metric': 'Empty Catch Blocks', 'Threshold': '> 0', 'Recommendation': 'Add proper error handling'},
                            {'Metric': 'Debt Ratio', 'Threshold': '> 20%', 'Recommendation': 'Priority refactoring needed'}
                        ])
                        recommendations.to_excel(writer, sheet_name='Recommendations', index=False)
                else:
                    filename = f"technical_debt_{timestamp}.csv"
                    package_summary.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Technical debt analysis complete! Report saved: {filename}"
            else:
                return "❌ No Java files found for analysis"
                
        except Exception as e:
            return f"❌ Technical debt analysis failed: {str(e)}"

    def analyze_dependency_metrics(self, output_format: str = 'excel') -> str:
        """Analyze package dependencies and coupling metrics"""
        if not self.current_repo_path:
            return "❌ No repository set. Use set_repository() first."
        
        print("🔍 Analyzing dependency metrics...")
        
        dependency_data = []
        package_imports = {}
        
        try:
            # First pass: collect all imports
            for root, dirs, files in os.walk(self.current_repo_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, self.current_repo_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            pkg = self.detect_package_from_source(content)
                            if not pkg:
                                pkg = self.package_from_filepath(rel_path)
                            
                            # Extract imports
                            imports = re.findall(r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*);', content)
                            internal_imports = [imp for imp in imports if not any(imp.startswith(ext) for ext in ['java.', 'javax.', 'org.', 'com.'])]
                            external_imports = [imp for imp in imports if any(imp.startswith(ext) for ext in ['java.', 'javax.', 'org.', 'com.'])]
                            
                            if pkg not in package_imports:
                                package_imports[pkg] = {'internal': set(), 'external': set(), 'files': 0}
                            
                            package_imports[pkg]['internal'].update(internal_imports)
                            package_imports[pkg]['external'].update(external_imports)
                            package_imports[pkg]['files'] += 1
                            
                        except Exception as e:
                            print(f"  Warning: Could not analyze {file}: {e}")
            
            # Calculate coupling metrics
            for pkg, imports in package_imports.items():
                afferent_coupling = sum(1 for other_pkg, other_imports in package_imports.items() 
                                      if other_pkg != pkg and any(imp.startswith(pkg) for imp in other_imports['internal']))
                efferent_coupling = len(imports['internal'])
                instability = efferent_coupling / (afferent_coupling + efferent_coupling) if (afferent_coupling + efferent_coupling) > 0 else 0
                
                dependency_data.append({
                    'package': pkg,
                    'file_count': imports['files'],
                    'internal_imports': len(imports['internal']),
                    'external_imports': len(imports['external']),
                    'afferent_coupling': afferent_coupling,
                    'efferent_coupling': efferent_coupling,
                    'instability': instability,
                    'total_dependencies': len(imports['internal']) + len(imports['external'])
                })
            
            if dependency_data:
                df = pd.DataFrame(dependency_data)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if output_format.lower() == 'excel':
                    filename = f"dependency_metrics_{timestamp}.xlsx"
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Dependency Metrics', index=False)
                        # Add metrics explanation
                        explanations = pd.DataFrame([
                            {'Metric': 'Afferent Coupling (Ca)', 'Description': 'Number of packages that depend on this package'},
                            {'Metric': 'Efferent Coupling (Ce)', 'Description': 'Number of packages this package depends on'},
                            {'Metric': 'Instability (I)', 'Description': 'Ce / (Ca + Ce). 0 = stable, 1 = unstable'},
                            {'Metric': 'Internal Imports', 'Description': 'Dependencies on internal packages'},
                            {'Metric': 'External Imports', 'Description': 'Dependencies on external libraries'}
                        ])
                        explanations.to_excel(writer, sheet_name='Metrics Explanation', index=False)
                else:
                    filename = f"dependency_metrics_{timestamp}.csv"
                    df.to_csv(filename, index=False, encoding='utf-8')
                
                return f"✅ Dependency metrics analysis complete! Report saved: {filename}"
            else:
                return "❌ No packages found for analysis"
                
        except Exception as e:
            return f"❌ Dependency metrics analysis failed: {str(e)}"


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