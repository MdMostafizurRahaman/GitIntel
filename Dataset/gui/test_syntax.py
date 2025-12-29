"""
Quick test to verify main.py syntax
"""
import sys
sys.dont_write_bytecode = True

try:
    import main
    print("✅ main.py imports successfully")
    print("✅ No syntax errors found")
except Exception as e:
    print(f"❌ Error importing main.py: {e}")
    import traceback
    traceback.print_exc()
