"""
Production-Grade Document Extraction Service
Uses proper libraries for each document type - NO LLM for basic extraction
"""
import logging
import re
import os
import json
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
            return {}
    
    # ========== Employment Letter Extraction (NEW) ==========
    
    def extract_employment_letter(self, file_path: str) -> Dict[str, Any]:
        """Extract employment details from employment letter"""
        try:
            text = self._extract_pdf_text(str(file_path))
            self.logger.info(f"Extracted {len(text)} chars from employment letter")
            return self._parse_employment_letter(text)
        except Exception as e:
            self.logger.error(f"Employment letter extraction failed: {e}")
            return {}
    
    def _parse_employment_letter(self, text: str) -> Dict[str, Any]:
        """Parse employment letter for company, position, salary, start date"""
        data = {
            "company_name": None,
            "current_position": None,
            "monthly_salary": 0.0,
            "join_date": None,
            "employment_type": None,
            "employment_status": "employed"
        }
        
        lines = text.split('\n')
        text_lower = text.lower()
        
        # Extract company name (usually at top)
        for line in lines[:10]:
            if line.strip() and not any(x in line.lower() for x in ['date:', 'to whom', 'hr', 'human resources', 'department']):
                if len(line.strip()) < 50 and len(line.strip()) > 3:
                    data['company_name'] = line.strip()
                    break
        
        # Extract position/job title
        position_patterns = [
            r'employed as\s+(?:a|an)?\s*([\w\s]+?)(?:\s+in|\.|,|$)',
            r'position[:\s]+([\w\s]+?)(?:\.|,|$)',
            r'works? as\s+(?:a|an)?\s*([\w\s]+?)(?:\s+in|\.|,|$)',
            r'serving.*?as\s+(?:a|an)?\s*([\w\s]+?)(?:\s+in|\.|,|$)'
        ]
        for pattern in position_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                data['current_position'] = match.group(1).strip().title()
                break
        
        # Extract monthly salary
        salary_patterns = [
            r'salary of[:\s]+(?:AED|aed)?[\s]?([\d,]+\.?\d*)',
            r'monthly salary[:\s]+(?:AED|aed)?[\s]?([\d,]+\.?\d*)',
            r'earns[:\s]+(?:AED|aed)?[\s]?([\d,]+\.?\d*)',
            r'compensation[:\s]+(?:AED|aed)?[\s]?([\d,]+\.?\d*)'
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                salary_str = match.group(1).replace(',', '')
                try:
                    data['monthly_salary'] = float(salary_str)
                    break
                except:
                    pass
        
        # Extract join date
        date_patterns = [
            r'joined.*?on[:\s]+(\w+\s+\d+,?\s+\d{4})',
            r'employment.*?from[:\s]+(\w+\s+\d+,?\s+\d{4})',
            r'start(?:ed|ing)?.*?(?:date|on)[:\s]+(\w+\s+\d+,?\s+\d{4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                data['join_date'] = match.group(1).strip()
                break
        
        # Extract employment type
        if 'full-time' in text_lower or 'full time' in text_lower:
            data['employment_type'] = 'Full-time'
        elif 'part-time' in text_lower or 'part time' in text_lower:
            data['employment_type'] = 'Part-time'
        elif 'contract' in text_lower:
            data['employment_type'] = 'Contract'
        elif 'permanent' in text_lower:
            data['employment_type'] = 'Permanent'
        
        self.logger.info(f"✅ Employment letter: company={data['company_name']}, position={data['current_position']}, salary={data['monthly_salary']} AED")
        
        return data
    
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
        """
        Parse assets and liabilities from DataFrame - PRODUCTION GRADE
        
        Handles multiple Excel formats:
        1. Vertical format: Labels in first column, values in second
        2. Horizontal format: Labels as column headers
        3. Multiple sheets with summary rows
        """
        data = {
            "total_assets": 0.0,
            "total_liabilities": 0.0,
            "net_worth": 0.0,
            "assets_breakdown": {},
            "liabilities_breakdown": {}
        }
        
        self.logger.info(f"Parsing Excel with shape {df.shape}, columns: {list(df.columns)}")
        
        # Strategy 1: Vertical format (labels in rows, values in adjacent column)
        # Common format: "Total Assets (AED):" in column 0, value in column 1
        for idx, row in df.iterrows():
            try:
                # Get first non-null column value as label
                label = None
                value_col = None
                
                for col_idx, col in enumerate(df.columns):
                    cell_value = row[col]
                    if pd.notna(cell_value) and str(cell_value).strip():
                        if label is None:
                            label = str(cell_value).strip()
                        elif value_col is None and col_idx > 0:
                            # This is the value column
                            value_col = cell_value
                            break
                
                if label and value_col is not None:
                    label_lower = label.lower()
                    
                    # Try to convert value to numeric
                    try:
                        numeric_value = float(str(value_col).replace(',', '').replace(' ', ''))
                    except (ValueError, AttributeError):
                        continue
                    
                    # Match Total Assets
                    if 'total' in label_lower and 'asset' in label_lower:
                        data['total_assets'] = numeric_value
                        self.logger.info(f"Found Total Assets (vertical): {numeric_value} AED")
                    
                    # Match Total Liabilities
                    elif 'total' in label_lower and ('liabilit' in label_lower or 'debt' in label_lower):
                        data['total_liabilities'] = numeric_value
                        self.logger.info(f"Found Total Liabilities (vertical): {numeric_value} AED")
                    
                    # Individual asset categories
                    elif any(kw in label_lower for kw in ['savings', 'property', 'cash', 'investment', 'vehicle', 'real estate']):
                        if 'asset' in label_lower or numeric_value > 0:
                            data['assets_breakdown'][label] = numeric_value
                    
                    # Individual liability categories
                    elif any(kw in label_lower for kw in ['loan', 'mortgage', 'credit card', 'debt']):
                        data['liabilities_breakdown'][label] = numeric_value
                        
            except Exception as e:
                self.logger.debug(f"Skipping row {idx}: {e}")
                continue
        
        # Strategy 2: Horizontal format (column headers with "Total Assets", "Total Liabilities")
        if data['total_assets'] == 0 and data['total_liabilities'] == 0:
            for col in df.columns:
                col_str = str(col).strip()
                col_lower = col_str.lower()
                
                try:
                    # Exact match for "Total Assets"
                    if 'total' in col_lower and 'asset' in col_lower:
                        values = pd.to_numeric(df[col], errors='coerce').dropna()
                        if len(values) > 0:
                            data['total_assets'] = float(values.iloc[0])
                            self.logger.info(f"Found Total Assets (horizontal): {data['total_assets']} AED")
                    
                    # Exact match for "Total Liabilities"
                    elif 'total' in col_lower and ('liabilit' in col_lower or 'debt' in col_lower):
                        values = pd.to_numeric(df[col], errors='coerce').dropna()
                        if len(values) > 0:
                            data['total_liabilities'] = float(values.iloc[0])
                            self.logger.info(f"Found Total Liabilities (horizontal): {data['total_liabilities']} AED")
                    
                    # Individual asset columns
                    elif any(kw in col_lower for kw in ['asset', 'savings', 'property', 'cash', 'investment']):
                        if 'total' not in col_lower:
                            values = pd.to_numeric(df[col], errors='coerce').fillna(0)
                            total = values.sum()
                            if total > 0:
                                data['assets_breakdown'][col_str] = float(total)
                    
                    # Individual liability columns
                    elif any(kw in col_lower for kw in ['liabil', 'debt', 'loan', 'mortgage', 'credit']):
                        if 'total' not in col_lower:
                            values = pd.to_numeric(df[col], errors='coerce').fillna(0)
                            total = values.sum()
                            if total > 0:
                                data['liabilities_breakdown'][col_str] = float(total)
                except Exception as e:
                    self.logger.debug(f"Error processing column {col}: {e}")
                    continue
        
        # Strategy 3: Aggregate from breakdown if totals still not found
        if data['total_assets'] == 0 and data['assets_breakdown']:
            data['total_assets'] = sum(data['assets_breakdown'].values())
            self.logger.info(f"Calculated Total Assets from breakdown: {data['total_assets']} AED")
        
        if data['total_liabilities'] == 0 and data['liabilities_breakdown']:
            data['total_liabilities'] = sum(data['liabilities_breakdown'].values())
            self.logger.info(f"Calculated Total Liabilities from breakdown: {data['total_liabilities']} AED")
        
        # Calculate net worth
        data['net_worth'] = data['total_assets'] - data['total_liabilities']
        
        # Validation
        if data['total_assets'] == 0 and data['total_liabilities'] == 0:
            self.logger.warning("No assets or liabilities extracted - check Excel format")
        
        self.logger.info(
            f"✅ EXTRACTION COMPLETE: Assets={data['total_assets']:.2f} AED, "
            f"Liabilities={data['total_liabilities']:.2f} AED, "
            f"Net Worth={data['net_worth']:.2f} AED"
        )
        
        return data
    
    # ========== Credit Report ==========
    
    def extract_credit_report(self, file_path: str) -> Dict[str, Any]:
        """Extract credit information from JSON or PDF"""
        try:
            # Check if file is JSON
            if file_path.endswith('.json'):
                self.logger.info(f"Processing JSON credit report: {file_path}")
                return self._parse_credit_report_json(file_path)
            
            # Check if JSON file exists alongside PDF
            json_path = file_path.replace('.pdf', '.json')
            if os.path.exists(json_path):
                self.logger.info(f"Found JSON credit report: {json_path}")
                return self._parse_credit_report_json(json_path)
            
            # Fallback to PDF extraction
            text = self._extract_pdf_text(file_path)
            self.logger.info(f"Extracted {len(text)} chars from credit report PDF")
            return self._parse_credit_report_text(text)
        except Exception as e:
            self.logger.error(f"Credit report extraction failed: {e}")
            return {}
    
    def _parse_credit_report_json(self, json_path: str) -> Dict[str, Any]:
        """Parse structured JSON credit report (UAE Credit Bureau format)"""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            # Extract comprehensive credit information
            result = {
                "credit_score": data.get("credit_score"),
                "credit_rating": data.get("credit_rating"),
                "report_id": data.get("report_id"),
                "report_date": data.get("report_date"),
                "bureau_name": data.get("bureau_name", "UAE Credit Bureau"),
                
                # Payment history
                "payment_history": data.get("payment_history", {}),
                "on_time_payments": data.get("payment_history", {}).get("on_time_payments", 0),
                "late_payments": data.get("payment_history", {}).get("late_payments_30_days", 0),
                "missed_payments": data.get("payment_history", {}).get("missed_payments", 0),
                "payment_ratio": data.get("payment_history", {}).get("payment_ratio", 0),
                
                # Outstanding debt
                "total_outstanding": data.get("total_outstanding", 0),
                "outstanding_debt": data.get("total_outstanding", 0),
                
                # Credit accounts (detailed)
                "credit_accounts": data.get("credit_accounts", []),
                "active_accounts": len([acc for acc in data.get("credit_accounts", []) if acc.get("account_status") == "Active"]),
                
                # Credit utilization
                "total_credit_limit": sum(acc.get("credit_limit", 0) for acc in data.get("credit_accounts", [])),
                "total_balance": sum(acc.get("balance", 0) for acc in data.get("credit_accounts", [])),
            }
            
            # Calculate credit utilization percentage
            if result["total_credit_limit"] > 0:
                result["credit_utilization"] = (result["total_balance"] / result["total_credit_limit"]) * 100
            else:
                result["credit_utilization"] = 0
            
            # Recent enquiries
            result["enquiries"] = data.get("enquiries", [])
            result["recent_enquiries"] = len(data.get("enquiries", []))
            
            self.logger.info(f"✅ Extracted credit data: score={result['credit_score']}, accounts={len(result['credit_accounts'])}, outstanding={result['outstanding_debt']:.2f} AED")
            
            return result
            
        except Exception as e:
            self.logger.error(f"JSON credit report parsing failed: {e}")
            return {}
    
    def _parse_credit_report_text(self, text: str) -> Dict[str, Any]:
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
