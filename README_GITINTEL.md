# 🚀 GitIntel: Unified Repository Intelligence Platform

**Traditional Analytics + AI-Powered Insights in One CLI**

GitIntel combines the power of traditional Git repository analysis with cutting-edge AI-powered question-answering capabilities, supporting both English and Bengali languages.

## 🎯 What is GitIntel?

GitIntel is a comprehensive repository analysis platform that brings together two powerful approaches:

1. **Traditional Analytics**: Detailed statistical analysis of commits, contributors, code metrics, and trends
2. **RepoChat Intelligence**: AI-powered question-answering using knowledge graphs and LLMs

## ✨ Key Features

### 🔍 Traditional Analytics
- **Contributor Analysis**: Detailed statistics on developers, commit patterns, and productivity
- **Code Metrics**: Lines of code, complexity analysis, file statistics
- **Temporal Analysis**: Activity patterns, growth trends, development velocity
- **Package Analysis**: Dependency tracking, churn analysis, package metrics
- **Excel Reports**: Professional Excel output with charts and visualizations

### 🤖 AI-Powered Intelligence (RepoChat)
- **Natural Language Q&A**: Ask questions about your repository in plain English or Bengali
- **Knowledge Graph**: Comprehensive repository knowledge extraction and storage
- **Smart Insights**: AI-generated insights about code quality, contributors, and patterns
- **Interactive Sessions**: Chat-like interface for exploring your repository

### 🌐 Language Support
- **English**: Full support for English queries and responses
- **Bengali (বাংলা)**: Native Bengali language support for questions and answers
- **Multilingual**: Easy to extend for additional languages

## 🚀 Quick Start

### 1. Setup
```bash
# Install GitIntel
python setup_gitintel.py

# Configure (add your API keys)
cp .env.template .env
# Edit .env with your Gemini API key
```

### 2. Basic Usage
```bash
# Full analysis of current directory
python gitintel.py --repo . --full-report

# Interactive Q&A session
python gitintel.py --repo . --interactive

# Quick insights
python gitintel.py --repo ./your-project --insights
```

### 3. Ask Questions
```bash
# English questions
python gitintel.py --ask "Who are the top contributors?"
python gitintel.py --ask "Which files have the highest complexity?"

# Bengali questions (বাংলা)
python gitintel.py --ask "কারা এই প্রজেক্টের প্রধান কন্ট্রিবিউটর?"
python gitintel.py --ask "কোন ফাইলগুলো সবচেয়ে জটিল?"
```

## 📋 Requirements

### Core Dependencies
- Python 3.8+
- pydriller (Git analysis)
- google-generativeai (LLM capabilities)
- xlsxwriter (Excel reports)
- pandas, numpy (Data processing)

### Optional Dependencies
- neo4j (Knowledge graph database)
- matplotlib, seaborn (Visualizations)
- plotly (Interactive charts)

## 🛠️ Installation

### Automatic Setup
```bash
python setup_gitintel.py
```

### Manual Setup
```bash
# Install dependencies
pip install pydriller google-generativeai xlsxwriter pandas numpy neo4j

# Setup environment
cp .env.template .env
# Add your Gemini API key to .env
```

## 💻 Command Line Interface

### Basic Commands
```bash
# Analyze repository
python gitintel.py --repo /path/to/repo

# Traditional analysis only
python gitintel.py --repo /path/to/repo --analyze traditional

# RepoChat only
python gitintel.py --repo /path/to/repo --analyze repochat

# Interactive mode
python gitintel.py --repo /path/to/repo --interactive
```

### Advanced Options
```bash
# Custom date range
python gitintel.py --repo /path/to/repo --since 2023-01-01 --until 2023-12-31

# Specific output format
python gitintel.py --repo /path/to/repo --output json

# Verbose logging
python gitintel.py --repo /path/to/repo --verbose

# Skip Excel generation
python gitintel.py --repo /path/to/repo --no-excel
```

## 🎭 Interactive Mode

Start an interactive session to explore your repository:

```bash
python gitintel.py --repo . --interactive
```

Example session:
```
🤖 GitIntel Interactive Session
Type 'help' for commands, 'quit' to exit

> Who committed the most lines?
🤖 Based on the analysis, John Doe is the top contributor with 15,420 lines added across 342 commits...

> কোন ফাইলটি সবচেয়ে বেশি পরিবর্তিত হয়েছে?
🤖 src/main/java/com/example/Service.java ফাইলটি সবচেয়ে বেশি পরিবর্তিত হয়েছে...

> insights
🤖 Here are key insights about your repository:
• High development velocity in the last quarter
• Core functionality concentrated in 5 key files...
```

## 📊 Output Formats

### Excel Reports
- **Summary Dashboard**: Overview metrics and charts
- **Contributors**: Detailed contributor analysis
- **Files**: File-level statistics and complexity
- **Temporal**: Time-based analysis and trends
- **Packages**: Dependency and package analysis

### JSON Output
```json
{
  "repository": {
    "name": "project-name",
    "total_commits": 1250,
    "contributors": 15,
    "files_analyzed": 342
  },
  "insights": [
    "High activity in Q4 2023",
    "Main development focused on core module"
  ]
}
```

