"""
Complete Usage Examples
Dataset Management System ব্যবহারের সম্পূর্ণ উদাহরণ
"""

# ==================== EXAMPLE 1: CLI ব্যবহার করে ====================

"""
Example 1.1: সম্পূর্ণ workflow (CLI)
"""

import subprocess
import os

# ডেটাসেট লিস্ট দেখুন
os.system("python -m cli.main list-datasets")

# Defects4J ডেটা এক্সট্রাক্ট করুন
os.system("""
python -m cli.main extract \
  --dataset-type defects4j \
  --source /path/to/defects4j \
  --output ./data/defects4j_raw.json \
  --format json
""")

# ডেটা প্রসেস করুন
os.system("""
python -m cli.main process \
  --input ./data/defects4j_raw.json \
  --output ./data/defects4j_processed.json \
  --normalize-code \
  --clean-text \
  --validate \
  --remove-duplicates
""")

# বাগ সেভেরিটি লেবেল করুন
os.system("""
python -m cli.main label \
  --input ./data/defects4j_processed.json \
  --output ./data/defects4j_labeled.json \
  --label-type bug_severity
""")

# Neo4j-এ ইমপোর্ট করুন
os.system("""
python -m cli.main import-to-neo4j \
  --input ./data/defects4j_labeled.json \
  --dataset-name "Defects4J Dataset" \
  --project-id "defects4j_001"
""")

# সিস্টেম স্ট্যাটাস চেক করুন
os.system("python -m cli.main status")


# ==================== EXAMPLE 2: Python Code ব্যবহার করে ====================

"""
Example 2.1: এক্সট্রাকশন থেকে Neo4j পর্যন্ত সম্পূর্ণ pipeline
"""

import json
from pathlib import Path

# ইমপোর্ট করুন
from extractors.factory import create_extractor
from processors.base_processor import ProcessingPipeline, CodeNormalizer, TextCleaner, DuplicateRemover
from labelers.labeler import BugSeverityLabeler, MultiLabelClassifier
from neo4j.manager import get_neo4j_manager

