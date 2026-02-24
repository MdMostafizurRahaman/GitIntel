"""
PROMISE Dataset Generator
Generates datasets matching the original PROMISE / DefectData schema:
  name, version, name (class), wmc, dit, noc, cbo, rfc, lcom, ca, ce,
  npm, lcom3, loc, dam, moa, mfa, cam, ic, cbm, amc, max_cc, avg_cc, bug
Reference: https://github.com/klainfo/DefectData
"""

import os
import re
import json
import csv
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

try:
    import lizard
    LIZARD_AVAILABLE = True
except ImportError:
    LIZARD_AVAILABLE = False
    print("WARNING: lizard not installed. Install with: pip install lizard")



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Original PROMISE CK CSV columns (24 total — note: "name" appears twice)
PROMISE_CSV_COLUMNS = [
    "name", "version", "name",
    "wmc", "dit", "noc", "cbo", "rfc", "lcom",
    "ca", "ce", "npm", "lcom3", "loc",
    "dam", "moa", "mfa", "cam", "ic", "cbm", "amc",
    "max_cc", "avg_cc", "bug"
]


def _extract_fqcn(code: str, file_path: Path) -> str:
    """Extract fully-qualified class name (package.ClassName) from Java source."""
    pkg_match = re.search(r'^\s*package\s+([\w.]+)\s*;', code, re.MULTILINE)
    cls_match = re.search(
        r'(?:^|[\n;{}])\s*(?:public\s+|private\s+|protected\s+|abstract\s+|final\s+)*'
        r'(?:class|interface|enum)\s+(\w+)',
        code, re.MULTILINE
    )
    pkg = pkg_match.group(1) if pkg_match else ""
    cls = cls_match.group(1) if cls_match else file_path.stem
    return f"{pkg}.{cls}" if pkg else cls