## 🧠 Knowledge Graph

GitIntel builds a comprehensive knowledge graph of your repository:

### Node Types
- **Files**: Source files with metadata
- **Commits**: Commit information and relationships
- **Authors**: Developer profiles and statistics
- **Functions/Classes**: Code structure elements
- **Dependencies**: Package and import relationships

### Queries Supported
- Contributor patterns and expertise
- File relationships and dependencies  
- Code complexity and quality metrics
- Development timeline and patterns
- Testing coverage and quality

## 🌍 Bengali Language Support

GitIntel provides full Bengali language support:

### Sample Bengali Questions
```bash
# Contributors
python gitintel.py --ask "কারা এই প্রজেক্টের প্রধান ডেভেলপার?"

# Code quality
python gitintel.py --ask "কোন ফাইলগুলোর মান উন্নত করা প্রয়োজন?"

# Activity
python gitintel.py --ask "গত মাসে কী কী পরিবর্তন হয়েছে?"

# Testing
python gitintel.py --ask "টেস্ট কভারেজ কেমন আছে?"
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Google Gemini API Key (required for LLM features)
GEMINI_API_KEY=your_api_key_here

# Neo4j Database (optional)
NEO4J_HOST=localhost
NEO4J_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Output preferences
DEFAULT_LANGUAGE=bengali
EXCEL_OUTPUT=true
VERBOSE_LOGGING=false
```

### Configuration File (gitintel.conf)
```ini
[DEFAULT]
cache_enabled = true
cache_duration = 3600
max_workers = 4

[traditional]
min_commits = 1
author_similarity_threshold = 0.8
exclude_merge_commits = true

[repochat]
knowledge_graph_type = memory
max_query_results = 50
similarity_threshold = 0.7

[llm]
temperature = 0.7
max_tokens = 1000
model = gemini-pro
```

## 🔍 Example Use Cases

### 1. Project Health Assessment
```bash
python gitintel.py --repo . --insights
```
Get AI-powered insights about project health, code quality, and development patterns.

### 2. Contributor Analysis
```bash
python gitintel.py --ask "Who are the domain experts for the authentication module?"
```
Identify expertise distribution and knowledge areas.

### 3. Code Quality Review
```bash
python gitintel.py --ask "Which files need refactoring?"
python gitintel.py --ask "কোন কোড গুলো জটিল এবং সহজ করা দরকার?"
```
Get recommendations for code improvements.

### 4. Development Planning
```bash
python gitintel.py --ask "What are the recent development trends?"
```
Understand development velocity and focus areas.

## 🚨 Troubleshooting

### Common Issues

**1. Missing API Key**
```bash
Error: GEMINI_API_KEY not found
Solution: Add your Google Gemini API key to .env file
```

**2. Neo4j Connection Failed**
```bash
Warning: Neo4j not available, using in-memory storage
Solution: This is normal - GitIntel will use fallback storage
```

**3. Large Repository Performance**
```bash
# For large repositories, use sampling
python gitintel.py --repo . --sample 1000
```

**4. Bengali Font Issues**
```bash
# Ensure your terminal supports UTF-8
export LANG=en_US.UTF-8
```

## 🔧 Advanced Usage

### Batch Processing
```bash
# Analyze multiple repositories
for repo in project1 project2 project3; do
    python gitintel.py --repo $repo --output json > ${repo}_analysis.json
done
```

### Custom Queries
```python
from gitintel import GitIntelEngine

engine = GitIntelEngine()
engine.setup("/path/to/repo")

# Custom analysis
result = engine.ask_question("Complex domain-specific question")
```

### Integration with CI/CD
```yaml
# GitHub Actions example
- name: Repository Analysis
  run: |
    python gitintel.py --repo . --output json > analysis.json
    # Upload analysis results
```

## 📈 Performance Tips

1. **Large Repositories**: Use `--sample` flag to limit analysis scope
2. **Caching**: Enable caching in config for repeated analysis
3. **Parallel Processing**: Increase `max_workers` for faster processing
4. **Memory Usage**: Use Neo4j for very large knowledge graphs

## 🤝 Contributing

GitIntel is designed to be extensible:

### Adding New Metrics
1. Add metric calculation to `repochat_metrics.py`
2. Update knowledge graph schema in `repochat_knowledge_graph.py`
3. Add query patterns to `repochat_query_generator.py`

### Language Support
1. Add language patterns to query generator
2. Update prompt templates
3. Add language-specific response formatting

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **RepoChat Research**: Based on "RepoChat: An LLM-Powered Chatbot for GitHub Repository Question-Answering"
- **PyDriller**: Git repository mining framework
- **Google Gemini**: AI language model capabilities
- **Neo4j**: Graph database technology

## 🔗 Links

- [Project Repository](https://github.com/your-username/gitintel)
- [Documentation](https://gitintel.readthedocs.io)
- [Issue Tracker](https://github.com/your-username/gitintel/issues)

---

**🇧🇩 Made with ❤️ for the Bengali developer community**

*"Intelligence for every repository, insights in every language"*