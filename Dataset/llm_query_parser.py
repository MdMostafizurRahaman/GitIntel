"""
LLM-Based Query Parser for Dataset Generation
Intelligently parses user requests to extract metrics and parameters
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from metrics_catalog import MetricsCatalog

logger = logging.getLogger(__name__)

class LLMQueryParser:
    """Parse user queries using AI analysis and pattern matching"""

    def __init__(self):
        self.metrics_catalog = MetricsCatalog()
        self.supported_datasets = ['promise', 'defects4j', 'bugs_jar', 'codexglue',
                                   'codesearchnet', 'sourcerer', 'manystubs4j', 'source_code']
        self.supported_formats = ['csv', 'json', 'jsonl', 'excel', 'xlsx']

        # AI-powered analysis patterns
        self.intent_patterns = {
            'dataset_creation': [
                r'create.*dataset', r'generate.*dataset', r'make.*dataset',
                r'build.*dataset', r'produce.*dataset', r'extract.*dataset'
            ],
            'metrics_analysis': [
                r'metric', r'complexity', r'quality', r'size', r'ck.*metric',
                r'cyclomatic', r'maintainability', r'loc', r'lines.*code'
            ],
            'bug_analysis': [
                r'bug', r'defect', r'vulnerability', r'error', r'fix', r'patch'
            ],
            'code_analysis': [
                r'code.*analysis', r'source.*code', r'repository', r'project',
                r'java.*project', r'software.*metrics'
            ]
        }
    
    def parse_query(self, query: str) -> Dict:
        """
        Parse user query using AI analysis and extract intent
        Returns structured request object
        """
        logger.info(f"Parsing query: {query}")

        query_lower = query.lower()

        result = {
            'original_query': query,
            'dataset_type': None,
            'metrics': [],
            'output_format': 'csv',
            'filters': {},
            'confidence': 0.0,
            'needs_clarification': False,
            'clarification_questions': [],
            'raw_matches': {},
            'intent_analysis': {}
        }

        # 1. AI-powered intent analysis
        intent_result = self._analyze_intent_with_ai(query)
        result['intent_analysis'] = intent_result

        # 2. Detect metrics using AI analysis
        requested_metrics = self._extract_metrics_with_ai(query, intent_result)
        result['metrics'] = requested_metrics

        # 3. Detect output format
        detected_format = self._detect_format(query_lower)
        if detected_format:
            result['output_format'] = detected_format

        # 4. Detect dataset type using AI
        detected_dataset = self._detect_dataset_with_ai(query, intent_result)
        if detected_dataset:
            result['dataset_type'] = detected_dataset
        else:
            # Dataset type not specified - need clarification
            result['needs_clarification'] = True
            result['clarification_questions'].append(
                "Which dataset would you like to use? Available: promise, defects4j, bugs_jar, codexglue, codesearchnet, sourcerer, manystubs4j, source_code"
            )

        # 5. Calculate confidence based on AI analysis
        result['confidence'] = self._calculate_confidence(intent_result, result)

        # 6. Check if clarification needed
        if not result['dataset_type'] or result['confidence'] < 0.6:
            result['needs_clarification'] = True

        logger.info(f"Parse result: metrics={len(result['metrics'])}, dataset={result['dataset_type']}, confidence={result['confidence']:.2f}")

        return result
    
    def _analyze_intent_with_ai(self, query: str) -> Dict:
        """
        Use AI-like analysis to understand user intent
        This simulates LLM analysis using pattern matching and heuristics
        """
        intent_scores = {}
        
        # Analyze each intent category
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            matches = []
            
            for pattern in patterns:
                if re.search(pattern, query.lower()):
                    score += 1
                    matches.append(pattern)
            
            intent_scores[intent_type] = {
                'score': score,
                'matches': matches,
                'confidence': min(1.0, score / len(patterns))
            }
        
        # Determine primary intent
        primary_intent = max(intent_scores.items(), key=lambda x: x[1]['score'])
        
        return {
            'primary_intent': primary_intent[0],
            'intent_scores': intent_scores,
            'overall_confidence': sum(s['confidence'] for s in intent_scores.values()) / len(intent_scores)
        }
    
    def _extract_metrics_with_ai(self, query: str, intent_analysis: Dict) -> List[str]:
        """
        Extract requested metrics using AI analysis
        """
        metrics = []
        query_lower = query.lower()
        
        # If intent is metrics analysis, be more aggressive in finding metrics
        is_metrics_focused = intent_analysis['primary_intent'] == 'metrics_analysis'
        
        # First, check for exact metric name matches (highest priority)
        exact_matches = []
        for metric_key in self.metrics_catalog.get_metric_names():
            if metric_key in query_lower:
                exact_matches.append(metric_key)
        
        if exact_matches:
            metrics.extend(exact_matches)
        
        # Then check for partial matches in metric names and descriptions
        if not exact_matches:  # Only if no exact matches found
            for metric_key in self.metrics_catalog.get_metric_names():
                metric = self.metrics_catalog.ALL_METRICS[metric_key]
                
                # Check if metric name, abbreviation, or description words appear in query
                name_words = metric['name'].lower().split()
                desc_words = metric['description'].lower().split()
                
                # For metrics-focused queries, be more lenient
                threshold = 2 if is_metrics_focused else 3
                
                for word in name_words + desc_words:
                    if len(word) > threshold and word in query_lower:
                        if metric_key not in metrics:
                            metrics.append(metric_key)
                        break
        
        # Handle common phrases with AI understanding
        if self._contains_any(query_lower, ['all metric', 'complete', 'full', 'everything']):
            metrics = self.metrics_catalog.get_metric_names()
        elif self._contains_any(query_lower, ['ck metric', 'chidamber', 'object oriented']):
            metrics.extend(list(self.metrics_catalog.CK_METRICS.keys()))
        elif self._contains_any(query_lower, ['complexity', 'cyclomatic', 'difficulty']):
            metrics.extend(list(self.metrics_catalog.COMPLEXITY_METRICS.keys()))
        elif self._contains_any(query_lower, ['size', 'loc', 'lines of code', 'length']):
            metrics.extend(list(self.metrics_catalog.SIZE_METRICS.keys()))
        elif self._contains_any(query_lower, ['quality', 'maintainab', 'readability']):
            metrics.extend(list(self.metrics_catalog.QUALITY_METRICS.keys()))
        elif self._contains_any(query_lower, ['bug', 'defect', 'error', 'fault']):
            metrics.extend(list(self.metrics_catalog.DEFECT_METRICS.keys()))
        elif self._contains_any(query_lower, ['coupling', 'cohesion', 'dependency']):
            metrics.extend(list(self.metrics_catalog.COUPLING_METRICS.keys()))
        elif self._contains_any(query_lower, ['structure', 'class', 'method', 'field', 'interface']):
            metrics.extend(list(self.metrics_catalog.STRUCTURE_METRICS.keys()))
        
        # If no specific metrics found but intent suggests metrics analysis, include basics
        if not metrics and is_metrics_focused:
            metrics = ['loc', 'cyclomatic_complexity', 'maintainability_index']
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(metrics))
    
    def _detect_dataset_with_ai(self, query: str, intent_analysis: Dict) -> Optional[str]:
        """
        Detect which dataset to use using AI analysis
        """
        query_lower = query.lower()
        
        # Direct dataset mentions
        for dataset in self.supported_datasets:
            if dataset in query_lower:
                return dataset
        
        # Check for specific structure metrics - these indicate source code analysis
        structure_metrics = [
            'num_static_methods', 'num_private_methods', 'num_public_methods', 
            'num_fields', 'num_methods', 'num_interfaces', 'num_classes',
            'number of classes', 'number of methods', 'number of interfaces'
        ]
        
        has_structure_metrics = any(metric in query_lower for metric in structure_metrics)
        if has_structure_metrics:
            return 'source_code'
        
        # AI-powered inference based on intent and content
        primary_intent = intent_analysis['primary_intent']
        
        # For bug/defect analysis, suggest defects4j or bugs_jar
        if primary_intent == 'bug_analysis':
            if 'java' in query_lower:
                return 'defects4j'
            else:
                return 'bugs_jar'
        
        # For code analysis, suggest source_code or promise
        elif primary_intent == 'code_analysis':
            if self._contains_any(query_lower, ['repository', 'project', 'github', 'source']):
                return 'source_code'
            elif self._contains_any(query_lower, ['metric', 'complexity', 'quality']):
                return 'promise'
        
        # For dataset creation with metrics, default to promise
        elif primary_intent == 'dataset_creation':
            if self._contains_any(query_lower, ['metric', 'complexity', 'quality', 'ck']):
                return 'promise'
            elif self._contains_any(query_lower, ['bug', 'defect']):
                return 'defects4j'
        
        # Check for project/repository names that indicate source code analysis
        source_code_indicators = [
            'elasticsearch', 'elastic search', 'spring', 'hibernate', 'maven', 
            'gradle', 'java project', 'source code', 'repository', 'repo',
            'github', 'gitlab', 'codebase', 'project'
        ]
        
        indicator_count = sum(1 for indicator in source_code_indicators if indicator in query_lower)
        has_metrics = any(metric in query_lower for metric in ['loc', 'complexity', 'cyclomatic', 'metric'])
        
        if indicator_count >= 2 or (has_metrics and 'dataset' in query_lower):
            return 'source_code'
        
        # Check for Java code mentions - suggest promise or bugs_jar
        if 'java' in query_lower and 'metric' in query_lower:
            return 'promise'
        
        return None
    
    def _calculate_confidence(self, intent_analysis: Dict, result: Dict) -> float:
        """
        Calculate overall confidence score
        """
        base_confidence = intent_analysis['overall_confidence']
        
        # Boost confidence if we have clear dataset type
        if result['dataset_type']:
            base_confidence += 0.3
        
        # Boost confidence based on exact metric matches
        exact_metric_matches = 0
        for metric in result['metrics']:
            if metric in result['original_query'].lower():
                exact_metric_matches += 1
        
        if exact_metric_matches > 0:
            base_confidence += min(0.4, exact_metric_matches * 0.1)
        
        # Boost confidence based on metrics found ratio
        metrics_ratio = len(result['metrics']) / len(self.metrics_catalog.get_metric_names())
        base_confidence += (metrics_ratio * 0.2)
        
        # Cap at 1.0
        return min(1.0, base_confidence)
    
    def _contains_any(self, text: str, patterns: List[str]) -> bool:
        """Check if text contains any of the patterns"""
        return any(pattern in text for pattern in patterns)
        """Extract requested metrics from query"""
        metrics = []
        
        # Search for each metric in query
        for metric_key in self.metrics_catalog.get_metric_names():
            metric = self.metrics_catalog.ALL_METRICS[metric_key]
            
            # Check if metric name, abbreviation, or description words appear in query
            name_words = metric['name'].lower().split()
            desc_words = metric['description'].lower().split()
            
            for word in name_words + desc_words:
                if len(word) > 2 and word in query:  # Ignore short words
                    if metric_key not in metrics:
                        metrics.append(metric_key)
                    break
        
        # Handle common phrases
        if 'all metric' in query or 'complete' in query or 'full' in query:
            metrics = self.metrics_catalog.get_metric_names()
        elif 'ck metric' in query or 'chidamber' in query:
            metrics.extend(list(self.metrics_catalog.CK_METRICS.keys()))
        elif 'complexity' in query:
            metrics.extend(list(self.metrics_catalog.COMPLEXITY_METRICS.keys()))
        elif 'size' in query or 'loc' in query:
            metrics.extend(list(self.metrics_catalog.SIZE_METRICS.keys()))
        elif 'quality' in query or 'maintainab' in query:
            metrics.extend(list(self.metrics_catalog.QUALITY_METRICS.keys()))
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(metrics))
    
    def _detect_format(self, query: str) -> Optional[str]:
        """Detect desired output format"""
        for fmt in self.supported_formats:
            if fmt in query:
                return 'xlsx' if fmt in ['excel', 'xlsx'] else fmt
        return None
    
    def _detect_dataset(self, query: str) -> Optional[str]:
        """Detect which dataset to use"""
        for dataset in self.supported_datasets:
            if dataset in query:
                return dataset
        
        # Check for project/repository names that indicate source code analysis
        source_code_indicators = [
            'elasticsearch', 'elastic search', 'spring', 'hibernate', 'maven', 
            'gradle', 'java project', 'source code', 'repository', 'repo',
            'github', 'gitlab', 'codebase', 'project', 'loc', 'cyclometric',
            'complexity', 'metrics', 'dataset'
        ]
        
        # If multiple source code indicators are present, or if we have metrics but no dataset,
        # default to source_code analysis
        indicator_count = sum(1 for indicator in source_code_indicators if indicator in query)
        has_metrics = any(metric in query.lower() for metric in ['loc', 'complexity', 'cyclomatic', 'soc', 'lloc'])
        
        if indicator_count >= 2 or (has_metrics and 'dataset' in query):
            return 'source_code'
        
        for indicator in source_code_indicators:
            if indicator in query:
                return 'source_code'
        
        # Check for Java code mentions - suggest promise or bugs_jar
        if 'java' in query and 'metric' in query:
            return 'promise'
        
        return None
    
    def ask_clarification(self, parse_result: Dict) -> Dict:
        """
        Interactively ask user for clarification on ambiguous queries
        """
        if not parse_result['needs_clarification']:
            return parse_result
        
        print("\n" + "="*70)
        print("🤖 AI DATASET GENERATION ASSISTANT")
        print("="*70)
        
        print(f"\nYour Request: {parse_result['original_query']}")
        print(f"AI Confidence: {parse_result['confidence']*100:.1f}%")
        
        intent = parse_result['intent_analysis']['primary_intent']
        print(f"Detected Intent: {intent.replace('_', ' ').title()}")
        
        if parse_result['clarification_questions']:
            print("\n📋 Questions to clarify your request:\n")
            
            for i, question in enumerate(parse_result['clarification_questions'], 1):
                print(f"{i}. {question}")
        
        # Ask for dataset if not specified
        if not parse_result['dataset_type']:
            print("\n📊 Available Datasets:")
            dataset_descriptions = {
                'promise': 'Software metrics for defect prediction (CK, complexity, quality metrics)',
                'defects4j': 'Real Java bug fixes from open source projects',
                'bugs_jar': 'Large-scale Java bug dataset with comprehensive metrics',
                'codexglue': 'Code-to-code transformation tasks',
                'codesearchnet': 'Code-to-documentation mapping',
                'sourcerer': 'Large-scale source code mining',
                'manystubs4j': 'Java bug fixes with rich context',
                'source_code': 'Generic source code repository analysis'
            }
            
            for i, ds in enumerate(self.supported_datasets, 1):
                desc = dataset_descriptions.get(ds, 'General dataset')
                print(f"  {i}. {ds} - {desc}")
            
            while True:
                choice = input("\n🎯 Select dataset (number or name): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(self.supported_datasets):
                        parse_result['dataset_type'] = self.supported_datasets[idx]
                        break
                elif choice in self.supported_datasets:
                    parse_result['dataset_type'] = choice
                    break
                print("❌ Invalid choice. Please try again.")
        
        # Ask for specific metrics if auto-detected many
        total_metrics = len(self.metrics_catalog.get_metric_names())
        if len(parse_result['metrics']) == total_metrics:
            print(f"\n📈 AI detected: ALL {total_metrics} metrics")
            response = input("Use all metrics? (yes/no): ").strip().lower()
            if response == 'no':
                self._ask_for_specific_metrics(parse_result)
        elif len(parse_result['metrics']) > 10:
            print(f"\n📈 AI detected: {len(parse_result['metrics'])} metrics")
            response = input("Refine metrics selection? (yes/no): ").strip().lower()
            if response.lower() == 'yes':
                self._ask_for_specific_metrics(parse_result)
        
        parse_result['needs_clarification'] = False
        return parse_result
    
    def _ask_for_specific_metrics(self, parse_result: Dict):
        """Ask user to specify which metrics they want"""
        print("\n📊 Available Metrics Categories:")
        categories = self.metrics_catalog.get_categories()
        for i, cat in enumerate(categories, 1):
            metric_count = len(self.metrics_catalog.get_metrics_by_category(cat))
            print(f"  {i}. {cat.title()} ({metric_count} metrics)")
        
        print("  0. Custom selection")
        
        choice = input("\n🎯 Select category (number) or 0 for custom: ").strip()
        
        if choice == '0':
            print("\n📝 Type metric names separated by commas:")
            print("Examples: loc, cyclomatic_complexity, maintainability_index")
            user_input = input("Metrics: ").strip()
            if user_input:
                parse_result['metrics'] = [m.strip() for m in user_input.split(',')]
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(categories):
                    category = categories[idx]
                    parse_result['metrics'] = list(
                        self.metrics_catalog.get_metrics_by_category(category).keys()
                    )
                    print(f"✅ Selected {len(parse_result['metrics'])} {category} metrics")
            except ValueError:
                print("❌ Invalid choice")
    
    def format_result_summary(self, parse_result: Dict) -> str:
        """Format parse result as readable summary"""
        summary = []
        summary.append("\n" + "="*70)
        summary.append("🤖 AI DATASET GENERATION PLAN")
        summary.append("="*70)
        summary.append(f"\n🎯 Dataset Type: {parse_result['dataset_type']}")
        summary.append(f"📄 Output Format: {parse_result['output_format']}")
        summary.append(f"🎯 Primary Intent: {parse_result['intent_analysis']['primary_intent'].replace('_', ' ').title()}")
        summary.append(f"📊 Metrics Selected ({len(parse_result['metrics'])}):")
        
        # Group metrics by category for readability
        by_category = {}
        for metric_key in parse_result['metrics']:
            if metric_key in self.metrics_catalog.ALL_METRICS:
                metric = self.metrics_catalog.ALL_METRICS[metric_key]
                cat = metric['category']
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(metric_key)
        
        for category in sorted(by_category.keys()):
            summary.append(f"\n  [{category.upper()}]")
            for metric_key in by_category[category]:
                metric = self.metrics_catalog.ALL_METRICS[metric_key]
                summary.append(f"    ✓ {metric['name']}")
        
        summary.append("\n" + "="*70 + "\n")
        return "\n".join(summary)


def demonstrate_parser():
    """Demonstrate the query parser"""
    parser = LLMQueryParser()
    
    test_queries = [
        "Generate a dataset of LOC, cyclomatic complexity and CK metrics in CSV format",
        "I need all metrics from promise dataset as Excel",
        "Create dataset with complexity metrics",
        "Give me bugs data with all metrics",
    ]
    
    print("\n" + "="*70)
    print("QUERY PARSER DEMONSTRATION")
    print("="*70)
    
    for query in test_queries:
        print(f"\nInput: {query}")
        result = parser.parse_query(query)
        print(f"Dataset: {result['dataset_type']}")
        print(f"Metrics: {result['metrics'][:3]}... ({len(result['metrics'])} total)")
        print(f"Format: {result['output_format']}")
        print(f"Confidence: {result['confidence']*100:.1f}%")
        print(f"Needs Clarification: {result['needs_clarification']}")


if __name__ == '__main__':
    demonstrate_parser()
