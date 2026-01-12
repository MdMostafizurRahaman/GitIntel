"""
Master script to generate ALL 6 benchmark datasets
Following official structures:

"""

import sys
from pathlib import Path

# Import all generators
from defects4j_generator import Defects4JGenerator
from bugsjar_generator import BugsJarGenerator  
from codexglue_generator import CodeXGLUEGenerator


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_all_benchmarks.py <repo_path> [commit_limit]")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    commit_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    
    print("=" * 80)
    print("GENERATING ALL 7 OFFICIAL BENCHMARK DATASETS")
    print("=" * 80)
    
    results = {}
    
    # 1. Defects4J
    print("\n[1/7] Generating Defects4J dataset...")
    print("-" * 80)
    try:
        gen = Defects4JGenerator(repo_path, commit_limit=commit_limit)
        result = gen.generate()
        results['Defects4J'] = result
        if 'error' not in result:
            print(f"SUCCESS Defects4J: {result['total_bugs']} bugs")
        else:
            print(f"ERROR Defects4J: {result['error']}")
    except Exception as e:
        print(f"ERROR Defects4J failed: {e}")
        results['Defects4J'] = {'error': str(e)}
    
    # 2. Bugs.jar
    print("\n[2/7] Generating Bugs.jar dataset...")
    print("-" * 80)
    try:
        gen = BugsJarGenerator(repo_path, commit_limit=commit_limit)
        result = gen.generate()
        results['Bugs.jar'] = result
        if 'error' not in result:
            print(f"SUCCESS Bugs.jar: {result.get('total_commits', 0)} commits")
        else:
            print(f"ERROR Bugs.jar: {result['error']}")
    except Exception as e:
        print(f"ERROR Bugs.jar failed: {e}")
        results['Bugs.jar'] = {'error': str(e)}
    
    # 3. CodeXGLUE
    print("\n[3/7] Generating CodeXGLUE dataset...")
    print("-" * 80)
    try:
        gen = CodeXGLUEGenerator(repo_path, commit_limit=commit_limit)
        result = gen.generate()
        results['CodeXGLUE'] = result
        if 'error' not in result:
            print(f"SUCCESS CodeXGLUE: {result['total_commits']} commits")
            for task, count in result.get('tasks', {}).items():
                print(f"   - {task}: {count}")
        else:
            print(f"ERROR CodeXGLUE: {result['error']}")
    except Exception as e:
        print(f"ERROR CodeXGLUE failed: {e}")
        results['CodeXGLUE'] = {'error': str(e)}
    
    # 4. ManySStuBs4J
    print("\n[4/7] Generating ManySStuBs4J dataset...")
    print("-" * 80)
    try:
        from manystubs4j_generator import ManySStuBs4JGenerator
        gen = ManySStuBs4JGenerator(repo_path, commit_limit=commit_limit)
        result = gen.generate()
        results['ManySStuBs4J'] = result
        if 'error' not in result:
            print(f"SUCCESS ManySStuBs4J: {result.get('total_bugs', 0)} bugs")
        else:
            print(f"ERROR ManySStuBs4J: {result['error']}")
    except Exception as e:
        print(f"ERROR ManySStuBs4J failed: {e}")
        results['ManySStuBs4J'] = {'error': str(e)}
    
    # 5. CodeSearchNet  
    print("\n[5/7] Generating CodeSearchNet dataset...")
    print("-" * 80)
    try:
        from codesearchnet_generator import CodeSearchNetGenerator
        gen = CodeSearchNetGenerator(repo_path, file_limit=commit_limit)
        result = gen.generate()
        results['CodeSearchNet'] = result
        if 'error' not in result:
            print(f"SUCCESS CodeSearchNet: {result.get('total_functions', 0)} functions")
        else:
            print(f"ERROR CodeSearchNet: {result['error']}")
    except Exception as e:
        print(f"ERROR CodeSearchNet failed: {e}")
        results['CodeSearchNet'] = {'error': str(e)}
    
    # 6. Sourcerer
    print("\n[6/7] Generating Sourcerer dataset...")
    print("-" * 80)
    try:
        from sourcerer_generator import SourcererGenerator
        gen = SourcererGenerator(repo_path, file_limit=commit_limit)
        result = gen.generate()
        results['Sourcerer'] = result
        if 'error' not in result:
            print(f"SUCCESS Sourcerer: {result.get('total_entities', 0)} entities")
        else:
            print(f"ERROR Sourcerer: {result['error']}")
    except Exception as e:
        print(f"ERROR Sourcerer failed: {e}")
        results['Sourcerer'] = {'error': str(e)}
    
    # 7. PROMISE
    print("\n[7/7] Generating PROMISE dataset...")
    print("-" * 80)
    try:
        from promise_generator import PROMISEGenerator
        gen = PROMISEGenerator(repo_path, file_limit=commit_limit)
        result = gen.generate()
        results['PROMISE'] = result
        if 'error' not in result:
            print(f"SUCCESS PROMISE: {result.get('total_files', 0)} files")
        else:
            print(f"ERROR PROMISE: {result['error']}")
    except Exception as e:
        print(f"ERROR PROMISE failed: {e}")
        results['PROMISE'] = {'error': str(e)}
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - ALL BENCHMARKS")
    print("=" * 80)
    
    success_count = sum(1 for r in results.values() if 'error' not in r)
    print(f"\nSuccessfully generated: {success_count}/7 benchmarks")
    print(f"Failed: {7 - success_count}/7 benchmarks")
    
    print("\nDetails:")
    for name, result in results.items():
        if 'error' in result:
            print(f"   ERROR {name}: {str(result['error'])[:50]}...")
        else:
            print(f"   SUCCESS {name}: Generated successfully")
    
    print("\n" + "=" * 80)
    return results


if __name__ == "__main__":
    main()
