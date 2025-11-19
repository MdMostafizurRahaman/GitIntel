"""
FastAPI Server for Website Integration
RESTful API for dataset management and access
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

from config.config import API_CONFIG, EXPORT_DIR, DATA_DIR
from extractors.factory import create_extractor, SUPPORTED_DATASETS, validate_source
from processors.base_processor import ProcessingPipeline, CodeNormalizer, TextCleaner, DuplicateRemover
from labelers.labeler import BugSeverityLabeler, CodeComplexityLabeler, FeatureLabelClassifier
from neo4j.manager import get_neo4j_manager

# Initialize FastAPI app
app = FastAPI(
    title="Dataset Management API",
    description="API for managing and accessing datasets",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

from pydantic import BaseModel

class DatasetInfo(BaseModel):
    """Dataset information"""
    id: str
    name: str
    description: str
    type: str

class ExtractionRequest(BaseModel):
    """Extraction request"""
    dataset_type: str
    source: str
    output_format: str = "json"

class ProcessingRequest(BaseModel):
    """Processing request"""
    input_file: str
    normalize_code: bool = False
    clean_text: bool = False
    remove_duplicates: bool = False

class LabelingRequest(BaseModel):
    """Labeling request"""
    input_file: str
    label_type: str

class ExportRequest(BaseModel):
    """Export request"""
    input_file: str
    output_format: str
    output_file: str

# ==================== ENDPOINTS ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/datasets")
async def list_datasets():
    """List all supported datasets"""
    return {
        "datasets": [
            {
                "id": key,
                "name": info["name"],
                "description": info["description"],
                "type": info["type"]
            }
            for key, info in SUPPORTED_DATASETS.items()
        ]
    }

@app.get("/api/datasets/{dataset_id}")
async def get_dataset_info(dataset_id: str):
    """Get information about specific dataset"""
    if dataset_id not in SUPPORTED_DATASETS:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    info = SUPPORTED_DATASETS[dataset_id]
    return {
        "id": dataset_id,
        "name": info["name"],
        "description": info["description"],
        "type": info["type"]
    }

@app.post("/api/extract")
async def extract_data(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """Extract data from source"""
    
    # Validate input
    if request.dataset_type not in SUPPORTED_DATASETS:
        raise HTTPException(status_code=400, detail="Invalid dataset type")
    
    if not validate_source(request.dataset_type, request.source):
        raise HTTPException(status_code=400, detail="Invalid or inaccessible source")
    
    try:
        # Extract
        extractor = create_extractor(request.dataset_type, request.source)
        records = extractor.extract()
        
        # Save to file
        output_file = DATA_DIR / f"extracted_{datetime.now().timestamp()}.json"
        with open(output_file, 'w') as f:
            json.dump(records, f, indent=2, default=str)
        
        return {
            "status": "success",
            "record_count": len(records),
            "output_file": str(output_file),
            "metadata": extractor.get_metadata()
        }
    
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_data(request: ProcessingRequest):
    """Process extracted data"""
    
    input_path = Path(request.input_file)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")
    
    try:
        # Load data
        with open(input_path) as f:
            records = json.load(f)
        
        # Create processing pipeline
        pipeline = ProcessingPipeline()
        
        if request.normalize_code:
            pipeline.add_processor(CodeNormalizer())
        if request.clean_text:
            pipeline.add_processor(TextCleaner())
        if request.remove_duplicates:
            pipeline.add_processor(DuplicateRemover())
        
        # Process
        processed = pipeline.process(records)
        
        # Save results
        output_file = DATA_DIR / f"processed_{datetime.now().timestamp()}.json"
        with open(output_file, 'w') as f:
            json.dump(processed, f, indent=2, default=str)
        
        return {
            "status": "success",
            "input_count": len(records),
            "output_count": len(processed),
            "output_file": str(output_file),
            "stats": pipeline.get_stats()
        }
    
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/label")
async def label_data(request: LabelingRequest):
    """Label dataset records"""
    
    input_path = Path(request.input_file)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")
    
    try:
        # Load data
        with open(input_path) as f:
            records = json.load(f)
        
        # Create labeler
        if request.label_type == "bug_severity":
            labeler = BugSeverityLabeler()
        elif request.label_type == "code_complexity":
            labeler = CodeComplexityLabeler()
        elif request.label_type == "feature_type":
            labeler = FeatureLabelClassifier()
        else:
            raise HTTPException(status_code=400, detail="Unknown label type")
        
        # Label
        labeled = labeler.label(records)
        
        # Save results
        output_file = DATA_DIR / f"labeled_{datetime.now().timestamp()}.json"
        with open(output_file, 'w') as f:
            json.dump(labeled, f, indent=2, default=str)
        
        return {
            "status": "success",
            "record_count": len(labeled),
            "output_file": str(output_file),
            "label_distribution": labeler.get_stats()
        }
    
    except Exception as e:
        logger.error(f"Labeling error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export")
async def export_data(request: ExportRequest):
    """Export data in specified format"""
    
    input_path = Path(request.input_file)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")
    
    try:
        # Load data
        with open(input_path) as f:
            records = json.load(f)
        
        output_path = Path(request.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export based on format
        if request.output_format.lower() == "json":
            with open(output_path, 'w') as f:
                json.dump(records, f, indent=2, default=str)
        
        elif request.output_format.lower() == "csv":
            import csv
            if records:
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)
        
        elif request.output_format.lower() == "jsonl":
            with open(output_path, 'w') as f:
                for record in records:
                    f.write(json.dumps(record, default=str) + '\n')
        
        else:
            raise HTTPException(status_code=400, detail="Unknown export format")
        
        return {
            "status": "success",
            "record_count": len(records),
            "output_file": str(output_path),
            "format": request.output_format
        }
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/neo4j/stats")
async def get_neo4j_stats():
    """Get Neo4j database statistics"""
    
    try:
        neo4j = get_neo4j_manager()
        stats = neo4j.get_statistics()
        
        return {
            "status": "connected",
            "statistics": stats,
            "total_items": sum(stats.values())
        }
    
    except Exception as e:
        logger.error(f"Neo4j error: {e}")
        raise HTTPException(status_code=500, detail="Neo4j connection failed")

@app.post("/api/neo4j/import")
async def import_to_neo4j(request: dict):
    """Import data to Neo4j"""
    
    input_file = request.get("input_file")
    dataset_name = request.get("dataset_name")
    
    if not input_file or not dataset_name:
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    input_path = Path(input_file)
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")
    
    try:
        # Load data
        with open(input_path) as f:
            records = json.load(f)
        
        # Import to Neo4j
        neo4j = get_neo4j_manager()
        
        imported_count = 0
        for record in records:
            try:
                node_type = record.get("type", "Record").replace("_", "").title()
                neo4j.create_node(node_type, record)
                imported_count += 1
            except Exception as e:
                logger.warning(f"Error importing record: {e}")
        
        return {
            "status": "success",
            "imported_count": imported_count,
            "total_records": len(records)
        }
    
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/{file_id}")
async def download_data(file_id: str):
    """Download processed data file"""
    
    file_path = DATA_DIR / f"{file_id}.json"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=f"{file_id}.json")

@app.get("/api/status")
async def system_status():
    """Get overall system status"""
    
    status = {
        "neo4j": "unknown",
        "storage": "unknown",
        "timestamp": datetime.now().isoformat()
    }
    
    # Check Neo4j
    try:
        neo4j = get_neo4j_manager()
        stats = neo4j.get_statistics()
        status["neo4j"] = "connected"
        status["neo4j_stats"] = stats
    except:
        status["neo4j"] = "disconnected"
    
    # Check storage
    try:
        available_space = Path("/").stat().st_size
        status["storage"] = "ok"
        status["data_dir_exists"] = DATA_DIR.exists()
    except:
        status["storage"] = "error"
    
    return status

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": "error"
        }
    )

# ==================== STARTUP/SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    logger.info("Starting Dataset Management API")
    logger.info(f"API running on {API_CONFIG['host']}:{API_CONFIG['port']}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown"""
    logger.info("Shutting down Dataset Management API")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        workers=API_CONFIG["workers"]
    )
