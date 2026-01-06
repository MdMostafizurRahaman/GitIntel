"""
Helper functions for dataset generation
Separated for cleaner architecture
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

# Safe print function for Windows console (handles emoji encoding)
def safe_print(*args, **kwargs):
    """Print safely to console, handling emoji characters on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # If emoji fails, try to encode with 'replace' strategy
        try:
            message = ' '.join(str(arg) for arg in args)
            # Replace common emojis with text equivalents for console output
            emoji_map = {
                '[OK]': '[OK]',
                '[ERROR]': '[ERROR]',
                '[TIMEOUT]': '[TIMEOUT]',
                '[SEARCH]': '[SEARCH]',
                '[THINKING]': '[THINKING]',
                '[WARNING]': '[WARNING]',
                '[DATA]': '[DATA]',
                '[CHART]': '[CHART]',
                '[JURY]': '[JURY]',
                '[VERDICT]': '[VERDICT]',
                '[SUCCESS]': '[SUCCESS]',
                '[NOTE]': '[NOTE]',
                '[SAVE]': '[SAVE]',
                '[FILES]': '[FILES]',
                '[PROCESSING]': '[PROCESSING]',
            }
            for emoji, text in emoji_map.items():
                message = message.replace(emoji, text)
            print(message, **kwargs)
        except:
            # Last resort: just print without the message
            pass


