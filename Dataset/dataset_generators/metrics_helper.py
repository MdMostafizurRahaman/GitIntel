import os
from pathlib import Path
from typing import Dict, Any


class MetricsHelper:
    """
    Compatibility wrapper used by the GUI and generators.
    All metric logic delegates to MetricsCatalog (single entry point).
    No duplicate metric calculation code here.
    """

    def __init__(self, repo_path: str):
        self.repo_path = str(repo_path)

    # ------------------------------------------------------------------
    def _catalog(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from metrics_catalog import MetricsCatalog
        return MetricsCatalog

    def _flat(self, file_path: str, selected_metrics: list = None) -> Dict[str, Any]:
        """Return flat metrics dict via MetricsCatalog."""
        return self._catalog().calculate_all_metrics(file_path, self.repo_path, selected_metrics=selected_metrics)

    # ------------------------------------------------------------------
    def get_all_metrics(self, file_path: str = None, selected_metrics: list = None) -> Dict[str, Any]:
        """
        Return {'metrics': {N metrics}} for a file.
        Pass selected_metrics to only compute what is needed.
        GUI reads result.get('metrics', {}) from this.
        """
        try:
            if file_path:
                path = file_path if os.path.isabs(file_path) else str(Path(self.repo_path) / file_path)
                if not os.path.isfile(path):
                    print(f"[WARNING MetricsHelper] File not found: {path}")
                    return {"metrics": {}}
                m = self._flat(path, selected_metrics)
                label = f"{len(selected_metrics)} selected" if selected_metrics else f"{len(m)}"
                print(f"[DEBUG MetricsHelper] {os.path.basename(path)}: {label} metrics")
                return {"metrics": m}
            else:
                combined = {}
                root = Path(self.repo_path)
                for p in list(root.rglob("*.java")) + list(root.rglob("*.py")):
                    if ".git" not in p.parts:
                        combined[str(p)] = self._flat(str(p), selected_metrics)
                return {"metrics": combined}
        except Exception as e:
            print(f"[ERROR MetricsHelper] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return {"metrics": {}}

    def get_loc_metrics(self, file_path: str) -> Dict:
        try:
            return self._catalog().calculate_loc_metrics(file_path)
        except Exception:
            return {"loc": 0, "kloc": 0, "soc": 0, "cloc": 0, "bloc": 0}

    def get_ck_metrics(self, file_path: str) -> Dict:
        try:
            return self._catalog().calculate_ck_metrics(file_path)
        except Exception:
            return {"wmc": 0, "dit": 0, "noc": 0, "cbo": 0, "rfc": 0, "lcom": 0}

    def get_complexity_metrics(self, file_path: str) -> Dict:
        try:
            return self._catalog().calculate_complexity_metrics(file_path)
        except Exception:
            return {"cyclomatic_complexity": 0, "cognitive_complexity": 0,
                    "essential_complexity": 0, "max_nesting_depth": 0}

    def get_halstead_metrics(self, file_path: str) -> Dict:
        try:
            m = self._flat(file_path)
            return {k: m.get(k, 0) for k in (
                "halstead_volume", "halstead_difficulty", "halstead_effort",
                "halstead_time", "halstead_bugs"
            )}
        except Exception:
            return {"halstead_volume": 0, "halstead_difficulty": 0,
                    "halstead_effort": 0, "halstead_time": 0, "halstead_bugs": 0}

    def get_defect_metrics(self, file_path: str) -> Dict:
        try:
            m = self._flat(file_path)
            return {
                "bug_count": m.get("num_bugs", 0),
                "bug_density": m.get("bug_density", 0),
                "vulnerabilities": m.get("vulnerabilities", 0),
                "is_defective": bool(m.get("has_defect", False)),
            }
        except Exception:
            return {"bug_count": 0, "bug_density": 0, "vulnerabilities": 0, "is_defective": False}

    def get_quality_metrics(self, file_path: str) -> Dict:
        try:
            m = self._flat(file_path)
            return {
                "code_duplication": m.get("duplication", 0),
                "comment_ratio": m.get("comment_ratio", 0),
                "documentation_coverage": m.get("documentation", 0),
            }
        except Exception:
            return {"code_duplication": 0, "comment_ratio": 0, "documentation_coverage": 0}


def get_metrics_helper(repo_path: str) -> MetricsHelper:
    return MetricsHelper(repo_path)
