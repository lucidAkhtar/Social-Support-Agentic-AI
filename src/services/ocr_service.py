"""
OCR Service - Production-grade document text extraction
Supports multiple OCR engines with fallback mechanisms
"""
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import re

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False


class OCREngine(Enum):
    """Available OCR engines"""
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"
    FALLBACK = "fallback"


@dataclass
class OCRConfig:
    """OCR configuration"""
    primary_engine: OCREngine = OCREngine.TESSERACT
    fallback_engine: OCREngine = OCREngine.FALLBACK
    tesseract_cmd: Optional[str] = None
    languages: List[str] = None
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = ["eng", "ara"]  # English and Arabic for UAE


class OCRService:
    """
    Production-grade OCR service with multiple engines and fallback
    Features:
    - Multiple OCR engine support (Tesseract, PaddleOCR)
    - Automatic fallback
    - Language support (English, Arabic)
    - Text post-processing
    - Error handling
    """
    
    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self.logger = logging.getLogger("OCRService")
        
        # Configure Tesseract
        if self.config.tesseract_cmd:
            if TESSERACT_AVAILABLE:
                pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_cmd
        
        # Initialize PaddleOCR if available
        self.paddle_ocr = None
        if PADDLEOCR_AVAILABLE and self.config.primary_engine == OCREngine.PADDLEOCR:
            try:
                self.paddle_ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',  # or 'arabic'
                    use_gpu=False
                )
                self.logger.info("PaddleOCR initialized")
            except Exception as e:
                self.logger.warning(f"PaddleOCR initialization failed: {e}")
        
        # Check available engines
        self._check_available_engines()
    
    def _check_available_engines(self):
        """Check which OCR engines are available"""
        available = []
        
        if TESSERACT_AVAILABLE:
            try:
                pytesseract.get_tesseract_version()
                available.append("Tesseract")
            except:
                pass
        
        if PADDLEOCR_AVAILABLE and self.paddle_ocr:
            available.append("PaddleOCR")
        
        if available:
            self.logger.info(f"Available OCR engines: {', '.join(available)}")
        else:
            self.logger.warning("No OCR engines available - using fallback text extraction")
    
    async def extract_text(self,
                          file_path: str,
                          document_type: Optional[str] = None) -> str:
        """
        Extract text from document with fallback
        
        Args:
            file_path: Path to image/PDF file
            document_type: Type of document for context
            
        Returns:
            Extracted text
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # If it's a text file, just read it
        if file_path.suffix.lower() == '.txt':
            return self._read_text_file(file_path)
        
        # Try primary engine
        try:
            if self.config.primary_engine == OCREngine.TESSERACT and TESSERACT_AVAILABLE:
                text = self._extract_with_tesseract(file_path)
            elif self.config.primary_engine == OCREngine.PADDLEOCR and self.paddle_ocr:
                text = self._extract_with_paddleocr(file_path)
            else:
                text = self._fallback_extraction(file_path)
            
            # Post-process text
            text = self._post_process_text(text)
            
            self.logger.info(f"Extracted {len(text)} characters from {file_path.name}")
            return text
            
        except Exception as e:
            self.logger.error(f"Primary OCR failed: {e}")
            
            # Try fallback
            try:
                text = self._fallback_extraction(file_path)
                text = self._post_process_text(text)
                self.logger.warning(f"Used fallback extraction for {file_path.name}")
                return text
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {fallback_error}")
                return ""
    
    def _read_text_file(self, file_path: Path) -> str:
        """Read plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _extract_with_tesseract(self, file_path: Path) -> str:
        """Extract text using Tesseract OCR"""
        try:
            image = Image.open(file_path)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text with language support
            lang = '+'.join(self.config.languages)
            text = pytesseract.image_to_string(image, lang=lang)
            
            return text
        except Exception as e:
            raise RuntimeError(f"Tesseract extraction failed: {e}")
    
    def _extract_with_paddleocr(self, file_path: Path) -> str:
        """Extract text using PaddleOCR"""
        try:
            result = self.paddle_ocr.ocr(str(file_path), cls=True)
            
            # Combine all text from OCR result
            text_lines = []
            for line in result:
                for word_info in line:
                    text_lines.append(word_info[1][0])
            
            return '\n'.join(text_lines)
        except Exception as e:
            raise RuntimeError(f"PaddleOCR extraction failed: {e}")
    
    def _fallback_extraction(self, file_path: Path) -> str:
        """Fallback extraction - read as text if possible"""
        # For testing, if it's actually a .txt file with wrong extension
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            # Return empty string if nothing works
            self.logger.warning(f"Could not extract text from {file_path}")
            return ""
    
    def _post_process_text(self, text: str) -> str:
        """Post-process extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common OCR artifacts
        text = text.replace('|', 'I')  # Common misread
        text = text.replace('0', 'O')  # In some contexts
        
        # Trim
        text = text.strip()
        
        return text
    
    async def extract_fields_from_id(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured fields from Emirates ID
        
        Args:
            file_path: Path to ID image
            
        Returns:
            Extracted fields
        """
        text = await self.extract_text(file_path, "emirates_id")
        
        # Extract common ID fields
        fields = {
            "full_name": self._extract_field(text, ["name", "holder"]),
            "id_number": self._extract_id_number(text),
            "nationality": self._extract_field(text, ["nationality", "national"]),
            "date_of_birth": self._extract_date(text, ["birth", "dob"]),
            "gender": self._extract_field(text, ["gender", "sex"]),
            "address": self._extract_field(text, ["address", "residence"])
        }
        
        return fields
    
    def _extract_field(self, text: str, keywords: List[str]) -> str:
        """Extract field value by keywords"""
        lines = text.split('\n')
        for line in lines:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    # Extract value after colon or keyword
                    if ':' in line:
                        value = line.split(':', 1)[1].strip()
                        if value:
                            return value
        return "Not found"
    
    def _extract_id_number(self, text: str) -> str:
        """Extract ID number using pattern matching"""
        # UAE ID pattern: 784-YYYY-XXXXXXX-X
        pattern = r'784-\d{4}-\d{7}-\d'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        
        # Fallback: look for 15-digit number
        pattern = r'\d{15}'
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        
        return "Not found"
    
    def _extract_date(self, text: str, keywords: List[str]) -> str:
        """Extract date field"""
        lines = text.split('\n')
        for line in lines:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    # Look for date patterns
                    patterns = [
                        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                        r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
                        r'\d{2}-\d{2}-\d{4}'   # DD-MM-YYYY
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            return match.group(0)
        return "Not found"


# Singleton instance
_ocr_service_instance = None

def get_ocr_service(config: Optional[OCRConfig] = None) -> OCRService:
    """Get or create OCR service singleton"""
    global _ocr_service_instance
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService(config)
    return _ocr_service_instance
