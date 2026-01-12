#!/usr/bin/env python3
"""Test MetricsHelper from GUI context"""

import sys
import os
from pathlib import Path

# Setup paths like GUI does
gui_dir = Path(__file__).parent
dataset_dir = gui_dir.parent
sys.path.insert(0, str(dataset_dir))

os.chdir(dataset_dir)

print(f"[TEST] Current dir: {os.getcwd()}")
print(f"[TEST] sys.path[0]: {sys.path[0]}")

# Import MetricsHelper
try:
    sys.path.insert(0, str(dataset_dir / "dataset_generators"))
    from metrics_helper import MetricsHelper
    print("[TEST] MetricsHelper imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import MetricsHelper: {e}")
    sys.exit(1)

# Create helper
repo_path = r"d:\GitIntel\kafka"
test_file = r"d:\GitIntel\kafka\clients\src\main\java\org\apache\kafka\common\Uuid.java"

print(f"[TEST] Creating MetricsHelper for: {repo_path}")
try:
    helper = MetricsHelper(repo_path)
    print("[TEST] MetricsHelper created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create MetricsHelper: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Get metrics
print(f"[TEST] Getting metrics for: {Path(test_file).name}")
try:
    result = helper.get_all_metrics(test_file)
    
    print(f"\n[RESULT]")
    print(f"  Result type: {type(result)}")
    print(f"  Result keys: {list(result.keys())}")
    print(f"  Metrics dict size: {len(result.get('metrics', {}))}")
    
    if 'metrics' in result:
        metrics = result['metrics']
        print(f"\n[METRICS]")
        print(f"  Total metrics: {len(metrics)}")
        print(f"  Sample keys: {list(metrics.keys())[:15]}")
        print(f"  Sample values:")
        for i, (key, value) in enumerate(list(metrics.items())[:5], 1):
            print(f"    {i}. {key} = {value}")
    else:
        print("[WARNING] No 'metrics' key in result!")
        print(f"[DEBUG] Full result: {result}")
        
except Exception as e:
    print(f"[ERROR] Failed to get metrics: {e}")
    import traceback
    traceback.print_exc()
