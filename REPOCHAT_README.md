# RepoChat CLI - LLM-Powered Repository Question-Answering System

A command-line implementation of the RepoChat concept from the research paper, combining Large Language Models (LLMs) with knowledge graphs for intelligent repository analysis and question-answering.

## 🚀 Features

### Core Capabilities
- **Knowledge Graph Construction**: Builds comprehensive repository knowledge graphs from Git metadata
- **Natural Language Queries**: Ask questions in English or Bengali about your repository
- **LLM-Powered Analysis**: Uses Google Gemini AI for intelligent query processing
- **Repository Metrics**: Comprehensive testing and quality metrics extraction
- **CLI Interface**: Easy-to-use command-line tool for developers

### Supported Question Types
- **Contributors**: "Who are the top contributors?", "কে সবচেয়ে বেশি commit করেছে?"
- **File Analysis**: "Which files change most frequently?", "কোন file এ সবচেয়ে বেশি bug আছে?"
- **Code Metrics**: "What is the complexity analysis?", "LOC per package দেখাও"
- **Bug Analysis**: "Show me bug-fixing commits", "Which developer introduced the most bugs?"
- **Testing Metrics**: "What is the test coverage?", "Test-to-source ratio কত?"
- **Quality Metrics**: "Show code churn analysis", "Refactoring commits দেখাও"

## 📦 Installation

### Prerequisites
- Python 3.8+
- Git installed and accessible from command line
- Google Gemini API key (for LLM features)

### Setup
```powershell
# Clone or navigate to GitIntelProject
cd D:\GitIntel\GitIntelProject

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env

# Optional: Install Neo4j for advanced graph features
# pip install neo4j
```

## 🎯 Quick Start

### 1. Interactive Mode (Recommended)
```powershell
python repochat_cli.py --repo D:\GitIntel\kafka
```

### 2. One-shot Question
```powershell
python repochat_cli.py --repo D:\GitIntel\maven --ask "Who are the top contributors?"
```

### 3. Data Ingestion Only
```powershell
python repochat_cli.py --repo D:\GitIntel\kafka --ingest
```

## 📋 Usage Examples

### Setting Up a Repository
```powershell
# Analyze Apache Kafka
python repochat_cli.py --repo D:\GitIntel\kafka

# Analyze Maven project
python repochat_cli.py --repo D:\GitIntel\maven

# Analyze Spring Boot course materials
python repochat_cli.py --repo "D:\GitIntel\Spring-Boot-in-Detailed-Way"
```

### Sample Questions

#### English Questions
```powershell
python repochat_cli.py --ask "Who are the most active contributors?"
python repochat_cli.py --ask "Which files have the highest complexity?"
python repochat_cli.py --ask "Show me recent bug-fixing commits"
python repochat_cli.py --ask "What is the test coverage ratio?"
python repochat_cli.py --ask "Which packages have the most code churn?"
```

#### Bengali Questions (Supported!)
```powershell
python repochat_cli.py --ask "কে সবচেয়ে বেশি commit করেছে?"
python repochat_cli.py --ask "কোন file এ সবচেয়ে বেশি change হয়েছে?"
python repochat_cli.py --ask "বাগ fix করার commit গুলো দেখাও"
python repochat_cli.py --ask "কোন package এ complexity সবচেয়ে বেশি?"
python repochat_cli.py --ask "test coverage কত percentage?"
```

### Interactive Mode Commands
```
RepoChat>>> Who are the top contributors?
RepoChat>>> help              # Show available commands  
RepoChat>>> status            # Show repository status
RepoChat>>> ingest            # Rebuild knowledge graph
RepoChat>>> quit              # Exit
```

## 🏗️ Architecture

### Data Ingestion Step
1. **Repository Metadata Extraction**: Uses PyDriller to extract commits, files, contributors
2. **Knowledge Graph Construction**: Creates nodes and relationships for all repository entities
3. **Metrics Generation**: Calculates comprehensive repository metrics
4. **Storage**: Saves to in-memory graph or Neo4j database

### Interaction Step
1. **Query Generation**: Converts natural language to Cypher queries using LLM
2. **Query Execution**: Runs queries against the knowledge graph
3. **Response Generation**: Creates user-friendly responses from query results

### Fallback System
- **Pattern Matching**: When LLM is unavailable, uses regex-based query mapping
- **In-Memory Storage**: Works without Neo4j using JSON-based graph storage
- **Simple Metrics**: Basic analysis without complex dependencies

## 📊 Available Metrics

### Repository Metrics
- Total commits, contributors, files
- Repository age and activity timeline
- Lines of code by language
- Code churn analysis

### Code Quality Metrics
- Bug-fixing commits identification
- Complexity analysis per file/package
- Refactoring and maintenance commits
- High-churn files identification

### Testing Metrics
- Test file detection and counting
- Test-to-source file ratio
- Test framework identification
- Test evolution over time

### Contributor Metrics
- Activity levels and contributions
- Files modified per contributor
- Collaboration patterns
- New contributor onboarding trends

### Time-Based Metrics
- Commit frequency analysis
- Development velocity trends
- Monthly/weekly activity patterns
- Release timeline analysis

## 🔧 Configuration

