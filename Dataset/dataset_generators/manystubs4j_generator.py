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

# 16 ManySStuBs4J bug type categories
BUG_TYPES = [
    'CHANGE_OPERATOR',
    'CHANGE_OPERAND',
    'CHANGE_NUMERAL',
    'CHANGE_BOOLEAN_LITERAL',
    'WRONG_FUNCTION_NAME',
    'CHANGE_MODIFIER',
    'ADD_THROWS_EXCEPTION',
    'DELETE_THROWS_EXCEPTION',
    'CHANGE_EXCEPTION',
    'MORE_SPECIFIC_IF',
    'LESS_SPECIFIC_IF',
    'MORE_SPECIFIC_RETURN_TYPE',
    'CHANGE_STRING_LITERAL',
    'CHANGE_RETURN_VALUE',
    'CHANGE_OBJECT',
    'CHANGE_CALLER_EXPRESSION',
]

OPERATORS = frozenset([
    '==', '!=', '>=', '<=', '>', '<',
    '&&', '||', '!',
    '+', '-', '*', '/', '%',
    '+=', '-=', '*=', '/=', '%=',
    '&', '|', '^', '~', '<<', '>>', '>>>',
])

MODIFIERS = frozenset(['public', 'private', 'protected', 'static', 'final',
                       'abstract', 'synchronized', 'volatile', 'transient'])


def _tokenize(line: str) -> List[str]:
    """Split a source line into tokens."""
    return re.findall(r'[a-zA-Z_]\w*|[0-9]+(?:\.[0-9]*)?[fFdDlL]?|"[^"]*"|'
                      r'\'[^\']*\'|[!=<>]=|&&|\|\||[+\-*/&|^!~<>%]=?|[{}()\[\];:,.]', line)


def _classify_bug_type(before: str, after: str) -> str:
    """Classify single-line change into one of the 16 ManySStuBs4J bug types."""
    b_tokens = _tokenize(before.strip())
    a_tokens = _tokenize(after.strip())

    # Boolean literal flip
    before_lower = before.strip().lower()
    after_lower = after.strip().lower()
    if (re.search(r'\btrue\b', before_lower) and re.search(r'\bfalse\b', after_lower)) or \
       (re.search(r'\bfalse\b', before_lower) and re.search(r'\btrue\b', after_lower)):
        return 'CHANGE_BOOLEAN_LITERAL'

    # String literal change
    b_strings = re.findall(r'"[^"]*"', before)
    a_strings = re.findall(r'"[^"]*"', after)
    if b_strings and a_strings and b_strings != a_strings and len(b_strings) == len(a_strings):
        return 'CHANGE_STRING_LITERAL'

    # Numeric literal change
    b_nums = re.findall(r'\b\d+(?:\.\d+)?[fFdDlL]?\b', before)
    a_nums = re.findall(r'\b\d+(?:\.\d+)?[fFdDlL]?\b', after)
    if b_nums and a_nums and b_nums != a_nums and len(b_nums) <= len(a_nums) + 1:
        return 'CHANGE_NUMERAL'

    # Throws clause changes
    if re.search(r'\bthrows\b', after) and not re.search(r'\bthrows\b', before):
        return 'ADD_THROWS_EXCEPTION'
    if re.search(r'\bthrows\b', before) and not re.search(r'\bthrows\b', after):
        return 'DELETE_THROWS_EXCEPTION'

    # Modifier changes
    b_mods = set(t for t in b_tokens if t in MODIFIERS)
    a_mods = set(t for t in a_tokens if t in MODIFIERS)
    if b_mods != a_mods:
        return 'CHANGE_MODIFIER'

    # Operator changes – look for tokens that are only in operators set
    b_ops = [t for t in b_tokens if t in OPERATORS]
    a_ops = [t for t in a_tokens if t in OPERATORS]
    if b_ops != a_ops:
        # Distinguish if/condition changes
        if re.search(r'\bif\s*\(', before) or re.search(r'\bif\s*\(', after):
            # More vs less specific if
            if len(a_ops) > len(b_ops):
                return 'MORE_SPECIFIC_IF'
            else:
                return 'LESS_SPECIFIC_IF'
        return 'CHANGE_OPERATOR'

    # Method name change: same structure but a method name differs
    b_calls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', before)
    a_calls = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', after)
    if b_calls and a_calls and b_calls != a_calls:
        if len(b_calls) == len(a_calls):
            return 'WRONG_FUNCTION_NAME'
        return 'CHANGE_CALLER_EXPRESSION'

    # Return statement change
    if re.match(r'\s*return\b', before) and re.match(r'\s*return\b', after):
        return 'CHANGE_RETURN_VALUE'

    # Return type change on method signature
    if re.search(r'(?:public|private|protected)\s+\w+\s+\w+\s*\(', before) and \
       re.search(r'(?:public|private|protected)\s+\w+\s+\w+\s*\(', after):
        b_type = re.search(r'(?:public|private|protected)\s+(\w+)\s+', before)
        a_type = re.search(r'(?:public|private|protected)\s+(\w+)\s+', after)
        if b_type and a_type and b_type.group(1) != a_type.group(1):
            return 'MORE_SPECIFIC_RETURN_TYPE'

    # Object/type name change
    b_types = re.findall(r'\b[A-Z]\w*\b', before)
    a_types = re.findall(r'\b[A-Z]\w*\b', after)
    if b_types and a_types and set(b_types) != set(a_types):
        return 'CHANGE_OBJECT'

    # Operand (variable) change
    b_ids = [t for t in b_tokens if re.match(r'[a-z_]\w+', t) and t not in MODIFIERS]
    a_ids = [t for t in a_tokens if re.match(r'[a-z_]\w+', t) and t not in MODIFIERS]
    if b_ids != a_ids and len(b_ids) == len(a_ids):
        return 'CHANGE_OPERAND'

    return 'CHANGE_OPERAND'  # default fallback


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

            limit = self.commit_limit or len(commits)

            for idx, commit_line in enumerate(commits[:limit]):
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
                    # Build the patch snippet for this single hunk
                    patch_snippet = (f"-{stub['sourceBeforeFix']}\n"
                                     f"+{stub['sourceAfterFix']}")
                    dataset.append({
                        'bugType': stub['bugType'],
                        'commitSHA1': commit_hash,
                        'fixCommitParentSHA1': parent_hash,
                        'commitFile': stub['commitFile'],
                        'patch': patch_snippet,
                        'projectName': project_name,
                        'bugLineNum': stub['bugLineNum'],
                        'fixLineNum': stub['fixLineNum'],
                        'sourceBeforeFix': stub['sourceBeforeFix'],
                        'sourceAfterFix': stub['sourceAfterFix'],
                    })

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
                'schema': ['bugType', 'commitSHA1', 'fixCommitParentSHA1',
                           'commitFile', 'patch', 'projectName',
                           'bugLineNum', 'fixLineNum',
                           'sourceBeforeFix', 'sourceAfterFix'],
                'bug_types': BUG_TYPES,
                'issues': dataset,
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"ManySStuBs4J dataset -> {dataset_dir}")
        logger.info(f"Bug type distribution: {type_counts}")

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
