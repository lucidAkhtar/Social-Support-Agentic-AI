"""
CreditReportGenerator: Generate synthetic credit bureau reports
JSON format + PDF rendering
Production-grade with realistic UAE credit scoring
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from .config import CREDIT_SCORE_RANGES


class CreditReportGenerator:
    """Generate realistic UAE credit bureau reports."""
    
    def __init__(self):
        """Initialize CreditReportGenerator."""
        self.bureau_name = "UAE Credit Bureau"
    
    def generate_credit_report(
        self,
        full_name: str,
        emirates_id: str,
        monthly_income: float,
        total_liabilities: float = 0,
        output_json_path: str = None,
        output_pdf_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate credit report.
        
        Args:
            full_name: Full name
            emirates_id: Emirates ID
            monthly_income: Monthly income in AED
            total_liabilities: Total outstanding debt
            output_json_path: Path to save JSON
            output_pdf_path: Path to save PDF
            
        Returns:
            Dict: Credit report data
        """
        # Generate credit score based on income and liabilities
        credit_score = self._calculate_credit_score(monthly_income, total_liabilities)
        
        # Generate payment history
        payment_history = self._generate_payment_history()
        
        # Generate credit accounts
        credit_accounts = self._generate_credit_accounts(total_liabilities)
        
        # Generate enquiries
        enquiries = self._generate_enquiries()
        
        report_data = {
            "report_id": f"CB-{random.randint(100000, 999999)}",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "bureau_name": self.bureau_name,
            "subject": {
                "name": full_name,
                "emirates_id": emirates_id,
                "nationality": "UAE National"
            },
            "credit_score": credit_score,
            "credit_rating": self._get_credit_rating(credit_score),
            "payment_history": payment_history,
            "credit_accounts": credit_accounts,
            "total_outstanding": total_liabilities,
            "enquiries": enquiries,
            "remarks": self._generate_remarks(credit_score, payment_history)
        }
        
        # Save JSON
        if output_json_path:
            with open(output_json_path, 'w') as f:
                json.dump(report_data, f, indent=2)
        
        # Save PDF
        if output_pdf_path:
            self._generate_pdf(report_data, output_pdf_path)
        
        report_data["json_path"] = output_json_path
        report_data["pdf_path"] = output_pdf_path
        
        return report_data
    
    def _calculate_credit_score(self, monthly_income: float, total_liabilities: float) -> int:
        """
        Calculate realistic credit score based on financial metrics.
        UAE Credit Bureau uses 0-1800 scale.
        
        Args:
            monthly_income: Monthly income
            total_liabilities: Total outstanding debt
            
        Returns:
            int: Credit score
        """
        # Base score
        base_score = 1200
        
        # Handle zero income case
        if monthly_income <= 0:
            base_score = 800  # Lower score for unemployed
        else:
            # Income adjustment (higher income = higher score)
            if monthly_income < 5000:
                base_score -= 200
            elif monthly_income < 10000:
                base_score -= 100
            elif monthly_income > 30000:
                base_score += 150
            
            # Debt-to-income ratio (only if we have positive income)
            if total_liabilities > 0:
                dti = total_liabilities / (monthly_income * 12)
                if dti > 5:
                    base_score -= 300
                elif dti > 3:
                    base_score -= 150
                elif dti > 1:
                    base_score -= 50
        
        # Add randomness
        base_score += random.randint(-150, 150)
        
        # Clamp to valid range
        return max(0, min(1800, base_score))
    
    def _get_credit_rating(self, score: int) -> str:
        """Get rating label for score."""
        for rating, (min_score, max_score) in CREDIT_SCORE_RANGES.items():
            if min_score <= score <= max_score:
                return rating
        return "Unknown"
    
    def _generate_payment_history(self) -> Dict[str, Any]:
        """Generate payment history."""
        on_time_payments = random.randint(20, 50)
        late_payments = random.randint(0, 5)
        missed_payments = random.randint(0, 2)
        
        return {
            "on_time_payments": on_time_payments,
            "late_payments_30_days": late_payments,
            "late_payments_60_days": max(0, late_payments - 2),
            "missed_payments": missed_payments,
            "payment_ratio": round(on_time_payments / (on_time_payments + late_payments + missed_payments) * 100, 1)
        }
    
    def _generate_credit_accounts(self, total_liabilities: float) -> list:
        """Generate credit account entries."""
        accounts = []
        
        # Mortgage account
        if total_liabilities > 100000:
            accounts.append({
                "account_type": "Mortgage",
                "institution": random.choice(["FAB", "ADIB", "Mashreq Bank"]),
                "account_status": "Active",
                "balance": round(total_liabilities * 0.6, 0),
                "credit_limit": round(total_liabilities * 0.65, 0),
                "last_payment": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "last_payment_amount": round(total_liabilities * 0.05, 0)
            })
        
        # Credit card accounts
        for i in range(random.randint(1, 3)):
            accounts.append({
                "account_type": "Credit Card",
                "institution": random.choice(["FAB", "ADIB", "Mashreq", "Emirates NBD"]),
                "account_status": "Active",
                "balance": round(random.uniform(5000, 50000), 0),
                "credit_limit": 100000,
                "last_payment": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "last_payment_amount": round(random.uniform(1000, 5000), 0)
            })
        
        # Personal loan
        if random.random() > 0.5:
            accounts.append({
                "account_type": "Personal Loan",
                "institution": random.choice(["FAB", "Mashreq", "Dubai Islamic Bank"]),
                "account_status": "Active",
                "balance": round(random.uniform(20000, 100000), 0),
                "credit_limit": round(random.uniform(20000, 100000), 0),
                "last_payment": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "last_payment_amount": round(random.uniform(1000, 5000), 0)
            })
        
        return accounts
    
    def _generate_enquiries(self) -> list:
        """Generate credit enquiries."""
        enquiries = []
        
        # Last 6 months of enquiries
        for i in range(random.randint(1, 4)):
            enquiries.append({
                "date": (datetime.now() - timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d"),
                "type": random.choice(["Mortgage Application", "Loan Application", "Credit Card Application"]),
                "institution": random.choice(["FAB", "ADIB", "Mashreq", "Emirates Islamic"])
            })
        
        return enquiries
    
    def _generate_remarks(self, credit_score: int, payment_history: Dict) -> str:
        """Generate credit report remarks."""
        if credit_score >= 1600:
            return "Excellent credit profile. Low risk customer."
        elif credit_score >= 1400:
            return "Good credit profile. Moderate risk customer."
        elif credit_score >= 1200:
            return "Fair credit profile. Acceptable risk customer."
        elif credit_score >= 1000:
            return "Poor credit profile. Monitor for payment defaults."
        else:
            return "Very poor credit profile. High risk customer."
    
    def _generate_pdf(self, report_data: Dict[str, Any], output_path: str) -> None:
        """
        Generate credit report PDF.
        
        Args:
            report_data: Report data
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
            
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1f4788'),
                alignment=TA_CENTER,
                spaceAfter=6
            )
            
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=6
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=3
            )
            
            # Header
            story.append(Paragraph("<b>UAE CREDIT BUREAU REPORT</b>", title_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Report Info
            info_data = [
                ["Report ID:", report_data['report_id']],
                ["Report Date:", report_data['report_date']],
                ["Name:", report_data['subject']['name']],
                ["Emirates ID:", report_data['subject']['emirates_id']],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Credit Score
            story.append(Paragraph("<b>Credit Score</b>", heading_style))
            
            score_data = [
                ["Score:", f"{report_data['credit_score']}/1800"],
                ["Rating:", report_data['credit_rating']],
                ["Total Outstanding:", f"AED {report_data['total_outstanding']:,.0f}"],
            ]
            
            score_table = Table(score_data, colWidths=[2*inch, 4*inch])
            score_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            story.append(score_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Payment History
            story.append(Paragraph("<b>Payment History</b>", heading_style))
            
            ph = report_data['payment_history']
            ph_data = [
                ["On-time Payments:", str(ph['on_time_payments'])],
                ["Late Payments (30 days):", str(ph['late_payments_30_days'])],
                ["Payment Ratio:", f"{ph['payment_ratio']}%"],
            ]
            
            ph_table = Table(ph_data, colWidths=[2*inch, 4*inch])
            ph_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(ph_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Remarks
            story.append(Paragraph("<b>Remarks</b>", heading_style))
            story.append(Paragraph(report_data['remarks'], normal_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Footer
            footer = f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | This is a synthetic report for demonstration purposes</i>"
            story.append(Paragraph(footer, normal_style))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")


# Quick test
if __name__ == "__main__":
    gen = CreditReportGenerator()
    
    print("=" * 60)
    print("CREDIT REPORT GENERATION TEST")
    print("=" * 60)
    
    report = gen.generate_credit_report(
        full_name="Ahmed Al Mazrouei",
        emirates_id="784-1990-123456-7",
        monthly_income=8500,
        total_liabilities=150000
    )
    
    print(f"\nCredit Report Generated:")
    print(f"  Credit Score: {report['credit_score']}/1800")
    print(f"  Rating: {report['credit_rating']}")
    print(f"  On-time Payments: {report['payment_history']['on_time_payments']}")
    print(f"  Accounts: {len(report['credit_accounts'])}")
