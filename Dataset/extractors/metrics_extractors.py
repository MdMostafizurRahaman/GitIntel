"""
PROMISE Repository Dataset Extractor
Software engineering datasets for metrics and bug prediction
"""

from typing import Dict, List, Optional
import logging
from pathlib import Path
import csv
import json
import re
from extractors.base_extractor import FileExtractor
import os
import javalang
from ck_metrics_analyzer import CKMetricsAnalyzer
from unified_metrics_analyzer import UnifiedMetricsAnalyzer

logger = logging.getLogger(__name__)

class PROMISEExtractor(FileExtractor):
    """Extractor for PROMISE Repository dataset"""
    
    def __init__(self, file_path: str, config: Optional[Dict] = None):
        """Initialize PROMISE extractor"""
        # Don't call parent init yet - we need to handle directories
        self.source = file_path
        self.config = config or {}
        self.extracted_data = []
        self.metadata = {}
        self.temp_dir = None
        
        # Handle both files and directories
        source_path = Path(file_path)
        
        if source_path.is_file():
            # Single file - use parent class validation
            super().__init__(file_path, config)
            self.file_path = source_path
        elif source_path.is_dir():
            # Directory - look for PROMISE files inside
            self.file_path = source_path
            self.dataset_type = "promise"
        else:
            raise ValueError(f"Invalid path: {file_path}")
        
        self.dataset_type = "promise"
    
    def validate(self) -> bool:
        """Validate PROMISE source"""
        if not self.file_path.exists():
            logger.error(f"Source not found: {self.file_path}")
            return False
        
        if self.file_path.is_file():
            # Single file - must be CSV, JSON, or ARFF
            return self.file_path.suffix in ['.csv', '.json', '.arff']
        
        elif self.file_path.is_dir():
            # Directory - must contain at least one PROMISE file
            for ext in ['*.csv', '*.json', '*.arff']:
                if list(self.file_path.glob(ext)):
                    return True
            
            # Check subdirectories
            for root, dirs, files in __import__('os').walk(self.file_path):
                for file in files:
                    if file.endswith(('.csv', '.json', '.arff')):
                        return True
            
            logger.error(f"No PROMISE files (CSV, JSON, ARFF) found in {self.file_path}")
            return False
        
        return False
    
    def extract(self) -> List[Dict]:
        """
        Extract PROMISE format data
        Software metrics and defect labels
        """
        logger.info(f"Extracting PROMISE data from {self.file_path}")
        
        extracted = []
        
        if self.file_path.is_file():
            # Single file
            if self.file_path.suffix == ".csv":
                extracted = self._extract_from_csv()
            elif self.file_path.suffix == ".arff":
                extracted = self._extract_from_arff()
            elif self.file_path.suffix == ".json":
                extracted = self._extract_from_json()
        
        elif self.file_path.is_dir():
            # Directory - first try to find PROMISE files
            extracted = self._extract_from_directory()
            
            # If no PROMISE files found, try extracting from Java source code
            if not extracted:
                logger.info("No PROMISE files found, attempting to extract metrics from Java source code")
                extracted = self._extract_from_java_files()
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "promise_structure")
        self.set_metadata("metrics_count", len(extracted[0].keys()) - 3 if extracted else 0)
        
        logger.info(f"Extracted {len(extracted)} PROMISE records")
        return extracted
    
    def _extract_from_directory(self) -> List[Dict]:
        """Extract from directory containing PROMISE files"""
        records = []
        import os
        
        try:
            # Find and process all PROMISE format files
            for root, dirs, files in os.walk(self.file_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    try:
                        if file.endswith('.csv'):
                            records.extend(self._extract_from_csv(file_path))
                        elif file.endswith('.arff'):
                            records.extend(self._extract_from_arff(file_path))
                        elif file.endswith('.json'):
                            records.extend(self._extract_from_json(file_path))
                    except Exception as e:
                        logger.warning(f"Error processing {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting from directory: {e}")
        
        return records
    
    def _extract_from_java_files(self) -> List[Dict]:
        """Extract metrics from Java source code files"""
        records = []
        
        try:
            # Analyze the entire repository once to get all metrics
            logger.info("Analyzing entire repository for comprehensive metrics...")
            
            # Get CK metrics for the whole repository
            ck_analyzer = CKMetricsAnalyzer(str(self.file_path))
            ck_results = ck_analyzer.analyze_repository()
            
            # Get unified metrics for the whole repository  
            unified_analyzer = UnifiedMetricsAnalyzer(str(self.file_path))
            unified_results = unified_analyzer.analyze_all()
            
            logger.info(f"Repository analysis complete. Found {len(ck_results)} classes with CK metrics, {len(unified_results)} with unified metrics")
            
            # Now process each Java file using the pre-computed metrics
            for root, dirs, files in os.walk(self.file_path):
                for file in files:
                    if file.endswith('.java'):
                        file_path = Path(root) / file
                        
                        try:
                            metrics = self._analyze_java_file_with_cached_metrics(file_path, ck_results, unified_results)
                            if metrics:
                                records.append(metrics)
                        except Exception as e:
                            logger.warning(f"Error analyzing {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error extracting Java metrics: {e}")
        
        return records
    
    def _analyze_java_file_with_cached_metrics(self, file_path: Path, ck_results: Dict, unified_results: Dict) -> Optional[Dict]:
        """Analyze a single Java file using pre-computed metrics from repository analysis"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            lines = code.split('\n')
            
            # Basic size metrics
            loc = len([l for l in lines if l.strip()])
            comment_lines = len([l for l in lines if l.strip().startswith(('//', '/*', '*', '*/'))])
            blank_lines = len([l for l in lines if not l.strip()])
            
            # Count classes, methods, fields using regex
            num_classes = len(re.findall(r'\b(public\s+)?class\s+\w+', code))
            num_interfaces = len(re.findall(r'\b(public\s+)?interface\s+\w+', code))
            
            # Count methods
            method_pattern = r'\b(public|private|protected|static)?\s+(static\s+)?(synchronized\s+)?(?:void|int|String|boolean|double|long|float|[\w<>[\]\.]+)\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
            num_methods = len(re.findall(method_pattern, code))
            
            # Count fields/attributes
            field_pattern = r'^\s+(public|private|protected|static)?\s+(?:static\s+)?(?:final\s+)?[\w<>[\]\.]+\s+\w+\s*(?:=|;)'
            num_fields = len(re.findall(field_pattern, code, re.MULTILINE))
            
            # Calculate cyclomatic complexity (simplified)
            complexity_keywords = code.count('if ') + code.count('for ') + code.count('while ') + \
                                code.count('case ') + code.count('catch ') + code.count('&&') + code.count('||')
            cyclomatic_complexity = max(1, complexity_keywords)
            
            # Count nested levels (approximate)
            max_nesting = 0
            current_nesting = 0
            for line in lines:
                open_braces = line.count('{')
                close_braces = line.count('}')
                current_nesting += open_braces - close_braces
                max_nesting = max(max_nesting, current_nesting)
            
            # Find CK metrics for this file from pre-computed results
            ck_metrics = None
            file_path_str = str(file_path)
            for class_name, metrics in ck_results.items():
                if hasattr(metrics, 'file_path') and metrics.file_path == file_path_str:
                    ck_metrics = metrics
                    break
            
            # Find unified metrics for this file from pre-computed results
            unified_metrics = None
            for class_name, metrics in unified_results.items():
                if hasattr(metrics, 'file_path') and metrics.file_path == file_path_str:
                    unified_metrics = metrics
                    break
            
            # Build comprehensive metrics record with all 34 metrics
            record = {
                "type": "comprehensive_java_metrics",
                "file": str(file_path.relative_to(self.file_path) if self.file_path.is_dir() else self.file_path.parent),
                "project": self.file_path.name if self.file_path.is_dir() else self.file_path.stem,
                "language": "java",
                
                # SIZE METRICS (5)
                "loc": loc,
                "comment_lines": comment_lines,
                "blank_lines": blank_lines,
                "total_lines": len(lines),
                "lines_of_code_actual": loc - comment_lines - blank_lines,
                
                # COMPLEXITY METRICS (4)
                "cyclomatic_complexity": cyclomatic_complexity,
                "max_nesting_depth": max_nesting,
                "avg_nesting_depth": max_nesting / max(1, num_methods),
                "cognitive_complexity": cyclomatic_complexity * 1.2,  # Approximation
                
                # CK METRICS (6)
                "wmc": ck_metrics.wmc if ck_metrics else num_methods,
                "dit": ck_metrics.dit if ck_metrics else 1,
                "noc": ck_metrics.noc if ck_metrics else 0,
                "cbo": ck_metrics.cbo if ck_metrics else num_classes,
                "rfc": ck_metrics.rfc if ck_metrics else num_methods,
                "lcom": ck_metrics.lcom if ck_metrics else 0.0,
                
                # STRUCTURE METRICS (7)
                "num_classes": num_classes,
                "num_interfaces": num_interfaces,
                "num_methods": num_methods,
                "num_fields": num_fields,
                "num_public_methods": len(re.findall(r'\bpublic\s+(?:static\s+)?(?:void|int|String|boolean|[\w<>[\]\.]+)\s+\w+\s*\(', code)),
                "num_private_methods": len(re.findall(r'\bprivate\s+(?:static\s+)?(?:void|int|String|boolean|[\w<>[\]\.]+)\s+\w+\s*\(', code)),
                "num_static_methods": len(re.findall(r'\b(?:public|private|protected)?\s+static\s+(?:void|int|String|boolean|[\w<>[\]\.]+)\s+\w+\s*\(', code)),
                
                # QUALITY METRICS (5)
                "comment_ratio": comment_lines / max(1, loc),
                "has_comments": comment_lines > 0,
                "avg_method_loc": (loc - comment_lines) / max(1, num_methods),
                "max_method_loc": (loc - comment_lines) // max(1, num_methods) + 10,  # Approximation
                "maintainability_index": unified_metrics.maintainability.maintainability_index if unified_metrics and unified_metrics.maintainability else 50.0,
                
                # DEFECT METRICS (4)
                "has_defect": 0,  # Would need external data
                "defect_type": "none",
                "num_bugs": 0,
                "bug_severity": "none",
                
                # COUPLING METRICS (3)
                "afferent_coupling": ck_metrics.cbo if ck_metrics else num_classes,
                "efferent_coupling": ck_metrics.cbo if ck_metrics else num_classes,
                "instability": (ck_metrics.cbo if ck_metrics else num_classes) / max(1, (ck_metrics.cbo if ck_metrics else num_classes) + num_methods),
                
                # Additional unified metrics if available
                "halstead_volume": unified_metrics.halstead.volume if unified_metrics and unified_metrics.halstead else 0,
                "halstead_difficulty": unified_metrics.halstead.difficulty if unified_metrics and unified_metrics.halstead else 0,
                "technical_debt_hours": unified_metrics.maintainability.technical_debt_hours if unified_metrics and unified_metrics.maintainability else 0,
                "code_smells": len(unified_metrics.maintainability.code_smells) if unified_metrics and unified_metrics.maintainability else 0,
            }
            
            return record
        
        except Exception as e:
            logger.error(f"Error analyzing Java file {file_path}: {e}")
            return None
    
    def _analyze_java_file(self, file_path: Path) -> Optional[Dict]:
        """Analyze a single Java file and extract comprehensive metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            lines = code.split('\n')
            
            # Basic size metrics
            loc = len([l for l in lines if l.strip()])
            comment_lines = len([l for l in lines if l.strip().startswith(('//', '/*', '*', '*/'))])
            blank_lines = len([l for l in lines if not l.strip()])
            
            # Count classes, methods, fields
            num_classes = len(re.findall(r'\b(public\s+)?class\s+\w+', code))
            num_interfaces = len(re.findall(r'\b(public\s+)?interface\s+\w+', code))
            
            # Count methods
            method_pattern = r'\b(public|private|protected|static)?\s+(static\s+)?(synchronized\s+)?(?:void|int|String|boolean|double|long|float|[\w<>[\]\.]+)\s+\w+\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{'
            num_methods = len(re.findall(method_pattern, code))
            
            # Count fields/attributes
            field_pattern = r'^\s+(public|private|protected|static)?\s+(?:static\s+)?(?:final\s+)?[\w<>[\]\.]+\s+\w+\s*(?:=|;)'
            num_fields = len(re.findall(field_pattern, code, re.MULTILINE))
            
            # Calculate cyclomatic complexity (simplified)
            complexity_keywords = code.count('if ') + code.count('for ') + code.count('while ') + \
                                code.count('case ') + code.count('catch ') + code.count('&&') + code.count('||')
            cyclomatic_complexity = max(1, complexity_keywords)
            
            # Count nested levels (approximate)
            max_nesting = 0
            current_nesting = 0
            for line in lines:
                open_braces = line.count('{')
                close_braces = line.count('}')
                current_nesting += open_braces - close_braces
                max_nesting = max(max_nesting, current_nesting)
            
            # Try to get CK metrics using the analyzer
            ck_metrics = None
            try:
                # Create a temporary analyzer for this file
                temp_analyzer = CKMetricsAnalyzer(str(file_path.parent))
                ck_results = temp_analyzer.analyze_repository()
                
                # Find metrics for this file
                for class_name, metrics in ck_results.items():
                    if metrics.file_path == str(file_path):
                        ck_metrics = metrics
                        break
            except Exception as e:
                logger.debug(f"Could not calculate CK metrics for {file_path}: {e}")
            
            # Try to get unified metrics
            unified_metrics = None
            try:
                temp_unified = UnifiedMetricsAnalyzer(str(file_path.parent))
                unified_results = temp_unified.analyze_all()
                
                # Find metrics for this file
                for class_name, metrics in unified_results.items():
                    if metrics.file_path == str(file_path):
                        unified_metrics = metrics
                        break
            except Exception as e:
                logger.debug(f"Could not calculate unified metrics for {file_path}: {e}")
            
            # Build comprehensive metrics record with all 34 metrics
            record = {
                "type": "comprehensive_java_metrics",
                "file": str(file_path.relative_to(self.file_path) if self.file_path.is_dir() else self.file_path.parent),
                "project": self.file_path.name if self.file_path.is_dir() else self.file_path.stem,
                "language": "java",
                
                # SIZE METRICS (5)
                "loc": loc,
                "comment_lines": comment_lines,
                "blank_lines": blank_lines,
                "total_lines": len(lines),
                "lines_of_code_actual": loc - comment_lines - blank_lines,
                
                # COMPLEXITY METRICS (4)
                "cyclomatic_complexity": cyclomatic_complexity,
                "max_nesting_depth": max_nesting,
                "avg_nesting_depth": max_nesting / max(1, num_methods),
                "cognitive_complexity": cyclomatic_complexity * 1.2,  # Approximation
                
                # CK METRICS (6)
                "wmc": ck_metrics.wmc if ck_metrics else num_methods,
                "dit": ck_metrics.dit if ck_metrics else 1,
                "noc": ck_metrics.noc if ck_metrics else 0,
                "cbo": ck_metrics.cbo if ck_metrics else num_classes,
                "rfc": ck_metrics.rfc if ck_metrics else num_methods,
                "lcom": ck_metrics.lcom if ck_metrics else 0.0,
                
                # STRUCTURE METRICS (7)
                "num_classes": num_classes,
                "num_interfaces": num_interfaces,
                "num_methods": num_methods,
                "num_fields": num_fields,
                "num_public_methods": len(re.findall(r'\bpublic\s+(?:static\s+)?(?:void|int|String|boolean|[\w<>[\]\.]+)\s+\w+\s*\(', code)),
                "num_private_methods": len(re.findall(r'\bprivate\s+(?:static\s+)?(?:void|int|String|boolean|[\w<>[\]\.]+)\s+\w+\s*\(', code)),
                "num_static_methods": len(re.findall(r'\b(?:public|private|protected)?\s+static\s+(?:void|int|String|boolean|[\w<>[\]\.]+)\s+\w+\s*\(', code)),
                
                # QUALITY METRICS (5)
                "comment_ratio": comment_lines / max(1, loc),
                "has_comments": comment_lines > 0,
                "avg_method_loc": (loc - comment_lines) / max(1, num_methods),
                "max_method_loc": (loc - comment_lines) // max(1, num_methods) + 10,  # Approximation
                "maintainability_index": unified_metrics.maintainability.maintainability_index if unified_metrics and unified_metrics.maintainability else 50.0,
                
                # DEFECT METRICS (4)
                "has_defect": 0,  # Would need external data
                "defect_type": "none",
                "num_bugs": 0,
                "bug_severity": "none",
                
                # COUPLING METRICS (3)
                "afferent_coupling": ck_metrics.cbo if ck_metrics else num_classes,
                "efferent_coupling": ck_metrics.cbo if ck_metrics else num_classes,
                "instability": (ck_metrics.cbo if ck_metrics else num_classes) / max(1, (ck_metrics.cbo if ck_metrics else num_classes) + num_methods),
                
                # Additional unified metrics if available
                "halstead_volume": unified_metrics.halstead.volume if unified_metrics and unified_metrics.halstead else 0,
                "halstead_difficulty": unified_metrics.halstead.difficulty if unified_metrics and unified_metrics.halstead else 0,
                "technical_debt_hours": unified_metrics.maintainability.technical_debt_hours if unified_metrics and unified_metrics.maintainability else 0,
                "code_smells": len(unified_metrics.maintainability.code_smells) if unified_metrics and unified_metrics.maintainability else 0,
            }
            
            return record
        
        except Exception as e:
            logger.error(f"Error analyzing Java file {file_path}: {e}")
            return None
    
    def _extract_from_csv(self, file_path: Optional[Path] = None) -> List[Dict]:
        """Extract from CSV file"""
        records = []
        
        if file_path is None:
            file_path = self.file_path
        
        try:
            with open(file_path) as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    record = {
                        "type": "promise_metrics",
                        "project": file_path.stem,
                    }
                    
                    # Process metrics
                    for key, value in row.items():
                        try:
                            # Try to convert to float for numeric metrics
                            record[key] = float(value)
                        except (ValueError, TypeError):
                            # Keep as string if conversion fails
                            record[key] = value
                    
                    # Check for defect label
                    defect_label = row.get("defects") or row.get("buggy") or row.get("bugs")
                    if defect_label:
                        record["has_defect"] = defect_label.lower() in ["yes", "true", "1", "defective"]
                    
                    records.append(record)
        
        except Exception as e:
            logger.error(f"Error reading CSV {file_path}: {e}")
        
        return records
    
    def _extract_from_arff(self, file_path: Optional[Path] = None) -> List[Dict]:
        """Extract from ARFF file (Weka format)"""
        records = []
        
        if file_path is None:
            file_path = self.file_path
        
        try:
            lines = file_path.read_text().split('\n')
            
            # Parse header
            attributes = []
            in_data = False
            
            for line in lines:
                line = line.strip()
                
                if line.lower().startswith("@attribute"):
                    # Extract attribute name
                    parts = line.split()
                    attr_name = parts[1]
                    attributes.append(attr_name)
                
                elif line.lower() == "@data":
                    in_data = True
                    continue
                
                elif in_data and line and not line.startswith("%"):
                    # Parse data record
                    values = line.split(',')
                    if len(values) == len(attributes):
                        record = {
                            "type": "promise_metrics",
                            "project": file_path.stem,
                        }
                        
                        for attr, value in zip(attributes, values):
                            try:
                                record[attr] = float(value.strip())
                            except (ValueError, TypeError):
                                record[attr] = value.strip()
                        
                        records.append(record)
        
        except Exception as e:
            logger.error(f"Error reading ARFF {file_path}: {e}")
        
        return records
    
    def _extract_from_json(self, file_path: Optional[Path] = None) -> List[Dict]:
        """Extract from JSON file"""
        records = []
        
        if file_path is None:
            file_path = self.file_path
        
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    item["type"] = "promise_metrics"
                    records.append(item)
            
            elif isinstance(data, dict) and "records" in data:
                for item in data["records"]:
                    item["type"] = "promise_metrics"
                    records.append(item)
        
        except Exception as e:
            logger.error(f"Error reading JSON {file_path}: {e}")
        
        return records

class BugsJarExtractor(FileExtractor):
    """Extractor for Bugs.jar dataset"""
    
    def __init__(self, file_path: str, config: Optional[Dict] = None):
        """Initialize Bugs.jar extractor"""
        super().__init__(file_path, config)
        self.dataset_type = "bugs_jar"
    
    def extract(self) -> List[Dict]:
        """
        Extract Bugs.jar format data
        Java class information, bug locations, test cases
        """
        logger.info(f"Extracting Bugs.jar data from {self.file_path}")
        
        extracted = []
        
        # For JAR files, we need to parse them
        if self.file_path.suffix == ".jar":
            extracted = self._extract_from_jar()
        
        # Or parse metadata JSON
        elif self.file_path.suffix == ".json":
            extracted = self._extract_from_metadata()
        
        # Or parse CSV with class information
        elif self.file_path.suffix == ".csv":
            extracted = self._extract_from_csv()
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "bugs_jar_structure")
        
        logger.info(f"Extracted {len(extracted)} Bugs.jar records")
        return extracted
    
    def _extract_from_jar(self) -> List[Dict]:
        """Extract from JAR file"""
        records = []
        
        try:
            import zipfile
            with zipfile.ZipFile(self.file_path) as jar:
                for name in jar.namelist():
                    if name.endswith(".class"):
                        # Parse class information
                        record = {
                            "type": "bugs_jar_class",
                            "class_path": name,
                            "class_name": name.replace("/", ".").replace(".class", ""),
                        }
                        records.append(record)
        
        except Exception as e:
            logger.error(f"Error reading JAR: {e}")
        
        return records
    
    def _extract_from_metadata(self) -> List[Dict]:
        """Extract from metadata JSON"""
        records = []
        
        try:
            with open(self.file_path) as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for item in data:
                    item["type"] = "bugs_jar_metadata"
                    records.append(item)
        
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
        
        return records
    
    def _extract_from_csv(self) -> List[Dict]:
        """Extract from CSV file"""
        records = []
        
        try:
            with open(self.file_path) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record = {
                        "type": "bugs_jar_class_info",
                    }
                    record.update(row)
                    records.append(record)
        
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
        
        return records
