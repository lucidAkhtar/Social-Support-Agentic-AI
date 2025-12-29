"""
ResumeGenerator: Generate professional CVs/Resumes
Matches employment history, education, and experience
Production-grade PDF output
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .config import GOVERNMENT_EMPLOYERS, PRIVATE_EMPLOYERS, JOB_TITLES, EDUCATION_LEVELS


class ResumeGenerator:
    """Generate professional resumes/CVs."""
    
    SKILLS_BANK = {
        "Government": [
            "Administrative Management", "Policy Implementation", "Public Relations",
            "Database Management", "Financial Reporting", "Compliance", "Planning",
            "Team Leadership", "Document Management", "Client Service"
        ],
        "Private": [
            "Customer Service", "Sales", "Financial Analysis", "Project Management",
            "Business Development", "IT Systems", "Marketing", "Quality Assurance",
            "Supply Chain", "Operations", "Data Analysis", "Communication"
        ],
        "Self-employed": [
            "Business Development", "Client Management", "Financial Management",
            "Problem Solving", "Negotiation", "Strategic Planning", "Market Analysis",
            "Networking", "Risk Management", "Entrepreneurship"
        ]
    }
    
    def __init__(self):
        """Initialize ResumeGenerator."""
        self.employers = GOVERNMENT_EMPLOYERS + PRIVATE_EMPLOYERS
    
    def generate_resume(
        self,
        full_name: str,
        email: str,
        phone: str,
        education_level: str,
        current_position: str,
        years_experience: int,
        current_employer: str = None,
        employment_type: str = "Government",
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate professional resume.
        
        Args:
            full_name: Full name
            email: Email address
            phone: Phone number
            education_level: Education level from EDUCATION_LEVELS
            current_position: Current job title
            years_experience: Years of work experience
            current_employer: Current employer name
            employment_type: Type of employment
            output_path: Path to save PDF
            
        Returns:
            Dict: Resume data and file path
        """
        # Generate work experience
        work_experience = self._generate_work_experience(
            years=years_experience,
            current_position=current_position,
            current_employer=current_employer,
            employment_type=employment_type
        )
        
        # Generate education
        education = self._generate_education(education_level)
        
        # Generate skills
        skills = random.sample(
            self.SKILLS_BANK.get(employment_type, self.SKILLS_BANK["Private"]),
            k=8
        )
        
        resume_data = {
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "education_level": education_level,
            "education": education,
            "work_experience": work_experience,
            "skills": skills,
            "years_experience": years_experience,
            "pdf_path": output_path
        }
        
        # Generate PDF if output path provided
        if output_path:
            self._generate_pdf(resume_data, output_path)
        
        return resume_data
    
    def _generate_work_experience(
        self,
        years: int,
        current_position: str,
        current_employer: str = None,
        employment_type: str = "Government"
    ) -> List[Dict[str, str]]:
        """
        Generate work experience entries.
        
        Args:
            years: Total years of experience
            current_position: Current job title
            current_employer: Current employer
            employment_type: Type of employment
            
        Returns:
            List: Work experience entries
        """
        experience = []
        today = datetime.now()
        
        # Handle unemployed/student cases
        if years == 0 or employment_type in ["Unemployed", "Student"]:
            return [{
                "position": current_position or "Job Seeker",
                "employer": "N/A",
                "start_date": today.strftime("%B %Y"),
                "end_date": "Present",
                "duration": "0 years"
            }]
        
        # Current position (ongoing)
        if not current_employer:
            if employment_type == "Government":
                current_employer = random.choice(GOVERNMENT_EMPLOYERS)[1]
            elif employment_type == "Private":
                current_employer = random.choice(PRIVATE_EMPLOYERS)[1]
            else:
                current_employer = "Self-Employed"
        
        current_start = today - timedelta(days=random.randint(365, 365*5))
        
        experience.append({
            "position": current_position,
            "employer": current_employer,
            "start_date": current_start.strftime("%B %Y"),
            "end_date": "Present",
            "duration": f"{max(1, (today - current_start).days // 365)} years"
        })
        
        # Previous positions
        remaining_years = years - max(1, (today - current_start).days // 365)
        
        while remaining_years > 0:
            if employment_type == "Government":
                employer = random.choice(GOVERNMENT_EMPLOYERS)[1]
                positions = JOB_TITLES["Government"]
            else:
                employer = random.choice(PRIVATE_EMPLOYERS)[1]
                positions = JOB_TITLES["Private"]
            
            position = random.choice(positions)
            employment_duration = random.randint(1, min(4, remaining_years))
            
            end_date = current_start - timedelta(days=30)
            start_date = end_date - timedelta(days=employment_duration*365)
            
            experience.append({
                "position": position,
                "employer": employer,
                "start_date": start_date.strftime("%B %Y"),
                "end_date": end_date.strftime("%B %Y"),
                "duration": f"{employment_duration} years"
            })
            
            remaining_years -= employment_duration
            current_start = start_date
        
        return experience
    
    def _generate_education(self, education_level: str) -> List[Dict[str, str]]:
        """
        Generate education entries.
        
        Args:
            education_level: Highest education level
            
        Returns:
            List: Education entries
        """
        education = []
        
        # Map education level to school/university
        universities = [
            "United Arab Emirates University",
            "American University of Sharjah",
            "Al Ain University",
            "Abu Dhabi University",
            "Zayed University",
            "Abu Dhabi Vocational Education and Training Institute"
        ]
        
        # Current degree
        if education_level in ["Bachelor's Degree", "Master's Degree", "PhD"]:
            university = random.choice(universities)
            field = random.choice([
                "Business Administration", "Finance", "Computer Science",
                "Engineering", "Accounting", "Management", "Economics"
            ])
            
            today = datetime.now()
            if education_level == "Bachelor's Degree":
                grad_year = today.year - random.randint(3, 10)
            elif education_level == "Master's Degree":
                grad_year = today.year - random.randint(1, 5)
            else:  # PhD
                grad_year = today.year - random.randint(1, 3)
            
            education.append({
                "degree": education_level,
                "field": field,
                "institution": university,
                "graduation_year": str(grad_year)
            })
        
        # Secondary education
        education.append({
            "degree": "High School Diploma",
            "field": "General Studies",
            "institution": "Government Secondary School",
            "graduation_year": str(datetime.now().year - random.randint(8, 20))
        })
        
        return education
    
    def _generate_pdf(self, resume_data: Dict[str, Any], output_path: str) -> None:
        """
        Generate resume PDF.
        
        Args:
            resume_data: Resume data dictionary
            output_path: Path to save PDF
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            name_style = ParagraphStyle(
                'Name',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1f4788'),
                alignment=TA_CENTER,
                spaceAfter=3,
                leading=16
            )
            
            contact_style = ParagraphStyle(
                'Contact',
                parent=styles['Normal'],
                fontSize=8,
                alignment=TA_CENTER,
                spaceAfter=10
            )
            
            section_style = ParagraphStyle(
                'Section',
                parent=styles['Heading2'],
                fontSize=10,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=6,
                spaceBefore=6,
                borderColor=colors.HexColor('#1f4788'),
                borderWidth=1,
                borderPadding=4
            )
            
            entry_style = ParagraphStyle(
                'Entry',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=3,
                leading=11
            )
            
            # Header
            story.append(Paragraph(resume_data['full_name'], name_style))
            
            contact_info = f"{resume_data['email']} | {resume_data['phone']}"
            story.append(Paragraph(contact_info, contact_style))
            
            story.append(Spacer(1, 0.1*inch))
            
            # Professional Summary
            story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
            summary = f"Dedicated professional with {resume_data['years_experience']} years of experience in {resume_data['education_level']} role."
            story.append(Paragraph(summary, entry_style))
            story.append(Spacer(1, 0.08*inch))
            
            # Work Experience
            story.append(Paragraph("WORK EXPERIENCE", section_style))
            for exp in resume_data['work_experience'][:4]:  # Show last 4 positions
                exp_text = f"<b>{exp['position']}</b><br/>{exp['employer']}<br/>{exp['start_date']} – {exp['end_date']}"
                story.append(Paragraph(exp_text, entry_style))
                story.append(Spacer(1, 0.06*inch))
            
            story.append(Spacer(1, 0.08*inch))
            
            # Education
            story.append(Paragraph("EDUCATION", section_style))
            for edu in resume_data['education']:
                edu_text = f"<b>{edu['degree']}</b> in {edu['field']}<br/>{edu['institution']} ({edu['graduation_year']})"
                story.append(Paragraph(edu_text, entry_style))
                story.append(Spacer(1, 0.06*inch))
            
            story.append(Spacer(1, 0.08*inch))
            
            # Skills
            story.append(Paragraph("KEY SKILLS", section_style))
            skills_text = ", ".join(resume_data['skills'])
            story.append(Paragraph(skills_text, entry_style))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")


# Quick test
if __name__ == "__main__":
    gen = ResumeGenerator()
    
    print("=" * 60)
    print("RESUME GENERATION TEST")
    print("=" * 60)
    
    resume = gen.generate_resume(
        full_name="Ahmed Al Mazrouei",
        email="ahmed.mazrouei@gmail.com",
        phone="+971-50-123-4567",
        education_level="Bachelor's Degree",
        current_position="Senior Accountant",
        years_experience=5,
        employment_type="Government"
    )
    
    print(f"\nResume Generated:")
    print(f"  Name: {resume['full_name']}")
    print(f"  Experience: {resume['years_experience']} years")
    print(f"  Education: {resume['education_level']}")
    print(f"  Work positions: {len(resume['work_experience'])}")
    print(f"  Skills: {len(resume['skills'])}")
