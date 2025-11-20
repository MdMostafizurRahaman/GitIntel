"""
Professional Dataset Generator
Creates datasets similar to Defects4J, Bugs.jar, CodeXGLUE, etc. from existing repositories
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProfessionalDatasetGenerator:
    """Generates professional-quality datasets from Java repositories"""

    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)
        self.output_dir = Path("d:\\GitIntel\\GitIntelProject\\Dataset\\generated_datasets")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repositories = self._find_repositories()

    def _find_repositories(self) -> List[Dict]:
        """Find all git repositories in workspace"""
        repos = []
        for item in self.workspace.iterdir():
            if item.is_dir() and (item / ".git").exists():
                repos.append({
                    "name": item.name,
                    "path": item,
                    "type": self._classify_repository(item)
                })
        return repos

    def _classify_repository(self, repo_path: Path) -> str:
        """Classify repository type"""
        if (repo_path / "pom.xml").exists():
            return "maven"
        elif (repo_path / "build.gradle").exists():
            return "gradle"
        elif (repo_path / "src").exists():
            return "java"
        else:
            return "unknown"

    def generate_all_datasets(self):
        """Generate all types of professional datasets"""
        logger.info("Starting professional dataset generation...")

        # Generate datasets
        self.generate_defects4j_dataset()
        self.generate_bugs_jar_dataset()
        self.generate_codexglue_dataset()
        self.generate_codesearchnet_dataset()
        self.generate_sourcerer_dataset()
        self.generate_promise_dataset()
        self.generate_manystubs4j_dataset()

        logger.info("All datasets generated successfully!")

    def generate_defects4j_dataset(self):
        """Generate Defects4J-style bug fix dataset"""
        logger.info("Generating Defects4J-style dataset...")

        dataset = []
        dataset_dir = self.output_dir / "defects4j_dataset"
        dataset_dir.mkdir(exist_ok=True)

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                logger.info(f"Processing {repo['name']} for Defects4J dataset...")

                java_files = list(repo["path"].rglob("*.java"))[:10]  # Process first 10 files
                for i, java_file in enumerate(java_files):
                    try:
                        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        # Create synthetic bug-fix pair
                        buggy_code = code.replace(' == ', ' = ', 1) if ' == ' in code else code

                        if buggy_code != code:  # Only if we could introduce a bug
                            record = {
                                "bug_id": f"{repo['name']}_bug_{i+1:03d}",
                                "project": repo['name'],
                                "file_path": str(java_file.relative_to(repo["path"])),
                                "buggy_code": buggy_code,
                                "fixed_code": code,
                                "bug_type": "synthetic_equality",
                                "severity": "medium",
                                "language": "java",
                                "dataset_type": "defects4j"
                            }
                            dataset.append(record)

                            # Create Defects4J directory structure
                            bug_dir = dataset_dir / f"bug_{len(dataset):03d}"
                            bug_dir.mkdir(exist_ok=True)

                            with open(bug_dir / "buggy.java", 'w', encoding='utf-8') as f:
                                f.write(buggy_code)
                            with open(bug_dir / "fixed.java", 'w', encoding='utf-8') as f:
                                f.write(code)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        # Save dataset
        output_file = self.output_dir / "defects4j_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Defects4J dataset saved: {len(dataset)} bug pairs")

    def generate_bugs_jar_dataset(self):
        """Generate Bugs.jar-style metrics dataset"""
        logger.info("Generating Bugs.jar-style dataset...")

        dataset = []

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                java_files = list(repo["path"].rglob("*.java"))[:20]
                for java_file in java_files:
                    try:
                        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        # Calculate basic metrics
                        lines = code.split('\n')
                        record = {
                            "project": repo['name'],
                            "file_path": str(java_file.relative_to(repo["path"])),
                            "language": "java",
                            "dataset_type": "bugs_jar",
                            "loc": len(lines),
                            "classes": code.count('class '),
                            "methods": code.count('public ') + code.count('private ') + code.count('protected '),
                            "complexity": code.count('if ') + code.count('for ') + code.count('while ') + 1,
                            "has_bug": False
                        }
                        dataset.append(record)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        output_file = self.output_dir / "bugs_jar_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Bugs.jar dataset saved: {len(dataset)} records")

    def generate_codexglue_dataset(self):
        """Generate CodeXGLUE-style code dataset"""
        logger.info("Generating CodeXGLUE-style dataset...")

        dataset = []

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                java_files = list(repo["path"].rglob("*.java"))[:15]
                for java_file in java_files:
                    try:
                        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        # Extract method signatures
                        import re
                        methods = re.findall(r'public\s+\w+\s+(\w+)\s*\([^)]*\)', code)

                        for method in methods[:3]:  # Limit methods per file
                            record = {
                                "project": repo['name'],
                                "file_path": str(java_file.relative_to(repo["path"])),
                                "language": "java",
                                "dataset_type": "codexglue",
                                "signature": f"{method}()",
                                "code_snippet": code[:1000],  # First 1000 chars
                                "complexity": len(re.findall(r'\b(if|for|while)\b', code))
                            }
                            dataset.append(record)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        output_file = self.output_dir / "codexglue_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"CodeXGLUE dataset saved: {len(dataset)} records")

    def generate_codesearchnet_dataset(self):
        """Generate CodeSearchNet-style dataset"""
        logger.info("Generating CodeSearchNet-style dataset...")

        dataset = []

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                java_files = list(repo["path"].rglob("*.java"))[:10]
                for java_file in java_files:
                    try:
                        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        # Create synthetic documentation
                        record = {
                            "project": repo['name'],
                            "file_path": str(java_file.relative_to(repo["path"])),
                            "language": "java",
                            "dataset_type": "codesearchnet",
                            "code": code,
                            "docstring": f"This is a Java class from {repo['name']} project",
                            "code_tokens": code.split(),
                            "docstring_tokens": f"This is a Java class from {repo['name']} project".split()
                        }
                        dataset.append(record)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        output_file = self.output_dir / "codesearchnet_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"CodeSearchNet dataset saved: {len(dataset)} records")

    def generate_sourcerer_dataset(self):
        """Generate Sourcerer-style dataset"""
        logger.info("Generating Sourcerer-style dataset...")

        dataset = []

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                java_files = list(repo["path"].rglob("*.java"))[:25]
                for java_file in java_files:
                    try:
                        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        record = {
                            "project": repo['name'],
                            "file_path": str(java_file.relative_to(repo["path"])),
                            "language": "java",
                            "dataset_type": "sourcerer",
                            "code": code,
                            "file_size": len(code),
                            "line_count": len(code.split('\n')),
                            "has_pom": (repo["path"] / "pom.xml").exists(),
                            "has_gradle": (repo["path"] / "build.gradle").exists()
                        }
                        dataset.append(record)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        output_file = self.output_dir / "sourcerer_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"Sourcerer dataset saved: {len(dataset)} records")

    def generate_promise_dataset(self):
        """Generate PROMISE-style dataset"""
        logger.info("Generating PROMISE-style dataset...")

        dataset = []
        from extractors.metrics_extractors import PROMISEExtractor

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                java_files = list(repo["path"].rglob("*.java"))[:30]
                for java_file in java_files:
                    try:
                        # Use PROMISEExtractor to get comprehensive metrics
                        extractor = PROMISEExtractor(str(java_file), {})
                        metrics = extractor._analyze_java_file(str(java_file))
                        
                        record = {
                            "project": repo['name'],
                            "file": str(java_file.relative_to(repo["path"])),
                            "language": "java",
                            "dataset_type": "promise",
                            **metrics,  # Include all calculated metrics
                            "defects": 0
                        }
                        dataset.append(record)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        # Save as CSV
        csv_file = self.output_dir / "promise_dataset.csv"
        if dataset:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=dataset[0].keys())
                writer.writeheader()
                writer.writerows(dataset)

        # Also save as JSON with full metrics
        json_file = self.output_dir / "promise_dataset.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"PROMISE dataset saved: {len(dataset)} records")

    def generate_manystubs4j_dataset(self):
        """Generate ManySStuBs4J-style dataset"""
        logger.info("Generating ManySStuBs4J-style dataset...")

        dataset = []

        for repo in self.repositories:
            if repo["type"] in ["maven", "gradle", "java"]:
                java_files = list(repo["path"].rglob("*.java"))[:5]
                for i, java_file in enumerate(java_files):
                    try:
                        with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        record = {
                            "issue_id": f"{repo['name']}_issue_{i+1:03d}",
                            "project": repo['name'],
                            "file_path": str(java_file.relative_to(repo["path"])),
                            "issue_type": "Code Quality Issue",
                            "severity": "medium",
                            "description": f"Synthetic issue in {java_file.name}",
                            "code_snippet": code[:500],
                            "dataset_type": "manystubs4j"
                        }
                        dataset.append(record)

                    except Exception as e:
                        logger.warning(f"Error processing {java_file}: {e}")

        output_file = self.output_dir / "manystubs4j_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)

        logger.info(f"ManySStuBs4J dataset saved: {len(dataset)} records")

def main():
    """Main entry point"""
    workspace_path = "d:\\GitIntel"

    generator = ProfessionalDatasetGenerator(workspace_path)
    generator.generate_all_datasets()

    print("🎉 All professional datasets generated successfully!")
    print(f"📁 Check the output directory: {generator.output_dir}")

if __name__ == "__main__":
    main()