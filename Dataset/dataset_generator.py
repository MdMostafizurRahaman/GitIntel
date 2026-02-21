#!/usr/bin/env python3
"""
dataset_generator.py  (singular)
---------------------------------
Compatibility shim used by gui/main.py.
All benchmark generation delegates to MetricsCatalog.generate_benchmark()
which is the single authoritative entry point.
"""
import sys
from pathlib import Path

# Ensure Dataset root is on sys.path when imported from gui/
sys.path.insert(0, str(Path(__file__).parent))

from metrics_catalog import MetricsCatalog


class ProfessionalDatasetGenerator:
    """
    GUI-facing wrapper that maps per-benchmark method calls to
    MetricsCatalog.generate_benchmark(name, repo_path, ...).
    No generation logic lives here.
    """

    def __init__(self, workspace_path: str, commit_limit=None, timestamp=None):
        self.workspace_path = str(workspace_path)
        # commit_limit → file_limit for MetricsCatalog.generate_benchmark
        self.file_limit = int(commit_limit) if commit_limit else None

    # ------------------------------------------------------------------
    # Per-benchmark methods called by gui/main.py
    # ------------------------------------------------------------------

    def generate_defects4j_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "defects4j", self.workspace_path, file_limit=self.file_limit
        )

    def generate_bugs_jar_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "bugsjar", self.workspace_path, file_limit=self.file_limit
        )

    def generate_promise_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "promise", self.workspace_path, file_limit=self.file_limit
        )

    def generate_codexglue_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "codexglue", self.workspace_path, file_limit=self.file_limit
        )

    def generate_codesearchnet_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "codesearchnet", self.workspace_path, file_limit=self.file_limit
        )

    def generate_manystubs4j_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "manystubs4j", self.workspace_path, file_limit=self.file_limit
        )

    def generate_sourcerer_dataset(self):
        return MetricsCatalog.generate_benchmark(
            "sourcerer", self.workspace_path, file_limit=self.file_limit
        )