def _get_project_version(repo_path: Path) -> str:
    """Return latest git tag as version string, or '1.0' if no tags."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=str(repo_path),
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().lstrip("vV")
    except Exception:
        pass
    return "1.0"


class ProfessionalPROMISEGenerator:
    """Generate PROMISE dataset matching original DefectData CK schema."""

    def __init__(self, repo_path: str, output_dir: str = None, file_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.file_limit = file_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        if not LIZARD_AVAILABLE:
            raise ImportError("Lizard is required. Install: pip install lizard")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized PROMISE generator for {self.repo_path}")
    
    def generate(self) -> Dict:
        """Generate PROMISE dataset matching original DefectData CK CSV schema."""
        logger.info("Generating PROMISE dataset (original DefectData schema)...")

        dataset = []
        dataset_dir = self.output_dir / f"promise_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        project_name = self.repo_path.name
        version = _get_project_version(self.repo_path)

        # Collect Java files
        java_files = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and
                       d not in ['target', 'build', 'node_modules', 'generated_datasets',
                                 'output', '__pycache__', 'venv', '.git']]
            for f in files:
                if f.endswith('.java'):
                    java_files.append(Path(root) / f)

        logger.info(f"Found {len(java_files)} Java files")

        if not java_files:
            logger.warning("No Java files found")
            return {"error": "No Java files found"}

        try:
            for file_path in java_files:
                if self.file_limit and len(dataset) >= self.file_limit:
                    break

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()

                    if not code.strip():
                        continue

                    fqcn = _extract_fqcn(code, file_path)

                    # Lizard for cyclomatic/LOC metrics
                    lizard_result = lizard.analyze_file.analyze_source_code(
                        str(file_path), code
                    )

                    # CK Metrics
                    from metrics_catalog import MetricsCatalog
                    ck_metrics = MetricsCatalog.calculate_ck_metrics(str(file_path))

                    funcs = lizard_result.function_list
                    code_lines = code.split('\n')

                    # npm = number of public methods
                    # Use func.start_line to check the actual method signature line
                    npm = 0
                    for func in funcs:
                        line_idx = func.start_line - 1
                        # Check the signature line + up to 2 lines above (for annotations)
                        check_lines = code_lines[max(0, line_idx - 2): line_idx + 1]
                        if any(re.search(r'\bpublic\b', l) for l in check_lines):
                            npm += 1

                    # lcom3 = Henderson-Sellers approximation
                    lcom3 = round(max(0.0, 1.0 - (1.0 / max(len(funcs), 1))), 4)

                    # dam = private / (private + public + protected) field ratio
                    all_fields = re.findall(
                        r'\b(?:private|public|protected)\s+(?:static\s+)?(?:final\s+)?\w[\w<>\[\]]*\s+\w+\s*[;=]',
                        code)
                    priv_fields = re.findall(
                        r'\bprivate\s+(?:static\s+)?(?:final\s+)?\w[\w<>\[\]]*\s+\w+\s*[;=]',
                        code)
                    dam = round(len(priv_fields) / max(1, len(all_fields)), 4)

                    # moa = fields with user-defined (capitalised) type
                    moa = len(re.findall(
                        r'\b(?:private|public|protected)\s+(?:static\s+)?(?:final\s+)?([A-Z]\w*(?:<[^>]*>)?)\s+\w+\s*[;=]',
                        code))

                    # cam = Cohesion Among Methods
                    # ratio of method pairs sharing ≥1 parameter type to total possible pairs
                    # Extract only the parameter section from func.long_name (after the opening '(')
                    param_type_sets = []
                    for func in funcs:
                        long = func.long_name or ''
                        param_section = re.search(r'\(([^)]*)\)', long)
                        param_text = param_section.group(1) if param_section else ''
                        types = set(re.findall(
                            r'\b([A-Z]\w*|int|long|double|float|boolean|char|byte|short|String)\b',
                            param_text))
                        param_type_sets.append(types)

                    if len(funcs) > 1:
                        shared = sum(
                            1 for i in range(len(param_type_sets))
                            for j in range(i + 1, len(param_type_sets))
                            if param_type_sets[i] & param_type_sets[j]
                        )
                        total_pairs = len(funcs) * (len(funcs) - 1) / 2
                        cam = round(shared / total_pairs, 4)
                    else:
                        cam = 1.0

                    # cbm = sum of (cc - 1) per method ≈ coupling between methods
                    cbm = sum(max(0, func.cyclomatic_complexity - 1) for func in funcs)

                    # amc = average method LOC (consistent with CKMetrics tool definition)
                    amc = round(
                        sum(func.nloc for func in funcs) / max(1, len(funcs)), 4)

                    # Build record matching original PROMISE CK columns exactly
                    record = {
                        "name":    project_name,          # col 1: project name
                        "version": version,                # col 2: version
                        "class":   fqcn,                  # col 3: class (written as "name" in CSV)
                        "wmc":     ck_metrics["wmc"],
                        "dit":     ck_metrics["dit"],
                        "noc":     ck_metrics["noc"],
                        "cbo":     ck_metrics["cbo"],
                        "rfc":     ck_metrics["rfc"],
                        "lcom":    ck_metrics["lcom"],
                        "ca":      0,
                        "ce":      ck_metrics["cbo"],
                        "npm":     npm,
                        "lcom3":   lcom3,
                        "loc":     lizard_result.nloc,
                        "dam":     dam,
                        "moa":     moa,
                        "mfa":     0.0,
                        "cam":     cam,
                        "ic":      0,
                        "cbm":     cbm,
                        "amc":     amc,
                        "max_cc":  max((func.cyclomatic_complexity for func in funcs), default=0),
                        "avg_cc":  round(lizard_result.average_cyclomatic_complexity, 4),
                        "bug":     0,
                    }

                    dataset.append(record)

                    if len(dataset) % 50 == 0:
                        logger.info(f"Processed {len(dataset)} files...")

                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    continue

            logger.info(f"Calculated metrics for {len(dataset)} files")

        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}

        # ── CSV (original PROMISE format: duplicate "name" column) ──────────
        csv_file = dataset_dir / "promise_dataset.csv"
        if dataset:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header: "name" appears twice (project + class), matching original
                writer.writerow(PROMISE_CSV_COLUMNS)
                for rec in dataset:
                    writer.writerow([
                        rec["name"], rec["version"], rec["class"],
                        rec["wmc"], rec["dit"], rec["noc"], rec["cbo"],
                        rec["rfc"], rec["lcom"], rec["ca"], rec["ce"],
                        rec["npm"], rec["lcom3"], rec["loc"], rec["dam"],
                        rec["moa"], rec["mfa"], rec["cam"], rec["ic"],
                        rec["cbm"], rec["amc"], rec["max_cc"], rec["avg_cc"],
                        rec["bug"],
                    ])

        # ── JSON ─────────────────────────────────────────────────────────────
        output_file = dataset_dir / "promise_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'PROMISE',
                'description': 'PROMISE defect prediction dataset (DefectData CK schema)',
                'source': 'https://github.com/klainfo/DefectData',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_records': len(dataset),
                'columns': PROMISE_CSV_COLUMNS,
                'data': dataset,
            }, f, indent=2, ensure_ascii=False)

        # ── README ───────────────────────────────────────────────────────────
        readme = dataset_dir / "README.md"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(f"""# PROMISE Dataset — {project_name} v{version}

## Overview
Matches the **DefectData** (PROMISE) CK-metrics schema:
https://github.com/klainfo/DefectData

### Structure:
```
promise_dataset_{self.timestamp}/
├── promise_dataset.csv    # 24-column CSV (original schema)
├── promise_dataset.json   # JSON version
└── README.md
```

### Columns (24):
```
name, version, name (class), wmc, dit, noc, cbo, rfc, lcom,
ca, ce, npm, lcom3, loc, dam, moa, mfa, cam, ic, cbm, amc,
max_cc, avg_cc, bug
```

### Statistics:
- **Total records**: {len(dataset)}
- **Project**: {project_name}
- **Version**: {version}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## References
- Paper: Jureczko & Madeyski (2010) — defect prediction with CK metrics
- Data: http://promise.site.uottawa.ca/
""")

        logger.info(f"PROMISE dataset -> {dataset_dir} ({len(dataset)} records, 24 columns)")

        return {
            "status": "success",
            "total_files": len(dataset),
            "columns": 24,
            "output_dir": str(dataset_dir),
            "output_file": str(output_file),
            "csv_file": str(csv_file),
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python professional_promise_generator.py <repo_path> [file_limit]")
        print("Example: python professional_promise_generator.py d:/GitIntel/repo/druid 100")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    file_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    generator = ProfessionalPROMISEGenerator(repo_path, file_limit=file_limit)
    result = generator.generate()
    
    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    else:
        print(f"SUCCESS! Generated {result['total_files']} records with {result['columns']} columns")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()


# Alias for compatibility
PROMISEGenerator = ProfessionalPROMISEGenerator