def apply_custom_metrics(extracted_data: List[Dict], custom_metrics: List[Dict], repo_path: str = None, progress_callback=None) -> tuple:
    """
    Apply JURY-APPROVED custom metrics to extracted data
    This ACTUALLY EXECUTES the code that jury validated!
    
    Args:
        extracted_data: Base metrics from code analysis
        custom_metrics: Jury-approved metric definitions with generated code
        repo_path: Repository path for git queries (REQUIRED for git-based metrics)
        progress_callback: Optional callback(current, total, message) for progress updates
    
    Returns: (updated_data, applied_count, errors)
    """
    if not extracted_data:
        return extracted_data, 0, ["No extracted data"]
    
    # Convert to DataFrame
    df = pd.DataFrame(extracted_data)
    original_columns = set(df.columns)
    
    # DO NOT add placeholder columns - let generated code extract REAL data
    # The jury-generated code MUST query git repository for commit/author data
    
    applied_count = 0
    errors = []
    extraction_metadata = {}  # Track how each metric was extracted
    
    for custom in custom_metrics:
        metric_name = custom.get('name')
        formula = custom.get('expression', custom.get('formula', ''))
        code = custom.get('code')
        
        if not code:
            errors.append(f"{metric_name}: No code provided")
            continue
        
        try:
            # Extract metrics needed from formula
            metrics_in_formula = custom.get('custom_metrics', [])
            extraction_metadata[metric_name] = {
                'formula': formula,
                'metrics_needed': metrics_in_formula,
                'code_length': len(code),
                'status': 'pending'
            }
            
            safe_print(f"\n{'='*80}")
            safe_print(f"[METRIC] Processing: {metric_name}")
            safe_print(f"[FORMULA] {formula}")
            safe_print(f"[NEEDS] Metrics: {metrics_in_formula}")
            safe_print(f"{'='*80}")
            
            # Fix common pandas import errors in generated code
            code = code.replace('from pandas.DataFrame', 'import pandas as pd')
            code = code.replace('from pandas import DataFrame', 'import pandas as pd')
            
            # DEBUG: Print generated code to see what LLM produced
            safe_print(f"\n{'='*80}")
            safe_print(f"[SEARCH] GENERATED CODE FOR: {metric_name}")
            safe_print(f"{'='*80}")
            safe_print(code)
            safe_print(f"{'='*80}")
            safe_print(f"[FILES] Repository path: {repo_path}")
            safe_print(f"[DATA] DataFrame has {len(df)} rows")
            safe_print(f"[NOTE] First 3 files: {list(df['file'].head(3))}")
            safe_print(f"{'='*80}\n")
            
            # Execute the jury-approved code with proper global/local context
            # Code should be safe since it was verified by 3 judges
            from concurrent.futures import ThreadPoolExecutor, as_completed
            global_vars = {
                'pd': pd, 
                'np': np, 
                'DataFrame': pd.DataFrame, 
                'subprocess': subprocess, 
                'os': os,
                'ThreadPoolExecutor': ThreadPoolExecutor,
                'as_completed': as_completed
            }
            local_vars = {'df': df.copy(), 'repo_path': repo_path, 'progress_callback': progress_callback}
            
            # Execute code to define the function
            try:
                exec(code, global_vars, local_vars)
            except SyntaxError as se:
                safe_print(f"[ERROR] Syntax error in generated code: {se}")
                errors.append(f"{metric_name}: Syntax error in generated code: {str(se)}")
                continue
            except Exception as exec_error:
                safe_print(f"[ERROR] Error during code execution: {exec_error}")
                errors.append(f"{metric_name}: Code execution failed: {str(exec_error)}")
                continue
            
            # IMPORTANT: Call the generated function if it exists
            result_df = None
            if 'calculate_formulas' in local_vars:
                try:
                    # Pass repo_path to function so it can query git
                    # Add timeout for git operations
                    from concurrent.futures import TimeoutError as FutureTimeoutError
                    
                    result_df = local_vars['calculate_formulas'](df, repo_path=repo_path)
                    
                    if result_df is not None and isinstance(result_df, pd.DataFrame):
                        df = result_df
                        safe_print(f"[OK] Function returned DataFrame with {len(df.columns)} columns")
                    else:
                        safe_print(f"[ERROR] Function did not return DataFrame: {type(result_df)}")
                        errors.append(f"{metric_name}: Function did not return DataFrame")
                        continue
                except FutureTimeoutError:
                    safe_print(f"[ERROR] Git operations timed out for {metric_name}")
                    errors.append(f"{metric_name}: Git operations timeout")
                    continue
                except Exception as func_error:
                    safe_print(f"[ERROR] Error calling calculate_formulas: {func_error}")
                    safe_print(f"Error type: {type(func_error)}")
                    import traceback
                    safe_print(traceback.format_exc())
                    errors.append(f"{metric_name}: Function call failed: {str(func_error)}")
                    continue
            else:
                safe_print(f"[ERROR] No calculate_formulas function found in generated code")
                errors.append(f"{metric_name}: No calculate_formulas function in generated code")
                continue
            
            # Check if new columns were added
            new_cols = set(df.columns) - original_columns
            if new_cols:
                applied_count += 1
                extraction_metadata[metric_name]['status'] = 'success'
                extraction_metadata[metric_name]['columns_created'] = list(new_cols)
                safe_print(f"[OK] Applied: {metric_name}")
                safe_print(f"[CREATED] Columns: {new_cols}")
                safe_print(f"[COUNT] Total columns: {len(df.columns)}")
            else:
                extraction_metadata[metric_name]['status'] = 'failed_no_columns'
                safe_print(f"[ERROR] No new columns added for {metric_name}")
                errors.append(f"{metric_name}: No new columns created")
                
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            extraction_metadata[metric_name]['status'] = 'error'
            extraction_metadata[metric_name]['error'] = str(e)
            errors.append(f"{metric_name}: {str(e)}")
            safe_print(f"[ERROR] Error applying {metric_name}:")
            safe_print(error_detail)
            continue
    
    # Summary of what was extracted
    safe_print(f"\n{'='*80}")
    safe_print(f"[SUMMARY] Metric Extraction Results")
    safe_print(f"{'='*80}")
    for metric_name, metadata in extraction_metadata.items():
        safe_print(f"[{metadata['status'].upper()}] {metric_name}")
        if 'columns_created' in metadata:
            safe_print(f"         Created: {metadata['columns_created']}")
        if 'error' in metadata:
            safe_print(f"         Error: {metadata['error']}")
    safe_print(f"{'='*80}\n")
    
    # Update extracted_data with new columns
    updated_data = df.to_dict('records')
    
    return updated_data, applied_count, errors


def generate_dataset_file(extracted_data: List[Dict], config: Dict) -> tuple:
    """
    Generate dataset file with all metrics
    
    Returns: (output_file, df, error)
    """
    if not extracted_data:
        return None, None, "No data to save"
    
    # Convert to DataFrame
    df = pd.DataFrame(extracted_data)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "generated_datasets"
    output_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    benchmark = config.get('benchmark')
    
    if benchmark:
        filename = f"{benchmark.lower()}_{timestamp}.csv"
    else:
        filename = f"custom_dataset_{timestamp}.csv"
    
    output_file = output_dir / filename
    
    try:
        # Save CSV
        df.to_csv(output_file, index=False)
        return str(output_file), df, None
    except Exception as e:
        return None, None, str(e)


