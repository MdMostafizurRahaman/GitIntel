# Professional Datasets Generated

This directory contains 7 professional-quality datasets generated from the Java repositories in the workspace.

## Generated Datasets

### 1. Defects4J Dataset (`defects4j_dataset/`)
- **Type**: Bug-fix pairs dataset
- **Format**: JSON + individual bug directories
- **Records**: 10 bug pairs
- **Structure**:
  - `defects4j_dataset.json`: Complete dataset metadata
  - `bug_XXX/`: Individual bug directories
    - `buggy.java`: Code with synthetic bug
    - `fixed.java`: Corrected code

### 2. Bugs.jar Dataset (`bugs_jar_dataset.json`)
- **Type**: Code metrics and defect analysis
- **Format**: JSON
- **Records**: 80 files analyzed
- **Metrics**: LOC, classes, methods, complexity

### 3. CodeXGLUE Dataset (`codexglue_dataset.json`)
- **Type**: Code-to-code and code-to-text mappings
- **Format**: JSON
- **Records**: 97 code snippets
- **Features**: Method signatures, code snippets, complexity

### 4. CodeSearchNet Dataset (`codesearchnet_dataset.json`)
- **Type**: Code to documentation mapping
- **Format**: JSON
- **Records**: 40 code-documentation pairs
- **Features**: Tokenized code and documentation

### 5. Sourcerer Dataset (`sourcerer_dataset.json`)
- **Type**: Large-scale source code mining
- **Format**: JSON
- **Records**: 100 source files
- **Features**: File metadata, project structure

### 6. PROMISE Dataset (`promise_dataset.csv`)
- **Type**: Software metrics and defect prediction
- **Format**: CSV
- **Records**: 120 files
- **Features**: Lines of code, defect counts

### 7. ManySStuBs4J Dataset (`manystubs4j_dataset.json`)
- **Type**: Issue-based bug dataset
- **Format**: JSON
- **Records**: 20 issue records
- **Features**: Issue descriptions, code snippets

## Source Repositories Analyzed

- **druid**: Apache Druid (large Java project)
- **kafka**: Apache Kafka (large Java project)
- **maven**: Apache Maven (build tool)
- **test**: Test repository

## Usage

These datasets can be used for:
- Machine learning model training
- Code analysis research
- Bug detection algorithms
- Code search and recommendation systems
- Software metrics analysis

## Generation Script

The datasets were generated using `dataset_generator.py` which analyzes Java repositories and creates synthetic data similar to professional datasets like Defects4J, Bugs.jar, etc.

## Notes

- All datasets contain synthetic data for demonstration purposes
- Real datasets would require extensive manual curation and validation
- The structure and format match professional dataset standards