### Environment Variables
```env
# Required for LLM features
GEMINI_API_KEY=your_google_gemini_api_key

# Optional Neo4j configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Command Line Options
```powershell
python repochat_cli.py [OPTIONS]

Options:
  --repo, -r PATH          Repository path to analyze
  --ingest, -i             Run data ingestion to build knowledge graph
  --ask, -a TEXT           Ask a specific question
  --interactive, -int      Start interactive mode (default)
  --verbose, -v            Enable verbose logging
  --help                   Show help message
```

## 🎭 Knowledge Graph Schema

### Node Types
- **Repository**: Project information and metadata
- **Contributor**: Developer information and statistics  
- **Commit**: Individual commits with changes and metrics
- **File**: Source files with complexity and size information
- **Branch**: Git branches and their metadata
- **Tag**: Git tags and release information

### Relationships
- `(Contributor)-[:AUTHORED]->(Commit)`
- `(Commit)-[:MODIFIED]->(File)`
- `(Branch)-[:CONTAINS]->(Commit)`
- `(Tag)-[:POINTS_TO]->(Commit)`

## 🔍 Query Examples

### Cypher Queries Generated
```cypher
# Top contributors
MATCH (c:Contributor) RETURN c.name, c.commits ORDER BY c.commits DESC LIMIT 10

# Most modified files
MATCH (c:Commit)-[r:MODIFIED]->(f:File) RETURN f.name, count(r) as changes ORDER BY changes DESC LIMIT 10

# Bug-fixing commits
MATCH (c:Commit) WHERE c.is_bug_fix = true RETURN c.hash, c.message, c.author_name ORDER BY c.date DESC LIMIT 10

# Complex files
MATCH (f:File) WHERE f.lines_of_code > 100 RETURN f.name, f.lines_of_code ORDER BY f.lines_of_code DESC LIMIT 10
```

## 🐛 Common Issues & Solutions

### LLM Not Available
- **Issue**: `GEMINI_API_KEY not found`
- **Solution**: Set up your Gemini API key in `.env` file
- **Fallback**: System will use pattern-based query generation

### Neo4j Connection Failed
- **Issue**: `Neo4j not available`
- **Solution**: Install Neo4j or use in-memory graph storage
- **Fallback**: System automatically uses JSON-based storage

### Large Repository Performance
- **Issue**: Slow processing for large repositories
- **Solution**: Use commit limits in existing LLM tools for initial analysis
- **Example**: `python llm_cli.py "package churn first 500 commits"`

### Memory Issues
- **Issue**: Out of memory for very large repositories
- **Solution**: Process repositories in chunks or use database storage
- **Workaround**: Focus analysis on specific timeframes or packages

## 🔗 Integration with Existing Tools

RepoChat CLI integrates seamlessly with your existing GitIntelProject tools:

```powershell
# Use existing LLM analysis first
python llm_cli.py "LOC analysis first 1000 commits"

# Then use RepoChat for detailed questions
python repochat_cli.py --ask "Which packages from the LOC analysis have the highest complexity?"

# Combine with package analysis
python llm_cli.py "package churn analysis" 
python repochat_cli.py --ask "Show me contributors to high-churn packages"
```

## 🏆 Advantages Over Traditional Tools

### vs. Git Log Commands
- **Natural Language**: Ask questions instead of complex git commands
- **Aggregated Insights**: Combines multiple data sources automatically
- **Bengali Support**: Native language query support

### vs. GitHub Insights
- **Local Analysis**: Works on any Git repository, not just GitHub
- **Custom Metrics**: Extensible metrics and analysis capabilities
- **LLM Intelligence**: Smart question interpretation and response generation

### vs. Static Analysis Tools
- **Dynamic Queries**: Ask any question, not just predefined reports
- **Historical Analysis**: Incorporates commit history and evolution
- **Context Aware**: Understands relationships between different repository entities

## 🚧 Future Enhancements

### Planned Features
- [ ] GitHub API integration for issues and pull requests
- [ ] SZZ algorithm implementation for bug-introducing commit detection
- [ ] Advanced visualization generation
- [ ] Web interface (similar to original RepoChat paper)
- [ ] Support for additional version control systems
- [ ] Machine learning models for predictive analysis

### Advanced Analytics
- [ ] Code review effectiveness analysis
- [ ] Developer productivity patterns
- [ ] Technical debt accumulation tracking
- [ ] Security vulnerability correlation analysis

## 📚 Research Background

Based on the RepoChat research paper:
> "RepoChat: An LLM-Powered Chatbot for GitHub Repository Question-Answering" by Samuel Abedu et al.

**Key Innovations**:
- Synergizes LLMs with knowledge graphs for accurate repository QA
- Achieves 90% accuracy in answering repository-related questions
- Addresses limitations of pure RAG-based approaches for software repositories

## 🤝 Contributing

Contributions welcome! This implementation extends the original research with:
- CLI-first approach for developer workflows
- Bengali language support for diverse users
- Integration with existing analysis tools
- Comprehensive testing and quality metrics

## 📄 License

MIT License - Feel free to extend and modify for your needs.

---

**Happy Repository Analysis! 🎉**

Ask intelligent questions about your code, get intelligent answers.