def create_feedback_dialog(root, result_info: Dict, on_feedback_callback):
    """
    Create feedback dialog to collect user response
    
    result_info should contain:
    - file_path: str
    - df: DataFrame
    - custom_metrics: List[Dict]
    """
    dialog = tk.Toplevel(root)
    dialog.title("[DATA] Dataset Generated - Your Feedback")
    dialog.geometry("600x550")
    dialog.transient(root)
    dialog.grab_set()
    
    # Success header
    ttk.Label(dialog, text="[OK] Dataset Generated Successfully!",
             font=('Segoe UI', 14, 'bold'), foreground='green').pack(pady=10)
    
    df = result_info['df']
    file_path = result_info['file_path']
    
    # Stats
    stats_frame = ttk.LabelFrame(dialog, text="[CHART] Statistics", padding=10)
    stats_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(stats_frame, text=f"Rows: {len(df):,}", font=('Segoe UI', 10)).pack(anchor=tk.W)
    ttk.Label(stats_frame, text=f"Columns: {len(df.columns)}", font=('Segoe UI', 10)).pack(anchor=tk.W)
    ttk.Label(stats_frame, text=f"File: {os.path.basename(file_path)}", font=('Segoe UI', 10)).pack(anchor=tk.W)
    
    # Show columns
    cols_text = ", ".join(list(df.columns)[:10])
    if len(df.columns) > 10:
        cols_text += f" (+{len(df.columns)-10} more)"
    ttk.Label(stats_frame, text=f"Columns: {cols_text}", 
             font=('Segoe UI', 9), wraplength=500).pack(anchor=tk.W, pady=5)
    
    # Custom metrics status
    custom_metrics = result_info.get('custom_metrics', [])
    if custom_metrics:
        custom_frame = ttk.LabelFrame(dialog, text="🧮 Custom Metrics (Jury Approved)", padding=10)
        custom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        for custom in custom_metrics:
            name = custom.get('name')
            # Check if metric exists in any column
            exists = name in df.columns or any(name.lower() in str(col).lower() for col in df.columns)
            status = "[OK] Applied" if exists else "[WARNING] Not Found"
            ttk.Label(custom_frame, text=f"{status}: {name}", 
                     font=('Segoe UI', 9)).pack(anchor=tk.W)
    
    # Preview
    preview_frame = ttk.LabelFrame(dialog, text="[PREVIEW] Preview (First 3 rows)", padding=10)
    preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    preview_text = scrolledtext.ScrolledText(preview_frame, height=6, wrap=tk.NONE,
                                             font=('Consolas', 8))
    preview_text.pack(fill=tk.BOTH, expand=True)
    preview_text.insert('1.0', df.head(3).to_string())
    preview_text.config(state=tk.DISABLED)
    
    # Feedback section
    feedback_frame = ttk.LabelFrame(dialog, text="💬 Your Feedback", padding=10)
    feedback_frame.pack(fill=tk.X, padx=10, pady=10)
    
    ttk.Label(feedback_frame, text="How does this dataset look?").pack(anchor=tk.W)
    
    rating_var = tk.StringVar()
    ttk.Radiobutton(feedback_frame, text="[OK] Perfect - exactly what I needed",
                   variable=rating_var, value="perfect").pack(anchor=tk.W, pady=2)
    ttk.Radiobutton(feedback_frame, text="👍 Good - mostly correct",
                   variable=rating_var, value="good").pack(anchor=tk.W, pady=2)
    ttk.Radiobutton(feedback_frame, text="[WARNING] Needs improvement - missing something",
                   variable=rating_var, value="needs_work").pack(anchor=tk.W, pady=2)
    ttk.Radiobutton(feedback_frame, text="[ERROR] Not what I wanted - start over",
                   variable=rating_var, value="wrong").pack(anchor=tk.W, pady=2)
    
    # Actions
    action_frame = ttk.Frame(dialog)
    action_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def submit_feedback():
        rating = rating_var.get()
        if not rating:
            messagebox.showwarning("No Rating", "Please select a rating first")
            return
        
        feedback_data = {
            'rating': rating,
            'file': file_path,
            'rows': len(df),
            'columns': list(df.columns)
        }
        
        if on_feedback_callback:
            on_feedback_callback(feedback_data)
        
        messagebox.showinfo("Thank You!", "Feedback recorded! [SUCCESS]\n\nYou can:\n• Modify and regenerate\n• Create new dataset\n• Export results")
        dialog.destroy()
    
    def open_file():
        import subprocess
        import platform
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")
    
    def open_folder():
        import subprocess
        import platform
        folder = os.path.dirname(file_path)
        try:
            if platform.system() == 'Windows':
                subprocess.run(['explorer', folder])
            elif platform.system() == 'Darwin':
                subprocess.run(['open', folder])
            else:
                subprocess.run(['xdg-open', folder])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
    
    ttk.Button(action_frame, text="📄 Open CSV", command=open_file).pack(side=tk.LEFT, padx=2)
    ttk.Button(action_frame, text="[FILES] Open Folder", command=open_folder).pack(side=tk.LEFT, padx=2)
    ttk.Button(action_frame, text="📤 Submit Feedback", command=submit_feedback).pack(side=tk.LEFT, padx=2)
    ttk.Button(action_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=2)