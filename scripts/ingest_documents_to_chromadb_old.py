"""
Production-Grade Document Ingestion Pipeline for ChromaDB
=========================================================

Processes ALL documents from data/processed/documents/APP-XXXXX folders:
- PDFs: resume.pdf, employment_letter.pdf, credit_report.pdf, bank_statement.pdf
- XLSX: assets_liabilities.xlsx
- PNG: emirates_id.png

Pipeline Steps:
1. Document Discovery: Scan all APP folders
2. Text Extraction: PDF, XLSX, PNG (OCR)
3. Chunking: Semantic chunking with overlap
4. Embedding: OpenAI embeddings
5. Indexing: Store in ChromaDB with metadata
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# PDF processing
import pymupdf  # PyMuPDF for PDF extraction

# Excel processing
import pandas as pd
import openpyxl

# Image OCR
from PIL import Image
import pytesseract

# Embeddings and ChromaDB
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings


class DocumentIngestionPipeline:
    """FAANG-grade document processing pipeline"""
    
    def __init__(self, base_path: str = "data/processed/documents"):
        self.base_path = Path(base_path)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Initialize ChromaDB
        chroma_path = Path("data/databases/chromadb")
        chroma_path.mkdir(parents=True, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Document type mapping
        self.doc_types = {
            "resume.pdf": "resume",
            "employment_letter.pdf": "employment",
            "credit_report.pdf": "credit",
            "bank_statement.pdf": "bank_statement",
            "assets_liabilities.xlsx": "assets",
            "emirates_id.png": "id_document"
        }
        
        print("=" * 70)
        print("DOCUMENT INGESTION PIPELINE INITIALIZED")
        print("=" * 70)
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"  ⚠️  Error reading PDF {pdf_path.name}: {e}")
            return ""
    
    def extract_text_from_xlsx(self, xlsx_path: Path) -> str:
        """Extract text from Excel file"""
        try:
            df = pd.read_excel(xlsx_path)
            # Convert to structured text representation
            text = f"Excel Data from {xlsx_path.name}:\n\n"
            text += df.to_string(index=False)
            return text
        except Exception as e:
            print(f"  ⚠️  Error reading XLSX {xlsx_path.name}: {e}")
            return ""
    
    def extract_text_from_image(self, img_path: Path) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(img_path)
            text = pytesseract.image_to_string(image)
            return f"OCR from {img_path.name}:\n{text.strip()}"
        except Exception as e:
            print(f"  ⚠️  Error with OCR on {img_path.name}: {e}")
            return f"Image document: {img_path.name} (OCR unavailable)"
    
    def process_document(self, file_path: Path, app_id: str) -> List[Tuple[str, Dict]]:
        """
        Process a single document file.
        
        Returns:
            List of (text_chunk, metadata) tuples
        """
        file_name = file_path.name
        
        # Extract text based on file type
        if file_path.suffix.lower() == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.xlsx', '.xls']:
            text = self.extract_text_from_xlsx(file_path)
        elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            text = self.extract_text_from_image(file_path)
        elif file_path.suffix.lower() == '.txt':
            text = file_path.read_text(encoding='utf-8')
        else:
            print(f"  ⚠️  Unsupported file type: {file_name}")
            return []
        
        if not text or len(text) < 10:
            print(f"  ⚠️  No text extracted from {file_name}")
            return []
        
        # Chunk the text
        chunks = self.text_splitter.split_text(text)
        
        # Create metadata for each chunk
        doc_type = self.doc_types.get(file_name, "unknown")
        results = []
        
        for i, chunk in enumerate(chunks):
            metadata = {
                "app_id": app_id,
                "document_type": doc_type,
                "file_name": file_name,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source_path": str(file_path.relative_to(self.base_path)),
                "ingestion_date": datetime.now().isoformat()
            }
            results.append((chunk, metadata))
        
        return results
    
    def discover_applications(self) -> List[Path]:
        """Find all APP-XXXXX folders"""
        app_folders = sorted([
            d for d in self.base_path.iterdir() 
            if d.is_dir() and d.name.startswith("APP-")
        ])
        print(f"\n📁 Found {len(app_folders)} application folders")
        return app_folders
    
    def index_to_chromadb(self, chunks_with_metadata: List[Tuple[str, Dict]], collection_name: str):
        """Index documents to ChromaDB collection"""
        if not chunks_with_metadata:
            return
        
        # Get or create collection
        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            # Clear existing data
            existing_ids = collection.get()['ids']
            if existing_ids:
                collection.delete(ids=existing_ids)
                print(f"  🗑️  Cleared {len(existing_ids)} existing documents from {collection_name}")
        except:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": f"Document collection for {collection_name}"}
            )
        
        # Prepare data for batch insertion
        texts = [chunk for chunk, _ in chunks_with_metadata]
        metadatas = [meta for _, meta in chunks_with_metadata]
        ids = [f"{meta['app_id']}_{meta['document_type']}_{meta['chunk_index']}" 
               for _, meta in chunks_with_metadata]
        
        # Generate embeddings
        print(f"  🔄 Generating embeddings for {len(texts)} chunks...")
        embeddings = self.embeddings.embed_documents(texts)
        
        # Batch insert to ChromaDB
        print(f"  💾 Indexing to ChromaDB collection: {collection_name}")
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            end_idx = min(i + batch_size, len(texts))
            collection.add(
                documents=texts[i:end_idx],
                embeddings=embeddings[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx]
            )
        
        print(f"  ✅ Indexed {len(texts)} chunks to {collection_name}")
    
    def process_all_applications(self):
        """Main pipeline: Process all applications and index to ChromaDB"""
        print("\n" + "=" * 70)
        print("STARTING DOCUMENT INGESTION PIPELINE")
        print("=" * 70)
        
        app_folders = self.discover_applications()
        
        # Collections to populate
        resume_chunks = []
        employment_chunks = []
        financial_chunks = []  # bank statements, credit reports, assets
        id_chunks = []
        
        total_files_processed = 0
        total_chunks_created = 0
        
        for app_folder in app_folders:
            app_id = app_folder.name
            print(f"\n📂 Processing {app_id}...")
            
            # Process each document type
            for file_name, doc_type in self.doc_types.items():
                file_path = app_folder / file_name
                
                if not file_path.exists():
                    continue
                
                print(f"  📄 Processing {file_name}...")
                chunks = self.process_document(file_path, app_id)
                
                if chunks:
                    total_files_processed += 1
                    total_chunks_created += len(chunks)
                    print(f"    ✓ Created {len(chunks)} chunks")
                    
                    # Route to appropriate collection
                    if doc_type == "resume":
                        resume_chunks.extend(chunks)
                    elif doc_type == "employment":
                        employment_chunks.extend(chunks)
                    elif doc_type in ["credit", "bank_statement", "assets"]:
                        financial_chunks.extend(chunks)
                    elif doc_type == "id_document":
                        id_chunks.extend(chunks)
        
        print("\n" + "=" * 70)
        print("INDEXING TO CHROMADB")
        print("=" * 70)
        
        # Index each collection
        if resume_chunks:
            print(f"\n📚 Indexing resumes ({len(resume_chunks)} chunks)...")
            self.index_to_chromadb(resume_chunks, "resumes")
        
        if employment_chunks:
            print(f"\n💼 Indexing employment documents ({len(employment_chunks)} chunks)...")
            self.index_to_chromadb(employment_chunks, "employment_documents")
        
        if financial_chunks:
            print(f"\n💰 Indexing financial documents ({len(financial_chunks)} chunks)...")
            self.index_to_chromadb(financial_chunks, "financial_documents")
        
        if id_chunks:
            print(f"\n🆔 Indexing ID documents ({len(id_chunks)} chunks)...")
            self.index_to_chromadb(id_chunks, "id_documents")
        
        # Summary
        print("\n" + "=" * 70)
        print("INGESTION COMPLETE")
        print("=" * 70)
        print(f"✅ Applications processed: {len(app_folders)}")
        print(f"✅ Files processed: {total_files_processed}")
        print(f"✅ Total chunks created: {total_chunks_created}")
        print(f"✅ ChromaDB collections updated: resumes, employment_documents, financial_documents, id_documents")
        
        # Verification
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)
        for collection_name in ["resumes", "employment_documents", "financial_documents", "id_documents"]:
            try:
                collection = self.chroma_client.get_collection(collection_name)
                count = collection.count()
                print(f"✓ {collection_name}: {count} documents")
            except:
                print(f"⚠️  {collection_name}: Collection not found")


def main():
    """Run the ingestion pipeline"""
    pipeline = DocumentIngestionPipeline()
    pipeline.process_all_applications()


if __name__ == "__main__":
    main()
