"""
PRODUCTION-GRADE DOCUMENT INGESTION PIPELINE
Chunking → Embedding → Indexing to ChromaDB

Processes real documents from data/processed/documents/APP-XXXXX/:
- PDFs: resume.pdf, employment_letter.pdf, credit_report.pdf, bank_statement.pdf
- XLSX: assets_liabilities.xlsx
- PNG: emirates_id.png (OCR)
- TXT: any text files

Author: FAANG-grade implementation
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
import openpyxl
from PIL import Image
import pytesseract
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DocumentProcessor:
    """Extract text from various document types"""
    
    @staticmethod
    def extract_pdf(file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"  ⚠️  PDF extraction failed for {file_path}: {e}")
            return ""
    
    @staticmethod
    def extract_xlsx(file_path: str) -> str:
        """Extract text from Excel files"""
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            text = ""
            for sheet in wb.worksheets:
                text += f"Sheet: {sheet.title}\n"
                for row in sheet.iter_rows(values_only=True):
                    text += " | ".join([str(cell) if cell is not None else "" for cell in row]) + "\n"
            wb.close()
            return text.strip()
        except Exception as e:
            print(f"  ⚠️  XLSX extraction failed for {file_path}: {e}")
            return ""
    
    @staticmethod
    def extract_png(file_path: str) -> str:
        """Extract text from images using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"  ⚠️  OCR extraction failed for {file_path}: {e}")
            return ""
    
    @staticmethod
    def extract_txt(file_path: str) -> str:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"  ⚠️  TXT extraction failed for {file_path}: {e}")
            return ""


class TextChunker:
    """Chunk text into optimal sizes for embedding"""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, doc_type: str, app_id: str) -> List[Dict]:
        """
        Chunk text with metadata
        
        Strategy:
        - Resumes: 512 chars, overlap 50 (preserve skills/experience context)
        - Bank statements: 256 chars, overlap 30 (transaction details)
        - Credit reports: 384 chars, overlap 40 (credit history)
        - Employment letters: 512 chars, overlap 50 (full context)
        - Assets/liabilities: 256 chars, overlap 30 (financial items)
        - Emirates ID: 128 chars, no overlap (structured data)
        """
        if not text:
            return []
        
        # Adjust chunk size based on document type
        if doc_type == "emirates_id":
            chunk_size = 128
            overlap = 0
        elif doc_type in ["bank_statement", "assets_liabilities"]:
            chunk_size = 256
            overlap = 30
        elif doc_type == "credit_report":
            chunk_size = 384
            overlap = 40
        else:  # resume, employment_letter
            chunk_size = 512
            overlap = 50
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            
            if chunk_text.strip():
                chunks.append({
                    "chunk_id": f"{app_id}_{doc_type}_{chunk_id}",
                    "text": chunk_text,
                    "app_id": app_id,
                    "doc_type": doc_type,
                    "chunk_index": chunk_id,
                    "total_chunks": -1  # Will update after all chunks created
                })
                chunk_id += 1
            
            start += (chunk_size - overlap)
        
        # Update total chunks
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)
        
        return chunks


class ChromaDBIndexer:
    """Index documents into ChromaDB with embeddings"""
    
    def __init__(self, db_path: str = "data/databases/chromadb"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✓ Embedding model loaded\n")
        
        # Document type to collection mapping
        self.collection_mapping = {
            "resume": "resumes",
            "employment_letter": "application_summaries",
            "credit_report": "income_patterns",
            "bank_statement": "income_patterns",
            "assets_liabilities": "income_patterns",
            "emirates_id": "application_summaries"
        }
    
    def clear_collections(self):
        """Clear existing collections"""
        print("Clearing existing ChromaDB collections...")
        try:
            collections = self.client.list_collections()
            for collection in collections:
                self.client.delete_collection(collection.name)
            print("✓ Collections cleared\n")
        except Exception as e:
            print(f"⚠️  Error clearing collections: {e}\n")
    
    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"⚠️  Error creating collection {name}: {e}")
            return None
    
    def index_chunks(self, chunks: List[Dict]):
        """Index chunks with embeddings"""
        if not chunks:
            return
        
        # Group chunks by target collection
        collection_chunks = {}
        for chunk in chunks:
            doc_type = chunk["doc_type"]
            target_collection = self.collection_mapping.get(doc_type, "application_summaries")
            
            if target_collection not in collection_chunks:
                collection_chunks[target_collection] = []
            collection_chunks[target_collection].append(chunk)
        
        # Index each collection
        for collection_name, coll_chunks in collection_chunks.items():
            collection = self.get_or_create_collection(collection_name)
            if not collection:
                continue
            
            # Prepare batch data
            texts = [c["text"] for c in coll_chunks]
            ids = [c["chunk_id"] for c in coll_chunks]
            metadatas = [{
                "app_id": c["app_id"],
                "doc_type": c["doc_type"],
                "chunk_index": c["chunk_index"],
                "total_chunks": c["total_chunks"]
            } for c in coll_chunks]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts).tolist()
            
            # Add to collection
            try:
                collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
            except Exception as e:
                print(f"  ⚠️  Error indexing to {collection_name}: {e}")


