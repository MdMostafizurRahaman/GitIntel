import os
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

try:
    import javalang
    JAVALANG_AVAILABLE = True
except ImportError:
    JAVALANG_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CodeSearchNetGenerator:

    def __init__(self, repo_path: str, output_dir: str = None, file_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.file_limit = file_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized CodeSearchNet generator for {self.repo_path}")

    def _get_java_files(self) -> List[Path]:
        """Get Java files up to file_limit."""
        java_files = []
        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')
                       and d not in ['target', 'build', 'node_modules',
                                     'generated_datasets', '__pycache__']]
            for f in files:
                if f.endswith('.java'):
                    java_files.append(Path(root) / f)
                    if self.file_limit and len(java_files) >= self.file_limit:
                        return java_files
        return java_files

    def _get_file_sha(self, file_path: Path) -> str:
        """Get the latest commit SHA that touched this file."""
        try:
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%H', '--', str(file_path.relative_to(self.repo_path))],
                cwd=self.repo_path,
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return ''

    def _extract_javadoc(self, source: str, method_start_line: int) -> str:
        """Extract Javadoc comment immediately preceding a method (line numbers 1-based)."""
        lines = source.split('\n')
        idx = method_start_line - 2  # convert to 0-based, look at line before
        # Walk backward to find /** ... */
        end = idx
        while end >= 0 and not lines[end].strip().endswith('*/'):
            end -= 1
        if end < 0:
            return ''
        start = end
        while start >= 0 and '/**' not in lines[start]:
            start -= 1
        if start < 0 or '/**' not in lines[start]:
            return ''
        javadoc_lines = lines[start:end + 1]
        cleaned = ' '.join(
            re.sub(r'^\s*\*+\s?', '', l).strip()
            for l in javadoc_lines
        )
        cleaned = re.sub(r'/\*+', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _extract_method_body(self, source: str, start_line: int) -> str:
        """Extract a method's full text starting from start_line by brace matching."""
        lines = source.split('\n')
        # Find opening brace
        body_chars = []
        brace_depth = 0
        started = False
        for line in lines[start_line - 1:]:
            for ch in line:
                body_chars.append(ch)
                if ch == '{':
                    brace_depth += 1
                    started = True
                elif ch == '}':
                    brace_depth -= 1
                    if started and brace_depth == 0:
                        return ''.join(body_chars)
            body_chars.append('\n')
        return ''.join(body_chars)

    def _extract_methods_javalang(self, source: str, rel_path: str
                                   ) -> List[Dict]:
        """Use javalang AST to extract methods with metadata."""
        records = []
        try:
            tree = javalang.parse.parse(source)
        except Exception:
            return self._extract_methods_regex(source, rel_path)

        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            if not hasattr(node, 'position') or node.position is None:
                continue
            start_line = node.position.line
            func_name = node.name

            docstring = self._extract_javadoc(source, start_line)
            method_src = self._extract_method_body(source, start_line)

            # Rebuild signature from the line
            sig_line = source.split('\n')[start_line - 1] if start_line <= source.count('\n') + 1 else ''

            records.append({
                'func_name': func_name,
                'start_line': start_line,
                'docstring': docstring,
                'original_string': method_src,
                'code': method_src,
            })
        return records

    def _extract_methods_regex(self, source: str, rel_path: str) -> List[Dict]:
        """Fallback: regex-based method extraction."""
        records = []
        pattern = re.compile(
            r'(/\*\*.*?\*/\s*)?'
            r'(?:(?:public|private|protected|static|final|synchronized|abstract)\s+)+'
            r'(?:<[^>]*>\s+)?'
            r'[\w\[\]<>,\s]+\s+'
            r'(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{',
            re.DOTALL
        )
        for m in pattern.finditer(source):
            javadoc_raw = m.group(1) or ''
            func_name = m.group(2)
            start_line = source[:m.start()].count('\n') + 1
            docstring = re.sub(r'/\*+|\*+/', '', javadoc_raw)
            docstring = re.sub(r'^\s*\*\s?', '', docstring, flags=re.MULTILINE)
            docstring = re.sub(r'\s+', ' ', docstring).strip()
            # Extract body
            brace_depth = 0
            i = m.end() - 1  # points at '{'
            start_i = i
            while i < len(source):
                if source[i] == '{':
                    brace_depth += 1
                elif source[i] == '}':
                    brace_depth -= 1
                    if brace_depth == 0:
                        method_src = source[m.start():i + 1]
                        records.append({
                            'func_name': func_name,
                            'start_line': start_line,
                            'docstring': docstring,
                            'original_string': method_src,
                            'code': method_src,
                        })
                        break
                i += 1
        return records

    def generate(self) -> Dict:
        logger.info("Generating CodeSearchNet dataset (method-level)...")

        dataset = []
        dataset_dir = self.output_dir / f"codesearchnet_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        project_name = self.repo_path.name
        # Use GitHub-style repo identifier if possible
        repo_identifier = project_name

        java_files = self._get_java_files()
        logger.info(f"Found {len(java_files)} Java files")

        if not java_files:
            return {"error": "No Java files found"}

        # Determine split boundaries after counting methods (assign as we go, 80/10/10)
        method_idx = 0

        try:
            for file_path in java_files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        source = f.read()

                    if not source.strip():
                        continue

                    rel_path = str(file_path.relative_to(self.repo_path)).replace('\\', '/')

                    sha = self._get_file_sha(file_path)

                    extractor = (self._extract_methods_javalang
                                 if JAVALANG_AVAILABLE
                                 else self._extract_methods_regex)
                    methods = extractor(source, rel_path)

                    for mth in methods:
                        docstring = mth['docstring']
                        if not docstring:
                            # Skip methods with no documentation (CodeSearchNet only includes documented methods)
                            continue

                        code_tokens = re.findall(r'\w+|[^\w\s]', mth['code'])
                        docstring_tokens = docstring.split()

                        # Assign partition 80/10/10 based on running index
                        # (will be refined at end — assign based on final total)
                        dataset.append({
                            'repo': repo_identifier,
                            'path': rel_path,
                            'func_name': mth['func_name'],
                            'language': 'java',
                            'url': (f"https://github.com/{repo_identifier}/blob/{sha}/{rel_path}"
                                    f"#L{mth['start_line']}" if sha else ''),
                            'original_string': mth['original_string'],
                            'code': mth['code'],
                            'code_tokens': code_tokens[:512],
                            'docstring': docstring,
                            'docstring_tokens': docstring_tokens[:100],
                            'sha': sha,
                            'partition': '',   # filled below
                        })

                    if len(dataset) % 200 == 0 and dataset:
                        logger.info(f"Extracted {len(dataset)} methods so far...")

                except Exception as e:
                    logger.warning(f"Error processing {file_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}

        # Assign partition labels
        total = len(dataset)
        train_end = int(total * 0.8)
        valid_end = int(total * 0.9)
        for i, rec in enumerate(dataset):
            if i < train_end:
                rec['partition'] = 'train'
            elif i < valid_end:
                rec['partition'] = 'valid'
            else:
                rec['partition'] = 'test'

        logger.info(f"Extracted {total} documented methods from {len(java_files)} files")

        # Save JSONL (one method per line — CodeSearchNet standard format)
        jsonl_file = dataset_dir / "codesearchnet_java.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for rec in dataset:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')

        # Also save the legacy JSON for backward compat
        json_file = dataset_dir / "codesearchnet_dataset.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'CodeSearchNet_Java',
                'description': 'Method-level code+docstring pairs following CodeSearchNet schema',
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_methods': total,
                'schema': ['repo', 'path', 'func_name', 'language', 'url',
                           'original_string', 'code', 'code_tokens',
                           'docstring', 'docstring_tokens', 'sha', 'partition'],
                'extraction_method': 'method_level_ast_javadoc',
                'data': dataset,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"SUCCESS: CodeSearchNet dataset -> {dataset_dir}")

        return {
            "status": "success",
            "total_methods": total,
            "total_files": len(java_files),
            "output_dir": str(dataset_dir),
            "output_file": str(jsonl_file),
        }


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python codesearchnet_generator.py <repo_path> [file_limit]")
        sys.exit(1)

    repo_path = sys.argv[1]
    file_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    generator = CodeSearchNetGenerator(repo_path, file_limit=file_limit)
    result = generator.generate()

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Success! Generated {result['total_methods']} method entries from {result['total_files']} files")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
