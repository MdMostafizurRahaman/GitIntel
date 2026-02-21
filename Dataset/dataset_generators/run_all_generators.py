"""
Dataset Generators - Main Orchestrator
All benchmark generation routes through MetricsCatalog.generate_benchmark()
"""

import sys
from pathlib import Path

# Ensure Dataset/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from metrics_catalog import MetricsCatalog


BENCHMARKS = ["defects4j", "bugsjar", "manystubs4j",
              "codexglue", "codesearchnet", "sourcerer", "promise"]


def _print_menu():
    print("\n" + "="*70)
    print("REAL DATASET GENERATORS - NO SYNTHETIC DATA")
    print("="*70)
    print("\nAvailable Datasets (all extract REAL data from source code / git):")
    for i, name in enumerate(BENCHMARKS, 1):
        info = MetricsCatalog.BENCHMARKS.get(name, {})
        print(f"  {i}. {name.upper():16} - {info.get('description', '')}")
    print(f"  {len(BENCHMARKS)+1}. Generate ALL datasets")
    print("  0. Exit")
    print("="*70)


def _run(name: str, repo_path: str, **kwargs) -> bool:
    print(f"\nGenerating {name.upper()} dataset...")
    result = MetricsCatalog.generate_benchmark(name, repo_path, **kwargs)
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return False
    print(f"  SUCCESS: {result.get('total_files') or result.get('total_bugs') or result.get('total_commits') or '?'} records")
    print(f"  Output: {result.get('output_dir', 'n/a')}")
    return True


def run_all(repo_path: str, **kwargs):
    print("\n" + " GENERATING ALL DATASETS ".center(70, "="))
    results = {name: _run(name, repo_path, **kwargs) for name in BENCHMARKS}
    print("\n" + " SUMMARY ".center(70, "="))
    ok = sum(v for v in results.values())
    for name, success in results.items():
        print(f"  {name.upper():20} {'SUCCESS' if success else 'FAILED'}")
    print(f"\nCompleted: {ok}/{len(BENCHMARKS)} datasets generated successfully")
    print("="*70)


def main():
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
        choice = sys.argv[2] if len(sys.argv) > 2 else str(len(BENCHMARKS)+1)
    else:
        _print_menu()
        repo_path = input("\nEnter repository path: ").strip()
        if not repo_path or not Path(repo_path).exists():
            print("ERROR: Invalid repository path")
            return
        choice = input("\nEnter choice (0-{len(BENCHMARKS)+1}): ").strip()

    if choice == "0":
        print("Goodbye!")
    elif choice == str(len(BENCHMARKS)+1):
        run_all(repo_path)
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(BENCHMARKS):
                _run(BENCHMARKS[idx], repo_path)
            else:
                print("ERROR: Invalid choice")
        except ValueError:
            print("ERROR: Invalid choice")


if __name__ == "__main__":
    main()
