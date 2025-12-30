"""
Production-Grade Document Extraction Service
Uses proper libraries for each document type - NO LLM for basic extraction
"""
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd


class DocumentExtractor:
    """
    High-quality document extraction using specialized libraries
    - PDFs with text: pdfplumber (direct text extraction)
    - Scanned PDFs/Images: Tesseract OCR
    - Excel files: pandas/openpyxl
    - Intelligent field extraction with regex patterns
    """
    
    def __init__(self):
        self.logger = logging.getLogger("DocumentExtractor")
        self.logger.info("Document extractor initialized")
    
    # ========== Emirates ID Extraction ==========
    
    def extract_emirates_id(self, file_path: str) -> Dict[str, Any]:
        """Extract structured data from Emirates ID image"""
        try:
            # Use Tesseract OCR for image
            image = Image.open(file_path)
            
            # Preprocess image for better OCR
            image = self._preprocess_image(image)
            
            # Extract text with English + Arabic
            text = pytesseract.image_to_string(image, lang='eng+ara')
            
            self.logger.info(f"Extracted {len(text)} chars from Emirates ID")
            
            # Parse structured fields
            return self._parse_emirates_id(text)
            
        except Exception as e:
            self.logger.error(f"Emirates ID extraction failed: {e}")
            raise
    
    def _preprocess_image(self, image: Image) -> Image:
        """Preprocess image for better OCR quality"""
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too small (improve OCR accuracy)
        width, height = image.size
        if width < 1000:
            scale = 1000 / width
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image
    
    def _parse_emirates_id(self, text: str) -> Dict[str, Any]:
        """Parse Emirates ID fields from OCR text"""
        data = {
            "full_name": None,
            "id_number": None,
            "nationality": None,
            "date_of_birth": None,
            "gender": None,
            "issue_date": None,
            "expiry_date": None
        }
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Extract name (usually after "Name:" or first substantial line)
            if 'name' in line_lower and ':' in line:
                data['full_name'] = line.split(':', 1)[1].strip()
            elif not data['full_name'] and len(line.split()) >= 2 and line[0].isupper():
                # Likely a name if it's capitalized words
                if not any(keyword in line_lower for keyword in ['card', 'emirates', 'identity', 'united', 'arab']):
                    data['full_name'] = line.strip()
            
            # ID Number patterns: 784-YYYY-XXXXXXX-X or YYYY-XXXX-XXXXXXXX-X
            id_patterns = [
                r'(?:ID\s*No[:.]\s*)?(\d{3,4}[-\s]?\d{4}[-\s]?\d{7,8}[-\s]?\d)',
                r'(\d{15})'  # 15 consecutive digits
            ]
            for pattern in id_patterns:
                match = re.search(pattern, line)
                if match:
                    data['id_number'] = match.group(1).replace(' ', '-')
                    break
            
            # Nationality
            if 'nationality' in line_lower or 'national' in line_lower:
                if ':' in line:
                    data['nationality'] = line.split(':', 1)[1].strip()
                elif 'UAE' in line or 'Emirati' in line:
                    data['nationality'] = 'UAE'
            
            # Dates (DOB, Issue, Expiry)
            date_patterns = [
                r'(\d{4}[-/]\d{2}[-/]\d{2})',
                r'(\d{2}[-/]\d{2}[-/]\d{4})'
            ]
            
            if 'dob' in line_lower or 'birth' in line_lower:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        data['date_of_birth'] = self._normalize_date(match.group(1))
                        break
            
            if 'issued' in line_lower or 'issue' in line_lower:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        data['issue_date'] = self._normalize_date(match.group(1))
                        break
            
            if 'expir' in line_lower:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        data['expiry_date'] = self._normalize_date(match.group(1))
                        break
            
            # Gender
            if 'gender' in line_lower or 'sex' in line_lower:
                if 'male' in line_lower or 'female' in line_lower:
                    data['gender'] = 'Male' if 'male' in line_lower and 'female' not in line_lower else 'Female'
        
        return data
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        date_str = date_str.replace('/', '-')
        parts = date_str.split('-')
        
        if len(parts) == 3:
            if len(parts[0]) == 4:  # YYYY-MM-DD
                return date_str
            elif len(parts[2]) == 4:  # DD-MM-YYYY
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
        
        return date_str
    
    # ========== Bank Statement Extraction ==========
    
    def extract_bank_statement(self, file_path: str) -> Dict[str, Any]:
        """Extract data from bank statement PDF"""
        try:
            text = self._extract_pdf_text(file_path)
            self.logger.info(f"Extracted {len(text)} chars from bank statement")
            return self._parse_bank_statement(text)
        except Exception as e:
            self.logger.error(f"Bank statement extraction failed: {e}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n'.join(text_parts)
    
    def _parse_bank_statement(self, text: str) -> Dict[str, Any]:
        """Parse bank statement fields"""
        data = {
            "account_holder": None,
            "account_number": None,
            "average_monthly_income": 0.0,
            "total_expenses": 0.0,
            "average_balance": 0.0,
            "current_balance": 0.0,
            "monthly_income": 0.0,
            "monthly_expenses": 0.0
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line_clean = line.strip()
            
            # Account holder name
            if 'account holder' in line.lower() and ':' in line:
                data['account_holder'] = line.split(':', 1)[1].strip()
            
            # Account number
            if 'account number' in line.lower() and ':' in line:
                number = line.split(':', 1)[1].strip()
                data['account_number'] = number
            
            # Average Monthly Income
            if 'average monthly income' in line.lower():
                amount = self._extract_amount(line)
                if amount:
                    data['average_monthly_income'] = amount
                    data['monthly_income'] = amount
            
            # Total Expenses
            if 'total expenses' in line.lower():
                amount = self._extract_amount(line)
                if amount:
                    data['total_expenses'] = amount
                    # Estimate monthly expenses (if period is 3 months, divide by 3)
                    if '3 months' in line.lower():
                        data['monthly_expenses'] = amount / 3
                    else:
                        data['monthly_expenses'] = amount
            
            # Average Balance
            if 'average balance' in line.lower():
                amount = self._extract_amount(line)
                if amount:
                    data['average_balance'] = amount
            
            # Current Balance
            if 'current balance' in line.lower():
                amount = self._extract_amount(line)
                if amount:
                    data['current_balance'] = amount
        
        return data
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract monetary amount from text"""
        # Remove currency symbols and extract number
        # Patterns: AED 5,123.45 or $5,123.45 or 5123.45
        pattern = r'(?:AED|USD|EUR|\$|€)?\s*([\d,]+\.?\d*)'
        match = re.search(pattern, text)
        
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return float(amount_str)
            except ValueError:
                pass
        
        return None
    
    # ========== Resume/CV Extraction ==========
    
    def extract_resume(self, file_path: str) -> Dict[str, Any]:
        """Extract employment data from resume"""
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.pdf':
                text = self._extract_pdf_text(str(file_path))
            else:
                # Image-based resume
                image = Image.open(file_path)
                image = self._preprocess_image(image)
                text = pytesseract.image_to_string(image, lang='eng')
            
            self.logger.info(f"Extracted {len(text)} chars from resume")
            return self._parse_resume(text)
            
        except Exception as e:
            self.logger.error(f"Resume extraction failed: {e}")
            raise
    
    def _parse_resume(self, text: str) -> Dict[str, Any]:
        """Parse resume fields"""
        data = {
            "full_name": None,
            "email": None,
            "phone": None,
            "current_position": None,
            "years_of_experience": 0,
            "employment_status": "unknown",
            "skills": [],
            "education": []
        }
        
        lines = text.split('\n')
        text_lower = text.lower()
        
        # Name (usually first substantive line)
        for line in lines[:5]:
            if len(line.split()) >= 2 and line[0].isupper():
                if not any(kw in line.lower() for kw in ['resume', 'cv', 'curriculum']):
                    data['full_name'] = line.strip()
                    break
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            data['email'] = email_match.group(0)
        
        # Phone
        phone_pattern = r'[\+]?[0-9]{1,3}[-\s]?[(]?[0-9]{1,4}[)]?[-\s]?[0-9]{1,4}[-\s]?[0-9]{1,9}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            data['phone'] = phone_match.group(0)
        
        # Employment status
        if any(kw in text_lower for kw in ['currently employed', 'present', 'current position']):
            data['employment_status'] = 'employed'
        elif any(kw in text_lower for kw in ['unemployed', 'seeking', 'looking for']):
            data['employment_status'] = 'unemployed'
        
        # Extract years of experience
        exp_patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?'
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                data['years_of_experience'] = int(match.group(1))
                break
        
        return data
    
    # ========== Assets & Liabilities (Excel) ==========
    
    def extract_assets_liabilities(self, file_path: str) -> Dict[str, Any]:
        """Extract financial data from Excel file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            self.logger.info(f"Read Excel with {len(df)} rows, {len(df.columns)} columns")
            
            return self._parse_assets_liabilities(df)
            
        except Exception as e:
            self.logger.error(f"Assets/Liabilities extraction failed: {e}")
            raise
    
    def _parse_assets_liabilities(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Parse assets and liabilities from DataFrame"""
        data = {
            "total_assets": 0.0,
            "total_liabilities": 0.0,
            "net_worth": 0.0,
            "assets_breakdown": {},
            "liabilities_breakdown": {}
        }
        
        # Look for columns with financial data
        for col in df.columns:
            col_lower = str(col).lower()
            
            # Assets
            if 'asset' in col_lower or 'savings' in col_lower or 'property' in col_lower:
                values = pd.to_numeric(df[col], errors='coerce').fillna(0)
                total = values.sum()
                if total > 0:
                    data['assets_breakdown'][str(col)] = float(total)
                    data['total_assets'] += total
            
            # Liabilities
            if 'liabil' in col_lower or 'debt' in col_lower or 'loan' in col_lower:
                values = pd.to_numeric(df[col], errors='coerce').fillna(0)
                total = values.sum()
                if total > 0:
                    data['liabilities_breakdown'][str(col)] = float(total)
                    data['total_liabilities'] += total
        
        data['net_worth'] = data['total_assets'] - data['total_liabilities']
        
        return data
    
    # ========== Credit Report ==========
    
    def extract_credit_report(self, file_path: str) -> Dict[str, Any]:
        """Extract credit information from PDF"""
        try:
            text = self._extract_pdf_text(file_path)
            self.logger.info(f"Extracted {len(text)} chars from credit report")
            return self._parse_credit_report(text)
        except Exception as e:
            self.logger.error(f"Credit report extraction failed: {e}")
            raise
    
    def _parse_credit_report(self, text: str) -> Dict[str, Any]:
        """Parse credit report fields"""
        data = {
            "credit_score": None,
            "payment_history": None,
            "outstanding_debt": 0.0,
            "credit_utilization": None
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Credit score (usually 300-850 range)
            if 'credit score' in line_lower or 'score' in line_lower:
                score_match = re.search(r'\b([3-8]\d{2})\b', line)
                if score_match:
                    data['credit_score'] = int(score_match.group(1))
            
            # Payment history
            if 'payment history' in line_lower:
                if 'good' in line_lower or 'excellent' in line_lower:
                    data['payment_history'] = 'Good'
                elif 'poor' in line_lower or 'bad' in line_lower:
                    data['payment_history'] = 'Poor'
                elif 'fair' in line_lower:
                    data['payment_history'] = 'Fair'
            
            # Outstanding debt
            if 'outstanding' in line_lower or 'total debt' in line_lower:
                amount = self._extract_amount(line)
                if amount:
                    data['outstanding_debt'] = amount
            
            # Credit utilization
            if 'utilization' in line_lower:
                percent_match = re.search(r'(\d+)\s*%', line)
                if percent_match:
                    data['credit_utilization'] = f"{percent_match.group(1)}%"
        
        return data


# Singleton instance
_document_extractor = None

def get_document_extractor() -> DocumentExtractor:
    """Get singleton document extractor"""
    global _document_extractor
    if _document_extractor is None:
        _document_extractor = DocumentExtractor()
    return _document_extractor