class DocumentIngestionPipeline:
    """Main pipeline: Extract → Chunk → Embed → Index"""
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.chunker = TextChunker()
        self.indexer = ChromaDBIndexer()
        
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "failed_files": 0,
            "total_chunks": 0,
            "by_type": {}
        }
    
    def process_application(self, app_dir: Path) -> List[Dict]:
        """Process all documents in an application folder"""
        app_id = app_dir.name
        all_chunks = []
        
        # File extensions to process
        file_extensions = {
            '.pdf': self.processor.extract_pdf,
            '.xlsx': self.processor.extract_xlsx,
            '.png': self.processor.extract_png,
            '.txt': self.processor.extract_txt
        }
        
        for file_path in app_dir.iterdir():
            if file_path.suffix.lower() not in file_extensions:
                continue
            
            if file_path.name == 'metadata.json':
                continue
            
            self.stats["total_files"] += 1
            
            # Extract text
            extractor = file_extensions[file_path.suffix.lower()]
            text = extractor(str(file_path))
            
            if not text:
                self.stats["failed_files"] += 1
                continue
            
            # Determine document type from filename
            doc_type = file_path.stem  # e.g., "resume", "bank_statement"
            
            # Chunk text
            chunks = self.chunker.chunk(text, doc_type, app_id)
            all_chunks.extend(chunks)
            
            self.stats["processed_files"] += 1
            self.stats["total_chunks"] += len(chunks)
            
            # Track by type
            if doc_type not in self.stats["by_type"]:
                self.stats["by_type"][doc_type] = {"files": 0, "chunks": 0}
            self.stats["by_type"][doc_type]["files"] += 1
            self.stats["by_type"][doc_type]["chunks"] += len(chunks)
        
        return all_chunks
    
    def run(self, documents_dir: str = "data/processed/documents", clear_existing: bool = True):
        """Run the full ingestion pipeline"""
        print("=" * 80)
        print("DOCUMENT INGESTION PIPELINE - FAANG GRADE")
        print("=" * 80)
        print()
        
        # Clear existing data
        if clear_existing:
            self.indexer.clear_collections()
        
        # Process all applications
        documents_path = Path(documents_dir)
        app_dirs = sorted([d for d in documents_path.iterdir() if d.is_dir()])
        
        print(f"Found {len(app_dirs)} application folders\n")
        print("Processing documents...")
        print("-" * 80)
        
        for i, app_dir in enumerate(app_dirs, 1):
            print(f"[{i}/{len(app_dirs)}] {app_dir.name}...")
            
            # Extract, chunk, and collect
            chunks = self.process_application(app_dir)
            
            # Index chunks
            if chunks:
                self.indexer.index_chunks(chunks)
                print(f"  ✓ Indexed {len(chunks)} chunks")
            else:
                print(f"  ⚠️  No chunks generated")
        
        print("-" * 80)
        print()
        
        # Print statistics
        self._print_stats()
        
        # Verify ChromaDB
        self._verify_chromadb()
    
    def _print_stats(self):
        """Print processing statistics"""
        print("=" * 80)
        print("INGESTION STATISTICS")
        print("=" * 80)
        print(f"Total files found:     {self.stats['total_files']}")
        print(f"Successfully processed: {self.stats['processed_files']}")
        print(f"Failed:                {self.stats['failed_files']}")
        print(f"Total chunks created:  {self.stats['total_chunks']}")
        print()
        
        print("Breakdown by document type:")
        print("-" * 80)
        for doc_type, counts in sorted(self.stats["by_type"].items()):
            print(f"  {doc_type:25s} {counts['files']:3d} files → {counts['chunks']:5d} chunks")
        print()
    
    def _verify_chromadb(self):
        """Verify ChromaDB collections"""
        print("=" * 80)
        print("CHROMADB VERIFICATION")
        print("=" * 80)
        
        collections = self.indexer.client.list_collections()
        total_docs = 0
        
        for collection in collections:
            count = collection.count()
            total_docs += count
            print(f"  {collection.name:30s} {count:6d} documents")
        
        print(f"\n  {'TOTAL DOCUMENTS':30s} {total_docs:6d}")
        print("=" * 80)


if __name__ == "__main__":
    pipeline = DocumentIngestionPipeline()
    pipeline.run(
        documents_dir="data/processed/documents",
        clear_existing=True
    )
