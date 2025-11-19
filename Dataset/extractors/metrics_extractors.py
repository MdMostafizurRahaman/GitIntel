"""
PROMISE Repository Dataset Extractor
Software engineering datasets for metrics and bug prediction
"""

from typing import Dict, List, Optional
import logging
from pathlib import Path
import csv
import json
from extractors.base_extractor import FileExtractor

logger = logging.getLogger(__name__)

class PROMISEExtractor(FileExtractor):
    """Extractor for PROMISE Repository dataset"""
    
    def __init__(self, file_path: str, config: Optional[Dict] = None):
        """Initialize PROMISE extractor"""
        super().__init__(file_path, config)
        self.dataset_type = "promise"
    
    def extract(self) -> List[Dict]:
        """
        Extract PROMISE format data
        Software metrics and defect labels
        """
        logger.info(f"Extracting PROMISE data from {self.file_path}")
        
        extracted = []
        
        if self.file_path.suffix == ".csv":
            extracted = self._extract_from_csv()
        elif self.file_path.suffix == ".arff":
            extracted = self._extract_from_arff()
        elif self.file_path.suffix == ".json":
            extracted = self._extract_from_json()
        
        self.extracted_data = extracted
        self.set_metadata("record_count", len(extracted))
        self.set_metadata("extraction_method", "promise_structure")
        self.set_metadata("metrics_count", len(extracted[0].keys()) - 3 if extracted else 0)
        
        logger.info(f"Extracted {len(extracted)} PROMISE records")
        return extracted
    
    def _extract_from_csv(self) -> List[Dict]:
        """Extract from CSV file"""
        records = []
        
        try:
            with open(self.file_path) as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    record = {
                        "type": "promise_metrics",
                        "project": self.file_path.stem,
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
            logger.error(f"Error reading CSV: {e}")
        
        return records
    
    def _extract_from_arff(self) -> List[Dict]:
        """Extract from ARFF file (Weka format)"""
        records = []
        
        try:
            lines = self.file_path.read_text().split('\n')
            
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
                            "project": self.file_path.stem,
                        }
                        
                        for attr, value in zip(attributes, values):
                            try:
                                record[attr] = float(value.strip())
                            except (ValueError, TypeError):
                                record[attr] = value.strip()
                        
                        records.append(record)
        
        except Exception as e:
            logger.error(f"Error reading ARFF: {e}")
        
        return records
    
    def _extract_from_json(self) -> List[Dict]:
        """Extract from JSON file"""
        records = []
        
        try:
            with open(self.file_path) as f:
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
            logger.error(f"Error reading JSON: {e}")
        
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
