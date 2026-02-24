import os
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 16 ManySStuBs4J bug type categories — exact enum values from original dataset
BUG_TYPES = [
    'CHANGE_IDENTIFIER',
    'CHANGE_NUMERAL',
    'SWAP_BOOLEAN_LITERAL',
    'CHANGE_MODIFIER',
    'DIFFERENT_METHOD_SAME_ARGS',
    'OVERLOAD_METHOD_MORE_ARGS',
    'OVERLOAD_METHOD_DELETED_ARGS',
    'CHANGE_CALLER_IN_FUNCTION_CALL',
    'SWAP_ARGUMENTS',
    'CHANGE_OPERATOR',
    'CHANGE_UNARY_OPERATOR',
    'CHANGE_OPERAND',
    'LESS_SPECIFIC_IF',
    'MORE_SPECIFIC_IF',
    'ADD_THROWS_EXCEPTION',
    'DELETE_THROWS_EXCEPTION',
]

OPERATORS = frozenset([
    '==', '!=', '>=', '<=', '>', '<',
    '&&', '||',
    '+', '-', '*', '/', '%',
    '+=', '-=', '*=', '/=', '%=',
    '&', '|', '^', '~', '<<', '>>', '>>>',
])

MODIFIERS = frozenset(['public', 'private', 'protected', 'static', 'final',
                       'abstract', 'synchronized', 'volatile', 'transient'])

UNARY_OPERATORS = frozenset(['++', '--', '!', '~', '-', '+'])


def _tokenize(line: str) -> List[str]:
    """Split a source line into tokens."""
    return re.findall(r'[a-zA-Z_]\w*|[0-9]+(?:\.[0-9]*)?[fFdDlL]?|"[^"]*"|'
                      r'\'[^\']*\'|[!=<>]=|&&|\|\||[+\-*/&|^!~<>%]=?|[{}()\[\];:,.]', line)


def _get_call_args(line: str, method: str) -> List[str]:
    """Extract argument list tokens for a given method call."""
    m = re.search(re.escape(method) + r'\s*\(([^)]*)\)', line)
    if m:
        return [a.strip() for a in m.group(1).split(',') if a.strip()]
    return []


