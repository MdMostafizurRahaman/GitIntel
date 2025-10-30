# LLM-Powered Git Analysis Tool

## Overview
This tool uses Google Gemini LLM and PyDriller to analyze Java Git repositories using natural language commands. It generates automated Excel reports for package churn, LOC, complexity, and release analysis.

## Features
- **Natural Language Commands**: Bengali/English commands for analysis (e.g., "আমাকে 500+ line changes এর Excel দাও")
- **Automated Analysis**: Package churn, LOC, complexity, release-wise changes
- **Excel Report Generation**: Results saved as `.xlsx` files
- **Fallback System**: Default analysis if LLM is unavailable

## Installation
```pwsh
pip install -r requirements.txt
```

## Usage
Run analysis with natural language commands:
```pwsh
python llm_cli.py "আমাকে 500+ line changes এর Excel দাও"
python llm_cli.py "LOC analysis report দাও"
python llm_cli.py "complexity analysis করো"
python llm_cli.py "release wise changes দেখাও"
```

## Output
- Excel files (e.g., `package_churn_analysis_20251030_012642.xlsx`) are generated in the workspace.

## System Working Flow

### Architecture Overview
```
User Command → CLI Interface → LLM Processor → Analysis Engine → Excel Generator
     ↓              ↓              ↓              ↓              ↓
  Natural Lang   llm_cli.py    Gemini AI    PyDriller       openpyxl
  (Bengali/Eng)              Processing    + pandas +     .xlsx files
```

### Detailed Process Flow

#### 1. **Command Input & Repository Detection**
- User runs: `python llm_cli.py "আমাকে 500+ line changes এর Excel দাও"`
- CLI auto-detects Git repository in workspace (`D:\GitIntel\kafka`)
- Validates repository structure and Java files

#### 2. **LLM Command Processing**
- **LLMGitAnalyzer** class initializes with Gemini API
- Tries multiple Gemini models: `gemini-pro`, `gemini-1.5-pro`, `gemini-1.0-pro`
- If LLM available: Parses natural language to structured analysis plan
- If LLM unavailable: Falls back to default package churn analysis

#### 3. **Analysis Execution**
- **PyDriller Engine**: Mines Git commits, detects Java packages
- **Analysis Types**:
  - `package_churn`: Tracks packages with >500 line changes
  - `loc_analysis`: Lines of code metrics per package
  - `complexity_analysis`: Cyclomatic complexity using radon
  - `release_analysis`: Changes grouped by releases/tags

#### 4. **Data Processing**
- **pandas**: Aggregates and processes commit data
- **Custom Logic**: Calculates churn metrics, LOC deltas
- **Filtering**: Applies thresholds (e.g., 500+ line changes)

#### 5. **Excel Report Generation**
- **openpyxl**: Creates formatted Excel workbook
- **Sheets**: Summary, Detailed Analysis, Charts
- **Naming**: `package_churn_analysis_YYYYMMDD_HHMMSS.xlsx`

#### 6. **Error Handling & Fallback**
- LLM failures → Default analysis
- API errors → Graceful degradation
- Large repos → Progress indicators

### Data Flow Example
```
Git Commits (16k+) → PyDriller → Package Detection → Churn Calculation → Excel Export
     ↓                    ↓              ↓                    ↓              ↓
  Raw Changes        Modified Files   Java Packages       Metrics         .xlsx
```

### Key Components
- **`llm_cli.py`**: Command-line interface with auto-detection
- **`llm_git_analyzer.py`**: Main LLM-powered analysis engine
- **`requirements.txt`**: Python dependencies (PyDriller, pandas, openpyxl, etc.)
- **`.env`**: Gemini API key configuration

## Workflow

## Example Commands
- "500+ line changes দাও"
- "LOC report বানাও"
- "complexity analysis করো"
- "release wise changes দেখাও"

## Requirements
- Python 3.13+
- Google Gemini API key in `.env` as `GEMINI_API_KEY`

## License
MIT
