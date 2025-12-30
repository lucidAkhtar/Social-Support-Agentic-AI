"""
Resume Parser - Extract structured data from resumes using LLM
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import re

from .llm_service import get_llm_service, LLMService
from .ocr_service import get_ocr_service, OCRService


class ResumeParser:
    """
    Parse resumes and extract structured employment data
    Uses LLM for intelligent extraction
    """
    
    def __init__(self, 
                 llm_service: Optional[LLMService] = None,
                 ocr_service: Optional[OCRService] = None):
        self.llm_service = llm_service or get_llm_service()
        self.ocr_service = ocr_service or get_ocr_service()
        self.logger = logging.getLogger("ResumeParser")
    
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse resume and extract employment data
        
        Args:
            file_path: Path to resume file
            
        Returns:
            Structured employment data
        """
        try:
            # Extract text from resume
            self.logger.info(f"Parsing resume: {file_path}")
            text = await self.ocr_service.extract_text(file_path, "resume")
            
            if not text:
                self.logger.warning("No text extracted from resume")
                return self._get_empty_result()
            
            # Use LLM to extract structured data
            fields = [
                "current_position",
                "current_employer",
                "years_of_experience",
                "employment_status",
                "skills",
                "education"
            ]
            
            extracted = await self.llm_service.extract_structured_data(
                text=text,
                fields=fields,
                context="This is a resume/CV document. Extract employment-related information."
            )
            
            # Post-process and validate
            result = self._post_process_extraction(extracted, text)
            
            self.logger.info(f"Successfully parsed resume")
            return result
            
        except Exception as e:
            self.logger.error(f"Resume parsing failed: {e}")
            return self._get_empty_result()
    
    def _post_process_extraction(self, extracted: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """Post-process extracted data"""
        
        # Calculate total experience if not provided
        if not extracted.get("years_of_experience"):
            extracted["years_of_experience"] = self._estimate_experience(raw_text)
        else:
            # Convert to int
            try:
                extracted["years_of_experience"] = int(
                    re.search(r'\d+', str(extracted["years_of_experience"])).group()
                )
            except:
                extracted["years_of_experience"] = 0
        
        # Determine employment status
        if not extracted.get("employment_status"):
            if extracted.get("current_position") and extracted["current_position"] != "null":
                extracted["employment_status"] = "employed"
            else:
                extracted["employment_status"] = "unemployed"
        
        # Parse skills into list
        skills = extracted.get("skills", "")
        if isinstance(skills, str):
            if skills and skills != "null":
                extracted["skills"] = [s.strip() for s in skills.split(",")]
            else:
                extracted["skills"] = []
        
        # Parse education into list
        education = extracted.get("education", "")
        if isinstance(education, str):
            if education and education != "null":
                extracted["education"] = [e.strip() for e in education.split(",")]
            else:
                extracted["education"] = []
        
        # Build work history
        extracted["work_history"] = self._extract_work_history(raw_text)
        
        # Calculate total experience from work history if available
        if extracted["work_history"] and not extracted["years_of_experience"]:
            total_years = sum([job.get("years", 0) for job in extracted["work_history"]])
            extracted["years_of_experience"] = total_years
        
        return extracted
    
    def _estimate_experience(self, text: str) -> int:
        """Estimate years of experience from text"""
        # Look for patterns like "X years of experience"
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience:\s*(\d+)\+?\s*years?',
            r'(\d+)\s*years?\s+in\s+'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Estimate from work history years
        year_mentions = re.findall(r'\b(19|20)\d{2}\b', text)
        if len(year_mentions) >= 2:
            years = [int(y) for y in year_mentions]
            return max(years) - min(years)
        
        return 0
    
    def _extract_work_history(self, text: str) -> List[Dict[str, Any]]:
        """Extract work history from text"""
        work_history = []
        
        # Simple pattern matching for work experience
        lines = text.split('\n')
        
        current_job = {}
        for line in lines:
            line = line.strip()
            
            # Look for job titles (usually capitalized)
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line):
                if current_job:
                    work_history.append(current_job)
                current_job = {"title": line}
            
            # Look for company names
            elif any(keyword in line.lower() for keyword in ["company", "ltd", "llc", "inc"]):
                if current_job:
                    current_job["company"] = line
            
            # Look for years (YYYY - YYYY or YYYY - Present)
            year_match = re.search(r'(19|20)\d{2}\s*-\s*((19|20)\d{2}|present)', line, re.IGNORECASE)
            if year_match and current_job:
                years_text = year_match.group(0)
                current_job["period"] = years_text
                
                # Calculate years
                start_year = int(re.search(r'(19|20)\d{2}', years_text).group(0))
                if "present" in years_text.lower():
                    from datetime import datetime
                    end_year = datetime.now().year
                else:
                    end_match = re.findall(r'(19|20)\d{2}', years_text)
                    end_year = int(end_match[-1]) if len(end_match) > 1 else start_year
                
                current_job["years"] = end_year - start_year
        
        if current_job:
            work_history.append(current_job)
        
        return work_history[:5]  # Return up to 5 most recent jobs
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "current_position": None,
            "current_employer": None,
            "years_of_experience": 0,
            "employment_status": "unknown",
            "skills": [],
            "education": [],
            "work_history": []
        }


# Singleton instance
_resume_parser_instance = None

def get_resume_parser() -> ResumeParser:
    """Get or create resume parser singleton"""
    global _resume_parser_instance
    if _resume_parser_instance is None:
        _resume_parser_instance = ResumeParser()
    return _resume_parser_instance
