"""
BankStatementGenerator: Generate realistic PDF bank statements
3-month transaction history with income deposits and expenses
M1-optimized, production-grade
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .config import EXPENSE_CATEGORIES


class BankStatementGenerator:
    """Generate realistic UAE bank statement PDFs."""
    
    BANKS = {
        "FAB": "First Abu Dhabi Bank",
        "ADIB": "Abu Dhabi Islamic Bank",
        "Emirates Islamic": "Emirates Islamic Bank",
        "Mashreq": "Mashreq Bank",
        "DIB": "Dubai Islamic Bank"
    }
    
    def __init__(self):
        """Initialize BankStatementGenerator."""
        self.banks = list(self.BANKS.items())
    
    def generate_statement(
        self,
        account_holder: str,
        monthly_income: float,
        family_size: int,
        num_months: int = 3,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate bank statement for a person.
        
        Args:
            account_holder: Full name of account holder
            monthly_income: Monthly salary in AED
            family_size: Number of family members (for realistic expenses)
            num_months: Number of months to generate (default 3)
            output_path: Path to save PDF (optional)
            
        Returns:
            Dict: Statement data and file path
        """
        bank_code, bank_name = random.choice(self.banks)
        account_number = self._generate_account_number()
        
        # Generate transaction history
        transactions = self._generate_transactions(
            monthly_income=monthly_income,
            family_size=family_size,
            num_months=num_months
        )
        
        # Calculate statistics
        total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
        total_expenses = sum(abs(t["amount"]) for t in transactions if t["amount"] < 0)
        average_balance = self._calculate_average_balance(transactions)
        
        statement_data = {
            "bank_name": bank_name,
            "bank_code": bank_code,
            "account_holder": account_holder,
            "account_number": account_number,
            "account_type": random.choice(["Savings", "Checking"]),
            "currency": "AED",
            "statement_period": f"Last {num_months} months",
            "transactions": transactions,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "average_balance": average_balance,
            "average_monthly_income": total_income / num_months,
            "current_balance": average_balance * 0.8 + random.randint(-5000, 5000)
        }
        
        # Generate PDF if output path provided
        if output_path:
            self._generate_pdf(statement_data, output_path)
            statement_data["pdf_path"] = output_path
        
        return statement_data
    
    def _generate_account_number(self) -> str:
        """
        Generate realistic UAE bank account number.
        
        Returns:
            str: Account number
        """
        return f"{random.randint(100000000, 999999999)}"
    
    def _generate_transactions(
        self,
        monthly_income: float,
        family_size: int,
        num_months: int
    ) -> List[Dict[str, Any]]:
        """
        Generate realistic transaction history.
        
        Args:
            monthly_income: Monthly salary in AED
            family_size: Number of family members
            num_months: Number of months
            
        Returns:
            List: Transaction records
        """
        transactions = []
        today = datetime.now()
        
        for month in range(num_months):
            # Income: Usually on 1st or middle of month
            income_day = random.choice([1, 15])
            income_date = today - timedelta(days=30*month - income_day)
            
            # Add slight variance to income (±5%)
            actual_income = monthly_income * random.uniform(0.95, 1.05)
            
            transactions.append({
                "date": income_date.strftime("%Y-%m-%d"),
                "description": "Salary Deposit",
                "amount": round(actual_income, 2),
                "balance": None  # Will be calculated
            })
            
            # Generate daily expenses spread across the month
            for day in range(1, 30):
                if random.random() < 0.7:  # 70% chance of transaction on any day
                    expense_date = today - timedelta(days=30*month - day)
                    
                    # Choose random expense category
                    category = random.choice(list(EXPENSE_CATEGORIES.keys()))
                    min_amount, max_amount = EXPENSE_CATEGORIES[category]
                    amount = -round(random.uniform(min_amount, max_amount), 2)
                    
                    # Adjust expenses based on family size
                    amount *= (1 + (family_size - 1) * 0.15)
                    amount = round(amount, 2)
                    
                    transactions.append({
                        "date": expense_date.strftime("%Y-%m-%d"),
                        "description": f"{category} - Debit",
                        "amount": amount,
                        "balance": None
                    })
        
        # Sort by date
        transactions.sort(key=lambda x: x["date"])
        
        # Calculate running balance
        balance = random.randint(10000, 50000)  # Starting balance
        for transaction in transactions:
            balance += transaction["amount"]
            transaction["balance"] = max(0, round(balance, 2))  # Don't go negative
        
        return transactions
    
    def _calculate_average_balance(self, transactions: List[Dict]) -> float:
        """
        Calculate average balance from transactions.
        
        Args:
            transactions: List of transactions
            
        Returns:
            float: Average balance
        """
        if not transactions:
            return 0
        
        balances = [t["balance"] for t in transactions if t["balance"]]
        return sum(balances) / len(balances) if balances else 0
    
    def _generate_pdf(self, statement_data: Dict[str, Any], output_path: str) -> None:
        """
        Generate PDF bank statement.
        
        Args:
            statement_data: Statement data dictionary
            output_path: Path to save PDF
        """
        try:
            # Create PDF
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
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=6,
                alignment=TA_CENTER
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=11,
                textColor=colors.HexColor('#1f4788'),
                spaceAfter=3,
                alignment=TA_LEFT
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=2,
                alignment=TA_LEFT
            )
            
            # Header
            story.append(Paragraph(f"<b>{statement_data['bank_name']}</b>", title_style))
            story.append(Spacer(1, 0.1*inch))
            
            # Account Information
            info_data = [
                ["Account Holder:", statement_data["account_holder"]],
                ["Account Number:", statement_data["account_number"]],
                ["Account Type:", statement_data["account_type"]],
                ["Currency:", statement_data["currency"]],
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f4788')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Summary
            story.append(Paragraph("<b>Statement Summary</b>", heading_style))
            
            summary_data = [
                ["Average Monthly Income:", f"AED {statement_data['average_monthly_income']:,.2f}"],
                ["Total Expenses (3 months):", f"AED {statement_data['total_expenses']:,.2f}"],
                ["Average Balance:", f"AED {statement_data['average_balance']:,.2f}"],
                ["Current Balance:", f"AED {statement_data['current_balance']:,.2f}"],
            ]
            
            summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
            summary_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1f4788')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Transactions
            story.append(Paragraph("<b>Recent Transactions</b>", heading_style))
            
            # Show last 30 transactions only for PDF brevity
            trans_data = [["Date", "Description", "Amount", "Balance"]]
            for trans in statement_data["transactions"][-30:]:
                trans_data.append([
                    trans["date"],
                    trans["description"][:30],
                    f"AED {trans['amount']:,.2f}",
                    f"AED {trans['balance']:,.2f}"
                ])
            
            trans_table = Table(trans_data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 1.1*inch])
            trans_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            
            story.append(trans_table)
            story.append(Spacer(1, 0.2*inch))
            
            # Footer
            footer_text = f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | This is a synthetic statement for demonstration purposes</i>"
            story.append(Paragraph(footer_text, normal_style))
            
            # Build PDF
            doc.build(story)
            
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")


# Quick test
if __name__ == "__main__":
    gen = BankStatementGenerator()
    
    print("=" * 60)
    print("BANK STATEMENT GENERATION TEST")
    print("=" * 60)
    
    statement = gen.generate_statement(
        account_holder="Ahmed Al Mazrouei",
        monthly_income=8500,
        family_size=4,
        num_months=3
    )
    
    print(f"\nBank: {statement['bank_name']}")
    print(f"Account Holder: {statement['account_holder']}")
    print(f"Average Monthly Income: AED {statement['average_monthly_income']:,.2f}")
    print(f"Average Balance: AED {statement['average_balance']:,.2f}")
    print(f"Total Transactions: {len(statement['transactions'])}")