def _classify_bug_type(before: str, after: str) -> str:
    """Classify single-line change into one of the 16 ManySStuBs4J bug types
    using the exact original enum values."""
    b_tokens = _tokenize(before.strip())
    a_tokens = _tokenize(after.strip())
    before_s = before.strip()
    after_s  = after.strip()

    # ── SWAP_BOOLEAN_LITERAL ─────────────────────────────────────────────────
    if (re.search(r'\btrue\b', before_s, re.I) and re.search(r'\bfalse\b', after_s, re.I)) or \
       (re.search(r'\bfalse\b', before_s, re.I) and re.search(r'\btrue\b', after_s, re.I)):
        return 'SWAP_BOOLEAN_LITERAL'

    # ── CHANGE_NUMERAL ───────────────────────────────────────────────────────
    b_nums = re.findall(r'\b\d+(?:\.\d+)?[fFdDlL]?\b', before_s)
    a_nums = re.findall(r'\b\d+(?:\.\d+)?[fFdDlL]?\b', after_s)
    if b_nums != a_nums and len(b_nums) == len(a_nums) and b_nums and a_nums:
        return 'CHANGE_NUMERAL'

    # ── THROWS ───────────────────────────────────────────────────────────────
    if re.search(r'\bthrows\b', after_s) and not re.search(r'\bthrows\b', before_s):
        return 'ADD_THROWS_EXCEPTION'
    if re.search(r'\bthrows\b', before_s) and not re.search(r'\bthrows\b', after_s):
        return 'DELETE_THROWS_EXCEPTION'

    # ── CHANGE_MODIFIER ──────────────────────────────────────────────────────
    b_mods = set(t for t in b_tokens if t in MODIFIERS)
    a_mods = set(t for t in a_tokens if t in MODIFIERS)
    if b_mods != a_mods:
        return 'CHANGE_MODIFIER'

    # ── UNARY vs BINARY OPERATOR ─────────────────────────────────────────────
    b_unary = re.findall(r'(?<![=<>!&|+\-*/])[+\-]{2}|(?<!\w)!(?!=)', before_s)
    a_unary = re.findall(r'(?<![=<>!&|+\-*/])[+\-]{2}|(?<!\w)!(?!=)', after_s)
    b_ops = [t for t in b_tokens if t in OPERATORS]
    a_ops = [t for t in a_tokens if t in OPERATORS]

    if before_s.startswith('if') or after_s.startswith('if') or \
       re.search(r'\bif\s*\(', before_s) or re.search(r'\bif\s*\(', after_s):
        if b_ops != a_ops or b_unary != a_unary:
            if len(a_ops) + len(a_unary) > len(b_ops) + len(b_unary):
                return 'MORE_SPECIFIC_IF'
            else:
                return 'LESS_SPECIFIC_IF'

    if b_unary != a_unary and b_ops == a_ops:
        return 'CHANGE_UNARY_OPERATOR'
    if b_ops != a_ops:
        return 'CHANGE_OPERATOR'

    # ── METHOD CALL ANALYSIS ─────────────────────────────────────────────────
    b_calls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', before_s)
    a_calls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', after_s)

    if b_calls and a_calls:
        # Same method name, different argument counts
        if b_calls[0] == a_calls[0]:
            b_args = _get_call_args(before_s, b_calls[0])
            a_args = _get_call_args(after_s, a_calls[0])
            if len(b_args) != len(a_args):
                return ('OVERLOAD_METHOD_MORE_ARGS' if len(a_args) > len(b_args)
                        else 'OVERLOAD_METHOD_DELETED_ARGS')
            # Same arg count but different order → SWAP_ARGUMENTS
            if sorted(b_args) == sorted(a_args) and b_args != a_args:
                return 'SWAP_ARGUMENTS'
            # Same method, same args but caller changed
            if b_calls != a_calls and len(b_calls) == len(a_calls):
                b_callers = re.findall(r'(\w+)\.' + re.escape(b_calls[0]) + r'\s*\(', before_s)
                a_callers = re.findall(r'(\w+)\.' + re.escape(a_calls[0]) + r'\s*\(', after_s)
                if b_callers != a_callers:
                    return 'CHANGE_CALLER_IN_FUNCTION_CALL'
        # Different method name, same arg count → DIFFERENT_METHOD_SAME_ARGS
        elif len(b_calls) == len(a_calls):
            b_args = _get_call_args(before_s, b_calls[0])
            a_args = _get_call_args(after_s, a_calls[0])
            if len(b_args) == len(a_args):
                return 'DIFFERENT_METHOD_SAME_ARGS'
            return 'CHANGE_CALLER_IN_FUNCTION_CALL'

    # ── CHANGE_OPERAND (variable name changed, same structure) ───────────────
    b_ids = [t for t in b_tokens if re.match(r'[a-z_]\w+', t) and t not in MODIFIERS]
    a_ids = [t for t in a_tokens if re.match(r'[a-z_]\w+', t) and t not in MODIFIERS]
    if b_ids != a_ids and len(b_ids) == len(a_ids):
        return 'CHANGE_OPERAND'

    # ── CHANGE_IDENTIFIER (type name, field, or non-method identifier changed) ─
    b_caps = re.findall(r'\b[A-Z]\w*\b', before_s)
    a_caps = re.findall(r'\b[A-Z]\w*\b', after_s)
    if set(b_caps) != set(a_caps):
        return 'CHANGE_IDENTIFIER'

    # ── default fallback ──────────────────────────────────────────────────────
    return 'CHANGE_OPERAND'


