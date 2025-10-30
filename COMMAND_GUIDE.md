# GitIntel Complete Command Guide

## 🚀 Quick Start Commands

### Repository Setup
```bash
# Clone a new repository
python gitintel.py "clone https://github.com/apache/kafka"

# Set existing repository
python gitintel.py "set_repo d:\GitIntel\Kafka"

# Check status
python gitintel.py --repo d:\GitIntel\kafka --status
```

## 📊 Traditional Analytics (Excel Reports)

### Package Analysis
```bash
# Package churn analysis
python gitintel.py --repo d:\GitIntel\eureka "package churn first 500 commits"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "প্যাকেজ churn analysis করো"
```

### Lines of Code Analysis
```bash
# LOC analysis
python gitintel.py --repo d:\GitIntel\eureka "loc analysis first 500 commits"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "LOC analysis report দাও"
```

### Complexity Analysis
```bash
# Complexity analysis
python gitintel.py --repo d:\GitIntel\eureka "complexity analysis first 300 commits"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "complexity analysis করো"
```

### Release Analysis
```bash
# Release analysis
python gitintel.py --repo d:\GitIntel\eureka "release wise changes first 300 commits"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "release changes দেখাও"
```

## 🤖 Interactive Q&A Commands

### Contributor Questions
```bash
# English
python gitintel.py --repo d:\GitIntel\eureka "Who are the top contributors?"
python gitintel.py --repo d:\GitIntel\eureka "Which developer committed the most code?"
python gitintel.py --repo d:\GitIntel\eureka "Show me contributor statistics"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "কে সবচেয়ে বেশি commit করেছে?"
python gitintel.py --repo d:\GitIntel\eureka "কোন developer সবচেয়ে productive?"
```

### File & Package Questions
```bash
# English
python gitintel.py --repo d:\GitIntel\eureka "Which files change most frequently?"
python gitintel.py --repo d:\GitIntel\eureka "What are the most complex files?"
python gitintel.py --repo d:\GitIntel\eureka "Show me high-churn packages"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "কোন file এ সবচেয়ে বেশি change হয়েছে?"
python gitintel.py --repo d:\GitIntel\eureka "কোন file এ বেশি complexity আছে?"
```

### Bug & Quality Questions
```bash
# English
python gitintel.py --repo d:\GitIntel\eureka "Show me recent bug fixes"
python gitintel.py --repo d:\GitIntel\eureka "Which files have the most bugs?"
python gitintel.py --repo d:\GitIntel\eureka "What is the code quality trend?"

# Bengali
python gitintel.py --repo d:\GitIntel\eureka "সাম্প্রতিক bug fix গুলো দেখাও"
python gitintel.py --repo d:\GitIntel\eureka "কোন file এ সবচেয়ে বেশি bug আছে?"
```

## 🔧 System Commands

### Knowledge Graph Management
```bash
# Build knowledge graph for better Q&A
python gitintel.py --repo d:\GitIntel\eureka --build-kg

# Check system status
python gitintel.py --repo d:\GitIntel\eureka --status
```

### Interactive Mode
```bash
# Start interactive session
python gitintel.py --repo d:\GitIntel\eureka --interactive

# In interactive mode, use these commands:
GitIntel>>> package churn first 500 commits
GitIntel>>> Who are the top contributors?
GitIntel>>> কে সবচেয়ে বেশি commit করেছে?
GitIntel>>> help
GitIntel>>> status
GitIntel>>> quit
```

### Comprehensive Analysis
```bash
# Run both traditional and Q&A analysis
python gitintel.py --repo d:\GitIntel\eureka --analyze combined

# Only traditional analytics
python gitintel.py --repo d:\GitIntel\eureka --analyze traditional

# Only Q&A system
python gitintel.py --repo d:\GitIntel\eureka --analyze repochat
```

## 🎯 Working Examples (Tested)

### ✅ Netflix Eureka Repository
```bash
# Setup
python gitintel.py "clone https://github.com/Netflix/eureka"

# Traditional Analytics (Working)
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "package churn first 500 commits"
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "loc analysis first 500 commits"
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "complexity analysis first 300 commits"

# Q&A (Working after fix)
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka --build-kg
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "Who are the top contributors?"
```

### ✅ Apache Kafka Repository
```bash
# Setup
python gitintel.py "set_repo d:\GitIntel\kafka"

# Analysis
python gitintel.py --repo d:\GitIntel\kafka "package churn first 1000 commits"
python gitintel.py --repo d:\GitIntel\kafka "কে সবচেয়ে বেশি commit করেছে?"
```

## 📁 Output Files

### Excel Reports Location
```
D:\GitIntel\GitIntelProject\
├── package_churn_analysis_20251030_214143.xlsx
├── loc_analysis_20251030_215544.xlsx
├── complexity_analysis_20251030_215613.xlsx
└── ...
```

### Knowledge Graph Files
```
D:\GitIntel\GitIntelProject\
├── .repochat_state.json
├── .repochat_graph.json
└── ...
```

## 🔍 Troubleshooting

### If Q&A doesn't work:
```bash
# Build knowledge graph first
python gitintel.py --repo <your_repo> --build-kg

# Then try Q&A
python gitintel.py --repo <your_repo> "Who are the top contributors?"
```

### If repository not found:
```bash
# Check current working directory
cd d:\GitIntel\GitIntelProject

# Set repository explicitly
python gitintel.py "set_repo d:\GitIntel\eureka"
```

### If commands don't work:
```bash
# Check status
python gitintel.py --repo <your_repo> --status

# Try verbose mode
python gitintel.py --repo <your_repo> --verbose "your command"
```

## 🎯 Best Commands to Try Right Now

### Start with these working commands:
```bash
# 1. Set repository
python gitintel.py "set_repo d:\GitIntel\GitIntelProject\eureka"

# 2. Traditional analytics (guaranteed to work)
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "package churn first 300 commits"

# 3. Build knowledge graph
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka --build-kg

# 4. Try Q&A
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "Who are the top contributors?"

# 5. Interactive mode
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka --interactive
```

## 🚀 Next Level Commands

### Bengali Mixed Commands
```bash
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "complexity analysis করো first 200 commits"
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "কোন package এ সবচেয়ে বেশি churn আছে?"
```

### Advanced Analysis
```bash
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "release wise changes first 500 commits"
python gitintel.py --repo d:\GitIntel\GitIntelProject\eureka "loc per month first 1000 commits"
```

**Your GitIntel is now fully working! 🎉**