def complete_workflow(dataset_type, source_path):
    """সম্পূর্ণ workflow সম্পাদন করুন"""
    
    print(f"\n{'='*60}")
    print(f"Processing: {dataset_type}")
    print(f"Source: {source_path}")
    print(f"{'='*60}\n")
    
    # Step 1: Extract
    print("[STEP 1] Extracting data...")
    extractor = create_extractor(dataset_type, source_path)
    raw_records = extractor.extract()
    print(f"✓ Extracted {len(raw_records)} records")
    print(f"  Metadata: {extractor.get_metadata()}")
    
    # Step 2: Process
    print("\n[STEP 2] Processing data...")
    pipeline = ProcessingPipeline()
    pipeline.add_processor(CodeNormalizer())
    pipeline.add_processor(TextCleaner())
    pipeline.add_processor(DuplicateRemover())
    
    processed_records = pipeline.process(raw_records)
    print(f"✓ Processed {len(processed_records)} records")
    stats = pipeline.get_stats()
    for processor_name, processor_stats in stats.items():
        print(f"  {processor_name}: {processor_stats}")
    
    # Step 3: Label
    print("\n[STEP 3] Labeling data...")
    severity_labeler = BugSeverityLabeler()
    labeled_records = severity_labeler.label(processed_records)
    print(f"✓ Labeled {len(labeled_records)} records")
    print(f"  Distribution: {severity_labeler.get_stats()}")
    
    # Add multi-labels
    multi_labeler = MultiLabelClassifier()
    labeled_records = multi_labeler.label(labeled_records)
    print(f"  Multi-labels: {multi_labeler.get_stats()}")
    
    # Step 4: Save to file
    print("\n[STEP 4] Saving to file...")
    output_file = Path(f"./data/{dataset_type}_complete.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(labeled_records, f, indent=2, default=str)
    print(f"✓ Saved to {output_file}")
    
    # Step 5: Import to Neo4j
    print("\n[STEP 5] Importing to Neo4j...")
    neo4j = get_neo4j_manager()
    
    imported_count = 0
    for record in labeled_records:
        try:
            node_type = record.get("type", "Record").replace("_", "").title()
            neo4j.create_node(node_type, record)
            imported_count += 1
        except Exception as e:
            print(f"  Warning: Failed to import record: {e}")
    
    print(f"✓ Imported {imported_count}/{len(labeled_records)} records to Neo4j")
    
    # Step 6: Display statistics
    print("\n[STEP 6] Database statistics...")
    neo4j_stats = neo4j.get_statistics()
    print(f"  Total items: {sum(neo4j_stats.values())}")
    for node_type, count in sorted(neo4j_stats.items()):
        print(f"    {node_type}: {count}")
    
    print(f"\n{'='*60}")
    print("✓ Workflow completed successfully!")
    print(f"{'='*60}\n")
    
    return {
        "dataset_type": dataset_type,
        "raw_records": len(raw_records),
        "processed_records": len(processed_records),
        "labeled_records": len(labeled_records),
        "imported_records": imported_count,
        "output_file": str(output_file)
    }

# ব্যবহার করুন
if __name__ == "__main__":
    result = complete_workflow("defects4j", "/path/to/defects4j")
    print("\nResult Summary:")
    print(json.dumps(result, indent=2))


# ==================== EXAMPLE 3: মাল্টিপল ডেটাসেট প্রসেসিং ====================

"""
Example 3.1: একাধিক ডেটাসেট প্রসেস করুন
"""

from extractors.factory import SUPPORTED_DATASETS

def process_all_datasets(sources_map):
    """
    multiple datasets প্রসেস করুন
    
    sources_map: {dataset_type: source_path}
    """
    
    results = []
    
    for dataset_type, source_path in sources_map.items():
        try:
            print(f"\n{'='*60}")
            print(f"Processing: {dataset_type}")
            print(f"{'='*60}")
            
            result = complete_workflow(dataset_type, source_path)
            results.append(result)
        
        except Exception as e:
            print(f"✗ Error processing {dataset_type}: {e}")
            results.append({
                "dataset_type": dataset_type,
                "error": str(e)
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for result in results:
        if "error" in result:
            print(f"✗ {result['dataset_type']}: ERROR - {result['error']}")
        else:
            print(f"✓ {result['dataset_type']}: {result['processed_records']} records processed")
    
    return results

# ব্যবহার করুন
if __name__ == "__main__":
    sources = {
        "defects4j": "/path/to/defects4j",
        "codesearchnet": "/path/to/codesearchnet",
        "promise": "/path/to/promise_data.csv",
    }
    
    results = process_all_datasets(sources)


# ==================== EXAMPLE 4: কাস্টম Processing Pipeline ====================

"""
Example 4.1: কাস্টম processor সহ pipeline
"""

from processors.base_processor import BaseProcessor, ProcessingPipeline

class CustomLowercaseProcessor(BaseProcessor):
    """কাস্টম processor: সব টেক্সট lowercase করুন"""
    
    def process(self, records):
        for record in records:
            for key, value in record.items():
                if isinstance(value, str):
                    record[key] = value.lower()
        
        self.processed_data = records
        self.set_stat("total_records", len(records))
        return records

# ব্যবহার করুন
def custom_pipeline_example(raw_records):
    """কাস্টম pipeline উদাহরণ"""
    
    pipeline = ProcessingPipeline()
    pipeline.add_processor(CodeNormalizer())
    pipeline.add_processor(CustomLowercaseProcessor())
    pipeline.add_processor(TextCleaner())
    
    processed = pipeline.process(raw_records)
    return processed


# ==================== EXAMPLE 5: Neo4j Querying ====================

"""
Example 5.1: Processed data থেকে query করুন
"""

from neo4j.manager import get_neo4j_manager

def query_neo4j_examples():
    """Neo4j query উদাহরণ"""
    
    neo4j = get_neo4j_manager()
    
    # Query 1: সব critical bugs খুঁজুন
    print("\n[Query 1] Critical bugs:")
    critical_bugs = neo4j.find_nodes("Bug", {"severity": "critical"})
    for bug in critical_bugs[:5]:
        print(f"  - {bug.get('title', 'N/A')}")
    
    # Query 2: জটিল কোড খুঁজুন
    print("\n[Query 2] Complex code snippets:")
    complex_code = neo4j.find_nodes("CodeSnippet", {"complexity": "very_complex"})
    print(f"  Found {len(complex_code)} complex snippets")
    
    # Query 3: কাস্টম Cypher query
    print("\n[Query 3] Custom Cypher:")
    query = """
    MATCH (p:Project)-[HAS_BUG]->(b:Bug)
    WHERE b.severity = 'high'
    RETURN p.name as project, count(b) as bug_count
    ORDER BY bug_count DESC
    LIMIT 5
    """
    results = neo4j.query(query)
    for record in results:
        print(f"  {record[0]}: {record[1]} bugs")
    
    # Query 4: Related bugs খুঁজুন
    print("\n[Query 4] Related bugs:")
    bugs = neo4j.find_relationships("RELATED_TO", "Bug", "Bug")
    print(f"  Found {len(bugs)} related bug pairs")


# ==================== EXAMPLE 6: Data Export ====================

"""
Example 6.1: বিভিন্ন ফরম্যাটে export করুন
"""

def export_examples(records, output_dir="./exports"):
    """বিভিন্ন ফরম্যাটে export করুন"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export as JSON
    json_file = output_dir / "data.json"
    with open(json_file, 'w') as f:
        json.dump(records, f, indent=2, default=str)
    print(f"✓ Exported JSON: {json_file}")
    
    # Export as CSV
    csv_file = output_dir / "data.csv"
    import csv
    if records:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
    print(f"✓ Exported CSV: {csv_file}")
    
    # Export as JSONL
    jsonl_file = output_dir / "data.jsonl"
    with open(jsonl_file, 'w') as f:
        for record in records:
            f.write(json.dumps(record, default=str) + '\n')
    print(f"✓ Exported JSONL: {jsonl_file}")
    
    # Export as Parquet (যদি pandas/pyarrow installed হয়)
    try:
        import pandas as pd
        df = pd.DataFrame(records)
        parquet_file = output_dir / "data.parquet"
        df.to_parquet(parquet_file)
        print(f"✓ Exported Parquet: {parquet_file}")
    except ImportError:
        print("⚠ Parquet export skipped (pandas/pyarrow not installed)")


# ==================== EXAMPLE 7: Batch Processing ====================

"""
Example 7.1: বড় ডেটাসেট batch তে প্রসেস করুন
"""

from utils.helpers import batch_list

def batch_processing_example(records, batch_size=100):
    """Batch processing উদাহরণ"""
    
    batches = batch_list(records, batch_size)
    
    print(f"Processing {len(records)} records in {len(batches)} batches...")
    
    neo4j = get_neo4j_manager()
    total_imported = 0
    
    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}/{len(batches)}...", end=' ')
        
        batch_imported = 0
        for record in batch:
            try:
                node_type = record.get("type", "Record").replace("_", "").title()
                neo4j.create_node(node_type, record)
                batch_imported += 1
            except Exception as e:
                pass
        
        total_imported += batch_imported
        print(f"✓ ({batch_imported}/{len(batch)} imported)")
    
    print(f"\n✓ Total imported: {total_imported}/{len(records)}")


# ==================== EXAMPLE 8: Error Handling ====================

"""
Example 8.1: Error handling সহ robust workflow
"""

import traceback
from utils.logger import setup_logger

logger = setup_logger(__name__)

def robust_workflow(dataset_type, source_path, max_retries=3):
    """Error handling সহ workflow"""
    
    for attempt in range(max_retries):
        try:
            print(f"\n[Attempt {attempt + 1}/{max_retries}]")
            
            # Validate source
            from extractors.factory import validate_source
            if not validate_source(dataset_type, source_path):
                raise ValueError(f"Invalid source: {source_path}")
            
            # Extract
            extractor = create_extractor(dataset_type, source_path)
            records = extractor.extract()
            
            if not records:
                raise ValueError("No records extracted")
            
            # Process
            pipeline = ProcessingPipeline()
            pipeline.add_processor(CodeNormalizer())
            pipeline.add_processor(TextCleaner())
            
            processed = pipeline.process(records)
            
            if not processed:
                raise ValueError("No records after processing")
            
            # Label
            labeler = BugSeverityLabeler()
            labeled = labeler.label(processed)
            
            print(f"✓ Successfully processed {len(labeled)} records")
            return labeled
        
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                print(f"\n✗ All attempts failed")
                raise
            
            import time
            wait_time = 2 ** attempt  # Exponential backoff
            print(f"  Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


# ==================== QUICK START ====================

"""
Quick Start: সবচেয়ে সহজ উপায়ে শুরু করুন
"""

if __name__ == "__main__":
    print("""
    Dataset Management System - Quick Start Examples
    
    1. CLI: python -m cli.main list-datasets
    2. Complete Workflow: python examples.py (run complete_workflow)
    3. GUI: python -m gui.app
    4. API: python -m api.server
    
    আরও তথ্য: docs/README.md এবং docs/ARCHITECTURE.md দেখুন
    """)