def _parse_hunk_header(line: str) -> Tuple[int, int]:
    """Return (old_start, new_start) line numbers from a @@ hunk header."""
    m = re.search(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def _parse_single_line_hunks(diff_text: str, file_path: str) -> List[Dict]:
    """
    Parse a unified diff and extract hunks where exactly one line was
    removed and one line was added (the minimal single-statement stub).
    Returns list of dicts with before/after/line numbers.
    """
    results = []
    current_file = None
    lines = diff_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith('+++ b/'):
            current_file = line[6:].strip()
            i += 1
            continue

        if line.startswith('@@') and current_file:
            old_start, new_start = _parse_hunk_header(line)
            # Collect hunk lines
            hunk_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('@@') and \
                  not lines[i].startswith('diff '):
                hunk_lines.append(lines[i])
                i += 1

            # Analyse hunk – only accept single-deletion/single-addition hunks
            deletions = [(j, l) for j, l in enumerate(hunk_lines) if l.startswith('-')]
            additions = [(j, l) for j, l in enumerate(hunk_lines) if l.startswith('+')]

            if len(deletions) == 1 and len(additions) == 1:
                src_before = deletions[0][1][1:]   # strip leading '-'
                src_after = additions[0][1][1:]     # strip leading '+'
                # Skip empty or whitespace-only changes
                if src_before.strip() and src_after.strip() and \
                   src_before.strip() != src_after.strip():
                    bug_type = _classify_bug_type(src_before, src_after)
                    # Line number = old_start + offset of deletion within context
                    del_offset = sum(1 for j, l in enumerate(hunk_lines[:deletions[0][0]])
                                     if not l.startswith('+'))
                    add_offset = sum(1 for j, l in enumerate(hunk_lines[:additions[0][0]])
                                     if not l.startswith('-'))
                    results.append({
                        'bugType': bug_type,
                        'commitFile': current_file,
                        'bugLineNum': old_start + del_offset,
                        'fixLineNum': new_start + add_offset,
                        'sourceBeforeFix': src_before,
                        'sourceAfterFix': src_after,
                    })
            continue  # already advanced i inside hunk loop

        i += 1

    return results


class ManySStuBs4JGenerator:

    def __init__(self, repo_path: str, output_dir: str = None, commit_limit: int = None):
        self.repo_path = Path(repo_path)
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / "major_dataset"
        self.commit_limit = commit_limit
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a Git repository: {repo_path}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ManySStuBs4J generator for {self.repo_path}")

    def generate(self) -> Dict:
        """Generate ManySStuBs4J dataset with proper schema including bugType detection."""
        logger.info("Generating ManySStuBs4J dataset (single-statement bug stubs)...")

        dataset = []
        dataset_dir = self.output_dir / f"manystubs4j_dataset_{self.timestamp}"
        dataset_dir.mkdir(exist_ok=True)

        project_name = self.repo_path.name

        try:
            result = subprocess.run(
                ['git', 'log', '--all', '--format=%H|%P|%s', '--no-merges'],
                cwd=self.repo_path,
                capture_output=True, text=True,
                encoding='utf-8', errors='ignore', timeout=60
            )

            if result.returncode != 0:
                return {"error": "Git log failed"}

            commits = [c for c in result.stdout.strip().split('\n') if c and '|' in c]
            logger.info(f"Found {len(commits)} commits to analyse")

            if not commits:
                return {"error": "No commits found"}

            # Process commits until we find self.commit_limit stubs (not limited by commits)
            for idx, commit_line in enumerate(commits):
                # Stop only when we've found enough stubs
                if self.commit_limit and len(dataset) >= self.commit_limit:
                    break
                
                parts = commit_line.split('|', 2)
                if len(parts) < 2:
                    continue

                commit_hash = parts[0].strip()
                parent_hash = parts[1].strip().split()[0] if parts[1].strip() else ''
                commit_msg = parts[2].strip() if len(parts) > 2 else ''

                if not parent_hash:
                    continue

                # Get the diff for Java files only
                diff_result = subprocess.run(
                    ['git', 'diff', parent_hash, commit_hash, '--unified=3',
                     '--diff-filter=M', '--', '*.java'],
                    cwd=self.repo_path,
                    capture_output=True, text=True,
                    encoding='utf-8', errors='ignore', timeout=30
                )

                if diff_result.returncode != 0 or not diff_result.stdout.strip():
                    continue

                diff_text = diff_result.stdout
                stubs = _parse_single_line_hunks(diff_text, '')

                for stub in stubs:
                    src_before = stub['sourceBeforeFix']
                    src_after = stub['sourceAfterFix']
                    # Build per-file patch snippet (unified diff lines for this hunk)
                    patch_snippet = (f"-{src_before}\n+{src_after}")
                    dataset.append({
                        'bugType':              stub['bugType'],
                        'fixCommitSHA1':        commit_hash,
                        'fixCommitParentSHA1':  parent_hash,
                        'bugFilePath':          stub['commitFile'],
                        'fixPatch':             patch_snippet,
                        'projectName':          project_name,
                        'bugLineNum':           stub['bugLineNum'],
                        'bugNodeStartChar':     0,
                        'bugNodeLength':        len(src_before.strip()),
                        'fixLineNum':           stub['fixLineNum'],
                        'fixNodeStartChar':     0,
                        'fixNodeLength':        len(src_after.strip()),
                        'sourceBeforeFix':      src_before,
                        'sourceAfterFix':       src_after,
                    })
                    
                    # Stop if we've found enough stubs
                    if self.commit_limit and len(dataset) >= self.commit_limit:
                        break

                if (idx + 1) % 50 == 0:
                    logger.info(f"Processed {idx + 1} commits, found {len(dataset)} stubs...")

            logger.info(f"Extracted {len(dataset)} single-statement bug stubs")

        except subprocess.TimeoutExpired:
            return {"error": "Git command timeout"}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"error": str(e)}

        if not dataset:
            return {"error": "No single-statement bug stubs found"}

        # Bug type distribution stats
        type_counts: Dict[str, int] = {}
        for rec in dataset:
            type_counts[rec['bugType']] = type_counts.get(rec['bugType'], 0) + 1

        output_file = dataset_dir / "manystubs4j_dataset.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_type': 'ManySStuBs4J',
                'description': (
                    'Single-statement bug stubs following ManySStuBs4J schema '
                    '(Karampatsis et al., MSR 2020)'
                ),
                'repository': str(self.repo_path),
                'generated_at': datetime.now().isoformat(),
                'total_stubs': len(dataset),
                'bug_type_distribution': type_counts,
                'schema': ['bugType', 'fixCommitSHA1', 'fixCommitParentSHA1',
                           'bugFilePath', 'fixPatch', 'projectName',
                           'bugLineNum', 'bugNodeStartChar', 'bugNodeLength',
                           'fixLineNum', 'fixNodeStartChar', 'fixNodeLength',
                           'sourceBeforeFix', 'sourceAfterFix'],
                'bug_types': BUG_TYPES,
                'issues': dataset,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"ManySStuBs4J dataset -> {dataset_dir}")
        logger.info(f"Bug type distribution: {type_counts}")

        # Generate README
        readme = dataset_dir / "README.md"
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(f"""# ManySStuBs4J Dataset

## Overview
This dataset follows the **ManySStuBs4J** standard from https://github.com/maldil/ManySStuBs4J

ManySStuBs4J contains {len(dataset)} single-statement bug stubs extracted from GitHub commits.

### Structure:
```
manystubs4j_dataset_{self.timestamp}/
├── manystubs4j_dataset.json   # Main dataset with all stubs
└── README.md                  # This file
```

### JSON Format:
```json
{{
  "dataset_type": "ManySStuBs4J",
  "total_stubs": {len(dataset)},
  "bug_type_distribution": {type_counts},
  "issues": [
    {{
      "bugType": "CHANGE_OPERATOR",
      "fixCommitSHA1": "abc123...",
      "fixCommitParentSHA1": "def456...",
      "bugFilePath": "src/Main.java",
      "fixPatch": "-originalCode\\n+fixedCode",
      "projectName": "owner.repo",
      "bugLineNum": 42,
      "bugNodeStartChar": 0,
      "bugNodeLength": 25,
      "fixLineNum": 42,
      "fixNodeStartChar": 0,
      "fixNodeLength": 25,
      "sourceBeforeFix": "int x = a * b;",
      "sourceAfterFix": "int x = a + b;"
    }},
    ...
  ]
}}
```

### Bug Types (16 categories — exact original enum values):
```
1.  CHANGE_IDENTIFIER          - Changed variable/field/type identifier
2.  CHANGE_NUMERAL             - Changed numeric literal
3.  SWAP_BOOLEAN_LITERAL       - Flipped boolean (true <-> false)
4.  CHANGE_MODIFIER            - Changed access modifier
5.  DIFFERENT_METHOD_SAME_ARGS - Called different method with same args
6.  OVERLOAD_METHOD_MORE_ARGS  - Same method called with more arguments
7.  OVERLOAD_METHOD_DELETED_ARGS - Same method called with fewer arguments
8.  CHANGE_CALLER_IN_FUNCTION_CALL - Same method but different caller object
9.  SWAP_ARGUMENTS             - Same method but arguments swapped
10. CHANGE_OPERATOR            - Changed binary operator
11. CHANGE_UNARY_OPERATOR      - Changed unary operator (++/--)
12. CHANGE_OPERAND             - Changed operand/variable
13. LESS_SPECIFIC_IF           - Less specific if condition
14. MORE_SPECIFIC_IF           - More specific if condition
15. ADD_THROWS_EXCEPTION       - Added throws clause
16. DELETE_THROWS_EXCEPTION    - Removed throws clause
```

### Statistics
- **Total stubs**: {len(dataset)}
- **Bug type distribution**:
  {chr(10).join([f'  - {k}: {v}' for k, v in sorted(type_counts.items())])}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Use Cases
- Bug/defect prediction
- Code repair learning
- Program synthesis from buggy code
- Clone detection training

## References
- GitHub: https://github.com/maldil/ManySStuBs4J
- Paper: "Detecting Code Clones with Recurrent Neural Networks and Tree-Based Convolution" (MSR 2020)
- Original data: GitHub commits with single-line changes
""")

        logger.info(f"Generated README at {readme}")

        return {
            "status": "success",
            "total_method_changes": len(dataset),
            "bug_type_distribution": type_counts,
            "output_dir": str(dataset_dir),
            "output_file": str(output_file),
        }


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python manystubs4j_generator.py <repo_path> [commit_limit]")
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_limit = int(sys.argv[2]) if len(sys.argv) > 2 else None

    generator = ManySStuBs4JGenerator(repo_path, commit_limit=commit_limit)
    result = generator.generate()

    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    else:
        print(f"Success! Generated {result['total_method_changes']} single-statement stubs")
        print(f"Output: {result['output_dir']}")


if __name__ == "__main__":
    main()
