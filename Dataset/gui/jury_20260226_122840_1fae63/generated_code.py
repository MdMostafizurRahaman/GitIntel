import os
from typing import Dict, Any
from metrics_catalog import MetricsCatalog

def calculate(file_path: str, repo_path: str = None) -> Dict[str, Any]:
    """Calculate bug-related metrics and generate benchmarks for a given file/repo.

    Args:
        file_path: Path to the source code file
        repo_path: Optional path to git repository containing the file

    Returns:
        Dictionary containing metrics, benchmarks and error information
    """
    result = {
        "metrics": {},
        "benchmarks": {},
        "error": None
    }

    # Early validation of file path
    if not os.path.exists(file_path):
        result['error'] = f"File not found: {file_path}"
        return result

    try:
        # Calculate all metrics for the file
        metrics = MetricsCatalog.calculate_all_metrics(file_path, repo_path)
        
        # Filter for requested metrics only
        requested_metrics = [
            'num_authors', 'num_commits', 'bug_density', 'num_bugs',
            'pre_release_bugs', 'post_release_bugs', 'bug_fix_time',
            'defect_type', 'severity', 'priority'
        ]
        result['metrics'] = {k: metrics[k] for k in requested_metrics if k in metrics}
        
        # Generate requested benchmarks if repo_path provided
        if repo_path and os.path.exists(repo_path):
            benchmarks_dir = os.path.join(os.path.dirname(file_path), 'benchmarks')
            os.makedirs(benchmarks_dir, exist_ok=True)
            
            for benchmark in ['defects4j', 'bugsjar']:
                try:
                    benchmark_data = MetricsCatalog.generate_benchmark(
                        benchmark_name=benchmark,
                        repo_path=repo_path,
                        output_dir=benchmarks_dir
                    )
                    result['benchmarks'][benchmark] = benchmark_data
                except Exception as e:
                    result['benchmarks'][benchmark] = {"error": str(e)}
        elif repo_path:
            result['error'] = f"Repository path not found: {repo_path}"

    except Exception as e:
        result['error'] = str(e)

    return result


import csv as _csv
import argparse as _argparse

_REQUESTED_METRICS = ['num_authors', 'num_commits', 'bug_density', 'num_bugs', 'pre_release_bugs', 'post_release_bugs', 'bug_fix_time', 'defect_type', 'severity', 'priority']


def _collect_files(repo_path: str, ext: str = ".java"):
    """Walk repo_path and yield paths of files matching ext."""
    import os as _os
    for root, _, files in _os.walk(repo_path):
        for fname in files:
            if fname.endswith(ext):
                yield _os.path.join(root, fname)


def generate_csv(repo_path: str, output_csv: str, file_limit: int = None) -> str:
    """Calculate metrics for every source file in repo_path and write a CSV.

    Args:
        repo_path:   Absolute path to the git repository root.
        output_csv:  Destination CSV file path.
        file_limit:  Optional cap on the number of files processed.

    Returns:
        Path to the written CSV.
    """
    import os as _os
    if not _os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path does not exist: {repo_path}")
    if not _os.path.exists(_os.path.join(repo_path, ".git")):
        raise ValueError(f"Not a git repository: {repo_path}")

    files = list(_collect_files(repo_path))
    if file_limit:
        files = files[:file_limit]
    if not files:
        raise RuntimeError(f"No source files found in: {repo_path}")

    fieldnames = ["file_path"] + list(_REQUESTED_METRICS) + ["error"]
    _os.makedirs(_os.path.dirname(_os.path.abspath(output_csv)), exist_ok=True)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for idx, fpath in enumerate(files, 1):
            print(f"[{idx}/{len(files)}] {_os.path.relpath(fpath, repo_path)}")
            result = calculate(fpath, repo_path)
            row = {"file_path": _os.path.relpath(fpath, repo_path)}
            row.update(result.get("metrics", {}))
            row["error"] = result.get("error") or ""
            writer.writerow(row)

    print(f"\nDone — {len(files)} rows written to: {output_csv}")
    return output_csv


def main():
    import os as _os, sys as _sys
    parser = _argparse.ArgumentParser(
        description="Generate metrics CSV from a git repository."
    )
    parser.add_argument(
        "repo_path", nargs="?", default=None,
        help="Path to the git repository. Falls back to ConfigManager default.",
    )
    parser.add_argument("-o", "--output", default=None,
                        help="Output CSV path. Default: <repo_name>_metrics.csv.")
    parser.add_argument("--limit", type=int, default=None, metavar="N",
                        help="Process only the first N source files.")
    args = parser.parse_args()

    repo_path = args.repo_path
    if not repo_path:
        try:
            _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
            from config.config_manager import ConfigManager
            repo_path = ConfigManager().get_repo_path()
            print(f"Using configured repo: {repo_path}")
        except Exception:
            parser.error(
                "No repo_path supplied and no default found in config. "
                "Pass the repo path as the first argument."
            )

    repo_path = _os.path.abspath(repo_path)
    repo_name = _os.path.basename(repo_path)
    output_csv = args.output or _os.path.join(
        _os.path.dirname(_os.path.abspath(__file__)),
        f"{repo_name}_metrics.csv",
    )

    generate_csv(repo_path, output_csv, file_limit=args.limit)


if __name__ == "__main__":
    main()
