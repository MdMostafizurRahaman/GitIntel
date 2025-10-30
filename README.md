# LLM-Powered Git Analysis Tool

## Overview
This tool uses Google Gemini LLM and PyDriller to analyze Java Git repositories using natural language commands. It generates automated Excel reports for package churn, LOC, complexity, and release analysis with support for Git cloning and commit limits.

## Features
- **Natural Language Commands**: Bengali/English commands for analysis
- **Git Repository Cloning**: Clone any GitHub repo for analysis
- **Commit Limit Control**: Analyze specific number of commits (performance optimization)
- **Progress Tracking**: Real-time progress indicators during analysis
- **Automated Analysis**: Package churn, LOC, complexity, release-wise changes
- **Excel Report Generation**: Results saved as `.xlsx` files
- **Fallback System**: Simple command parsing when LLM quota exceeded

## Installation
```pwsh
# Install dependencies
pip install -r requirements.txt

# Set up Gemini API key (create .env file)
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Usage

### Clone and Analyze Remote Repositories
```pwsh
python llm_cli.py "clone https://github.com/SeleniumHQ/selenium"
python llm_cli.py "clone https://github.com/apache/maven"
```

### Analysis with Commit Limits (Performance Optimization)
```pwsh
python llm_cli.py "package churn first 500 commits"
python llm_cli.py "loc per month first 1000 commits"
python llm_cli.py "complexity first 200 commits"
```

### Natural Language Commands
```pwsh
python llm_cli.py "আমাকে 500+ line changes এর Excel দাও"
python llm_cli.py "LOC analysis report দাও"
python llm_cli.py "complexity analysis করো"
python llm_cli.py "release wise changes দেখাও"
python llm_cli.py "loc per month according to package"
```

### Simple Commands (Works without LLM)
```pwsh
python llm_cli.py "loc per month first 100"
python llm_cli.py "package churn first 50"
python llm_cli.py "complexity"
python llm_cli.py "releases"
```

## Supported Repositories
- ✅ **Apache Kafka** (D:\GitIntel\kafka)
- ✅ **Apache Maven** (cloned from GitHub)
- ✅ **Selenium** (cloned from GitHub)
- ✅ **Spring Boot** (D:\GitIntel\Spring-Boot-in-Detailed-Way)
- ✅ **Any Java repository** (local or GitHub)

## Output Files
All reports are timestamped Excel files:
- `package_churn_analysis_20251030_124511.xlsx`
- `loc_time_ratio_analysis_20251030_124248.xlsx`
- `complexity_analysis_20251030_124722.xlsx`

## System Working Flow

### Architecture Overview
```
User Command → CLI Interface → LLM/Simple Parser → Analysis Engine → Excel Generator
     ↓              ↓              ↓                    ↓              ↓
  Natural Lang   llm_cli.py    Gemini AI/Regex    PyDriller       openpyxl
  (Bengali/Eng)              Processing          + pandas +     .xlsx files
```

### New Features in Detail

#### 1. **Git Repository Cloning**
```python
# Clone any GitHub repository
python llm_cli.py "clone https://github.com/apache/maven"

# Automatic repository detection and setup
✅ Repository cloned successfully!
✅ Repository set: D:\GitIntel\maven
```

#### 2. **Commit Limit Control**
```python
# Process only first N commits for faster analysis
python llm_cli.py "loc analysis first 500 commits"

# Progress tracking
📊 Processing commits (limit: 500, total: 16511)...
   📈 Processed 100 commits...
   📈 Processed 200 commits...
   ⏹️ Reached commit limit of 500
```

#### 3. **Enhanced Progress Tracking**
- Real-time commit processing count
- Time estimates for large repositories
- Memory usage optimization for big datasets

#### 4. **Fallback Command System**
When LLM quota is exceeded, simple regex-based parsing:
```python
# These work without LLM
"loc per month first 100"  → analyze_loc_time_ratio(limit=100)
"package churn first 50"   → analyze_package_churn(limit=50)  
"complexity"               → analyze_complexity()
```

### Performance Optimizations
- **Commit Limits**: Process 100-1000 commits instead of full history
- **Progress Indicators**: Show processing status every 50-100 commits
- **Memory Management**: Stream processing for large repositories
- **Selective Analysis**: Focus on Java files only

## Advanced Usage

### Repository Management
```pwsh
# Set specific repository
python llm_cli.py "set_repo D:/GitIntel/kafka"

# Clone and switch
python llm_cli.py "clone https://github.com/spring-projects/spring-boot"
```

### Custom Analysis Parameters
```pwsh
# Custom threshold for package churn
python llm_cli.py "package changes over 1000 lines"

# Time-based analysis
python llm_cli.py "loc per month according to package"
python llm_cli.py "complexity time ratio first 200"
```

## Error Handling
- **LLM Quota Exceeded**: Automatic fallback to simple command parsing
- **Network Issues**: Local repository analysis continues
- **Large Repositories**: Commit limit prevents memory issues
- **Invalid Repositories**: Clear error messages and suggestions

## Requirements
- Python 3.13+
- Google Gemini API key in `.env` as `GEMINI_API_KEY`
- Git installed (for cloning repositories)
- ~2GB RAM for large repository analysis

## License
MIT
