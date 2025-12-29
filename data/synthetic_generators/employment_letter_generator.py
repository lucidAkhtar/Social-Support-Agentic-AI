"""
EmploymentLetterGenerator: Generate professional employer verification letters
Production-grade PDFs matching actual bank statement income
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from .config import GOVERNMENT_EMPLOYERS, PRIVATE_EMPLOYERS, JOB_TITLES


class EmploymentLetterGenerator:
    """Generate professional employment verification letters."""
    
    def __init__(self):
        """Initialize EmploymentLetterGenerator."""
        self.employers = GOVERNMENT_EMPLOYERS + PRIVATE_EMPLOYERS
    
    def generate_letter(
        self,
        employee_name: str,
        monthly_salary: float,
        years_employed: int,
        position: str = None,
        employment_type: str = "Government",
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate employment verification letter.
        
        Args:
            employee_name: Full name of employee
            monthly_salary: Monthly salary in AED
            years_employed: Years of employment
            position: Job position (auto-generated if not provided)
            employment_type: "Government" or "Private"
            output_path: Path to save PDF
            
        Returns:
            Dict: Letter data and file path
        """
        # Select employer
        if employment_type == "Government":
            employer_code, employer_name, _ = random.choice(GOVERNMENT_EMPLOYERS)
        else:
            employer_code, employer_name, _ = random.choice(PRIVATE_EMPLOYERS)
        
        # Select position if not provided
        if not position:
            position = random.choice(JOB_TITLES[employment_type])
        
        # Calculate employment dates
        today = datetime.now()
        start_date = today - timedelta(days=years_employed*365)
        
        letter_data = {
            "employer_name": employer_name,
            "employee_name": employee_name,
            "position": position,
            "monthly_salary": monthly_salary,
            "years_employed": years_employed,
            "start_date": start_date.strftime("%B %d, %Y"),
            "letter_date": today.strftime("%B %d, %Y"),
            "employment_type": employment_type,
            "pdf_path": output_path
        }
        
        # Generate PDF if output path provided
        if output_path:
            self._generate_pdf(letter_data, output_path)
        
        return letter_data
    
    def _generate_pdf(self, letter_data: Dict[str, Any], output_path: str) -> None:
        """
        Generate employment letter PDF.
        
        Args:
            letter_data: Letter data dictionary
            output_path: Path to save PDF
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            story = []
            
            # Styles
            styles = getSampleStyleSheet()
            
            letterhead_style = ParagraphStyle(
                'Letterhead',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#1f4788'),
                alignment=TA_CENTER,
                spaceAfter=12,
                leading=14
            )
            
            date_style = ParagraphStyle(
                'Date',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_LEFT,
                spaceAfter=18
            )
            
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=14
            )
            
            signature_style = ParagraphStyle(
                'Signature',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_LEFT,
                spaceAfter=2
            )
            
            # Letterhead
            story.append(Paragraph(
                f"<b>{letter_data['employer_name'].upper()}</b>",
                letterhead_style
            ))
            story.append(Paragraph(
                "Human Resources Department",
                letterhead_style
            ))
            story.append(Spacer(1, 0.3*inch))
            
            # Date
            story.append(Paragraph(
                f"Date: {letter_data['letter_date']}",
                date_style
            ))
            story.append(Spacer(1, 0.2*inch))
            
            # Salutation
            story.append(Paragraph(
                "To Whom It May Concern,",
                body_style
            ))
            story.append(Spacer(1, 0.1*inch))
            
            # Body
            body_text = f"""
This letter is to certify that <b>{letter_data['employee_name']}</b> is a valued employee of 
<b>{letter_data['employer_name']}</b>. {letter_data['employee_name']} is currently employed as a 
<b>{letter_data['position']}</b> in our organization.
<br/><br/>
{letter_data['employee_name']} joined our organization on <b>{letter_data['start_date']}</b> and has been 
serving continuously in this position. During the tenure with us, {letter_data['employee_name']} has 
demonstrated exemplary work ethics, reliability, and professional conduct.
<br/><br/>
We confirm that <b>{letter_data['employee_name']}</b> receives a monthly salary of <b>AED {letter_data['monthly_salary']:,.2f}</b> 
(Dirhams). The employment is on full-time basis and considered permanent.
<br/><br/>
We further confirm that the employment is in good standing and there are no outstanding obligations 
or liabilities against {letter_data['employee_name']} with our organization.
<br/><br/>
This letter is issued for official purposes and carries the certification of our Human Resources Department.
            """
            
            story.append(Paragraph(body_text, body_style))
            story.append(Spacer(1, 0.3*inch))
            
            # Closing
            story.append(Paragraph("Yours Sincerely,", body_style))
            story.append(Spacer(1, 0.8*inch))
            
            # Signature block
            story.append(Paragraph("_____________________", signature_style))
            story.append(Paragraph("Human Resources Manager", signature_style))
            story.append(Paragraph(f"{letter_data['employer_name']}", signature_style))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(
                "<i>This is a synthetic document for demonstration purposes.</i>",
                signature_style
            ))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")


# Quick test
if __name__ == "__main__":
    gen = EmploymentLetterGenerator()
    
    print("=" * 60)
    print("EMPLOYMENT LETTER GENERATION TEST")
    print("=" * 60)
    
    letter = gen.generate_letter(
        employee_name="Ahmed Al Mazrouei",
        monthly_salary=8500,
        years_employed=5,
        employment_type="Government"
    )
    
    print(f"\nLetter Generated:")
    print(f"  Employer: {letter['employer_name']}")
    print(f"  Employee: {letter['employee_name']}")
    print(f"  Position: {letter['position']}")
    print(f"  Salary: AED {letter['monthly_salary']:,.2f}/month")
    print(f"  Employment: {letter['years_employed']} years")
