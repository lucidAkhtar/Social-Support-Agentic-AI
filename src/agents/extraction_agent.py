"""
Data Extraction Agent
Extracts structured data from all uploaded documents using:
- pdfplumber for PDFs with text
- Tesseract OCR for images and scanned documents  
- pandas for Excel files
- Intelligent regex-based field extraction
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from ..core.base_agent import BaseAgent
from ..core.types import ExtractedData, Document
from ..services.document_extractor import get_document_extractor


class DataExtractionAgent(BaseAgent):
    """
    Extracts structured data from uploaded documents using production-grade libraries
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("DataExtractionAgent", config)
        self.logger = logging.getLogger("DataExtractionAgent")
        
        # Initialize document extractor
        self.extractor = get_document_extractor()
        
        self.logger.info("Document extractor initialized")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from all documents
        
        Input:
            - application_id
            - documents: List of Document objects
        
        Output:
            - extracted_data: ExtractedData object
        """
        start_time = datetime.now()
        application_id = input_data["application_id"]
        documents = input_data["documents"]
        
        self.logger.info(f"[{application_id}] Starting extraction for {len(documents)} documents")
        
        extracted_data = ExtractedData()
        
        # Process each document type
        for doc in documents:
            doc_type = doc["document_type"]
            file_path = doc["file_path"]
            
            try:
                if doc_type == "emirates_id":
                    result = await self._extract_emirates_id(file_path)
                    extracted_data.applicant_info.update(result)
                    
                elif doc_type == "bank_statement":
                    result = await self._extract_bank_statement(file_path)
                    extracted_data.income_data.update(result)
                    
                elif doc_type == "resume":
                    result = await self._extract_resume(file_path)
                    extracted_data.employment_data.update(result)
                    
                elif doc_type == "assets_liabilities":
                    result = await self._extract_assets_liabilities(file_path)
                    extracted_data.assets_liabilities.update(result)
                    
                elif doc_type == "credit_report":
                    result = await self._extract_credit_report(file_path)
                    extracted_data.credit_data.update(result)
                
                self.logger.info(f"[{application_id}] Extracted {doc_type}")
                
            except Exception as e:
                self.logger.error(f"[{application_id}] Error extracting {doc_type}: {str(e)}")
                # Continue with other documents
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"[{application_id}] Extraction completed in {duration:.2f}s")
        
        return {
            "extracted_data": extracted_data,
            "extraction_time": duration
        }
    
    async def _extract_emirates_id(self, file_path: str) -> Dict[str, Any]:
        """Extract data from Emirates ID using OCR and intelligent parsing"""
        try:
            return self.extractor.extract_emirates_id(file_path)
        except Exception as e:
            self.logger.error(f"Emirates ID extraction failed: {e}")
            return {}
    
    async def _extract_bank_statement(self, file_path: str) -> Dict[str, Any]:
        """Extract income data from bank statement using PDF text extraction"""
        try:
            return self.extractor.extract_bank_statement(file_path)
        except Exception as e:
            self.logger.error(f"Bank statement extraction failed: {e}")
            return {}
    
    async def _extract_resume(self, file_path: str) -> Dict[str, Any]:
        """Extract employment history from resume"""
        try:
            return self.extractor.extract_resume(file_path)
        except Exception as e:
            self.logger.error(f"Resume extraction failed: {e}")
            return {}
    
    async def _extract_assets_liabilities(self, file_path: str) -> Dict[str, Any]:
        """Extract assets and liabilities from Excel file"""
        try:
            return self.extractor.extract_assets_liabilities(file_path)
        except Exception as e:
            self.logger.error(f"Assets/liabilities extraction failed: {e}")
            return {}
    
    async def _extract_credit_report(self, file_path: str) -> Dict[str, Any]:
        """Extract credit information from credit report"""
        try:
            return self.extractor.extract_credit_report(file_path)
        except Exception as e:
            self.logger.error(f"Credit report extraction failed: {e}")
            return {}
