"""
Synthetic Data Generator for ML Model Training
Generates realistic applicant data for Random Forest model
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json
from pathlib import Path


class SyntheticDataGenerator:
    """Generate synthetic social support application data"""
    
    def __init__(self, num_samples=1000, seed=42):
        self.num_samples = num_samples
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        # UAE-specific data
        self.nationalities = ["UAE", "Egypt", "India", "Pakistan", "Philippines", "Jordan", "Syria"]
        self.emirates = ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"]
        self.employment_statuses = ["employed", "unemployed", "self_employed", "part_time"]
        self.positions = [
            "Sales Associate", "Driver", "Office Assistant", "Warehouse Worker",
            "Security Guard", "Cashier", "Cleaner", "Technician", "Teacher",
            "Accountant", "Manager", "Engineer", "Nurse", "Construction Worker"
        ]
        
    def generate_dataset(self) -> pd.DataFrame:
        """Generate complete synthetic dataset"""
        print(f"Generating {self.num_samples} synthetic applicants...")
        
        data = []
        
        for i in range(self.num_samples):
            applicant = self._generate_applicant()
            data.append(applicant)
        
        df = pd.DataFrame(data)
        print(f"✓ Generated {len(df)} records")
        return df
    
    def _generate_applicant(self) -> dict:
        """Generate a single applicant profile"""
        
        # Demographics
        age = np.random.randint(22, 65)
        nationality = random.choice(self.nationalities)
        gender = random.choice(["Male", "Female"])
        family_size = np.random.choice([1, 2, 3, 4, 5, 6, 7], p=[0.15, 0.25, 0.25, 0.20, 0.10, 0.04, 0.01])
        
        # Employment
        employment_status = random.choice(self.employment_statuses)
        if employment_status == "employed":
            years_experience = np.random.randint(0, min(age - 18, 30))
            current_position = random.choice(self.positions)
        elif employment_status == "self_employed":
            years_experience = np.random.randint(1, min(age - 18, 20))
            current_position = "Business Owner"
        else:
            years_experience = np.random.randint(0, min(age - 18, 15))
            current_position = "Unemployed"
        
        # Income (correlated with employment and experience)
        if employment_status == "unemployed":
            monthly_income = np.random.uniform(0, 1000)  # Minimal/support income
        elif employment_status == "part_time":
            monthly_income = np.random.uniform(1500, 4000)
        elif employment_status == "self_employed":
            monthly_income = np.random.uniform(2000, 15000)
        else:  # employed
            base_income = 3000 + (years_experience * 200)
            monthly_income = max(2000, np.random.normal(base_income, base_income * 0.3))
        
        monthly_income = round(monthly_income, 2)
        
        # Expenses (correlated with income and family size)
        base_expenses = 1500 + (family_size * 500)
        expense_ratio = np.random.uniform(0.6, 1.2)  # Some people overspend
        monthly_expenses = round(base_expenses * expense_ratio, 2)
        
        # Assets and Liabilities
        # Higher income -> more likely to have assets
        if monthly_income > 8000:
            total_assets = np.random.uniform(20000, 150000)
        elif monthly_income > 5000:
            total_assets = np.random.uniform(10000, 80000)
        elif monthly_income > 3000:
            total_assets = np.random.uniform(5000, 40000)
        else:
            total_assets = np.random.uniform(0, 15000)
        
        # Liabilities (debt)
        if total_assets > 50000:
            total_liabilities = np.random.uniform(5000, 60000)
        elif total_assets > 20000:
            total_liabilities = np.random.uniform(3000, 35000)
        else:
            total_liabilities = np.random.uniform(0, 20000)
        
        net_worth = total_assets - total_liabilities
        
        # Credit score (correlated with income and debt)
        if monthly_income > 8000 and net_worth > 30000:
            credit_score = np.random.randint(700, 850)
        elif monthly_income > 5000 and net_worth > 10000:
            credit_score = np.random.randint(600, 750)
        elif monthly_income > 3000:
            credit_score = np.random.randint(500, 700)
        else:
            credit_score = np.random.randint(400, 650)
        
        # Debt-to-Income ratio
        monthly_debt_payment = total_liabilities * 0.05  # Assume 5% monthly payment
        dti_ratio = (monthly_debt_payment / monthly_income * 100) if monthly_income > 0 else 100
        
        # Calculate net monthly income
        net_monthly_income = monthly_income - monthly_expenses
        
        # **ELIGIBILITY LABEL** - Business Rules
        # Complex logic considering multiple factors
        eligibility_score = 0
        
        # Income factor (0-30 points)
        if monthly_income < 3000:
            eligibility_score += 30
        elif monthly_income < 5000:
            eligibility_score += 20
        elif monthly_income < 8000:
            eligibility_score += 10
        
        # Net income factor (0-20 points)
        if net_monthly_income < 0:
            eligibility_score += 20
        elif net_monthly_income < 1000:
            eligibility_score += 15
        elif net_monthly_income < 2000:
            eligibility_score += 10
        
        # Family size factor (0-15 points)
        if family_size >= 5:
            eligibility_score += 15
        elif family_size >= 3:
            eligibility_score += 10
        elif family_size >= 2:
            eligibility_score += 5
        
        # Net worth factor (0-20 points)
        if net_worth < 0:
            eligibility_score += 20
        elif net_worth < 10000:
            eligibility_score += 15
        elif net_worth < 30000:
            eligibility_score += 10
        elif net_worth < 50000:
            eligibility_score += 5
        
        # Employment factor (0-10 points)
        if employment_status == "unemployed":
            eligibility_score += 10
        elif employment_status == "part_time":
            eligibility_score += 7
        
        # DTI factor (0-5 points)
        if dti_ratio > 50:
            eligibility_score += 5
        elif dti_ratio > 40:
            eligibility_score += 3
        
        # Determine eligibility (threshold: 60 points)
        is_eligible = 1 if eligibility_score >= 60 else 0
        
        # Add some randomness for realism (5% flip)
        if random.random() < 0.05:
            is_eligible = 1 - is_eligible
        
        return {
            # Demographics
            "age": age,
            "nationality": nationality,
            "gender": gender,
            "family_size": family_size,
            "emirate": random.choice(self.emirates),
            
            # Employment
            "employment_status": employment_status,
            "years_of_experience": years_experience,
            "current_position": current_position,
            
            # Financial
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "net_monthly_income": net_monthly_income,
            "total_assets": round(total_assets, 2),
            "total_liabilities": round(total_liabilities, 2),
            "net_worth": round(net_worth, 2),
            "credit_score": credit_score,
            "dti_ratio": round(dti_ratio, 2),
            
            # Target variable
            "is_eligible": is_eligible,
            "eligibility_score": eligibility_score
        }
    
    def save_dataset(self, df: pd.DataFrame, output_dir: str = "data/synthetic"):
        """Save dataset to CSV and JSON"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save CSV
        csv_path = f"{output_dir}/synthetic_applicants_{self.num_samples}.csv"
        df.to_csv(csv_path, index=False)
        print(f"✓ Saved CSV: {csv_path}")
        
        # Save JSON
        json_path = f"{output_dir}/synthetic_applicants_{self.num_samples}.json"
        df.to_json(json_path, orient="records", indent=2)
        print(f"✓ Saved JSON: {json_path}")
        
        # Save statistics
        stats = {
            "total_samples": len(df),
            "eligible_count": int(df["is_eligible"].sum()),
            "eligible_percentage": float(df["is_eligible"].mean() * 100),
            "average_income": float(df["monthly_income"].mean()),
            "average_family_size": float(df["family_size"].mean()),
            "employment_distribution": df["employment_status"].value_counts().to_dict(),
            "generated_at": datetime.now().isoformat()
        }
        
        stats_path = f"{output_dir}/dataset_statistics.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Saved Statistics: {stats_path}")
        
        return csv_path, json_path, stats_path
    
    def generate_sample_documents(self, applicant_data: dict, output_dir: str = "data/synthetic/documents"):
        """Generate sample document text for testing"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Emirates ID text
        emirates_id_text = f"""
EMIRATES ID CARD
════════════════════════════════════════════
Name: {applicant_data.get('name', 'Ahmed Mohammed Al-Rashid')}
ID Number: 784-{random.randint(1980, 2000)}-{random.randint(1000000, 9999999)}-1
Nationality: {applicant_data['nationality']}
Date of Birth: {random.randint(1960, 2003)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}
Gender: {applicant_data['gender']}
Address: {applicant_data['emirate']}, UAE
════════════════════════════════════════════
"""
        
        # Bank statement text
        bank_statement_text = f"""
BANK STATEMENT
════════════════════════════════════════════
Account Holder: {applicant_data.get('name', 'Ahmed Mohammed Al-Rashid')}
Account Number: ****{random.randint(1000, 9999)}
Statement Period: Last 6 months

Average Monthly Balance: {applicant_data['total_assets'] * 0.3:.2f} AED
Monthly Credit (Income): {applicant_data['monthly_income']:.2f} AED
Monthly Debit (Expenses): {applicant_data['monthly_expenses']:.2f} AED

Transaction Summary:
- Salary Credits: {applicant_data['monthly_income']:.2f} AED
- Rent Payments: {applicant_data['monthly_expenses'] * 0.4:.2f} AED
- Utilities: {applicant_data['monthly_expenses'] * 0.15:.2f} AED
- Food & Groceries: {applicant_data['monthly_expenses'] * 0.25:.2f} AED
- Other: {applicant_data['monthly_expenses'] * 0.2:.2f} AED
════════════════════════════════════════════
"""
        
        # Resume text
        resume_text = f"""
CURRICULUM VITAE
════════════════════════════════════════════
{applicant_data.get('name', 'Ahmed Mohammed Al-Rashid')}
{applicant_data['emirate']}, UAE
Phone: +971-XX-XXXXXXX
Email: ahmed@example.com

CURRENT POSITION
{applicant_data['current_position']}
{'Current Employer LLC' if applicant_data['employment_status'] == 'employed' else 'Seeking Employment'}

EXPERIENCE
Total Experience: {applicant_data['years_of_experience']} years
Employment Status: {applicant_data['employment_status'].title()}

EDUCATION
High School Diploma - 2003
{random.choice(['Bachelor Degree', 'Diploma', 'Certificate']) if applicant_data['years_of_experience'] > 5 else ''}

SKILLS
Customer Service, Communication, {'Technical Skills' if applicant_data['years_of_experience'] > 5 else 'Basic Skills'}
Languages: Arabic, English
════════════════════════════════════════════
"""
        
        # Assets/Liabilities Excel data (as text)
        assets_liabilities_text = f"""
ASSETS & LIABILITIES STATEMENT
════════════════════════════════════════════
ASSETS:
Savings Account: {applicant_data['total_assets'] * 0.4:.2f} AED
Vehicle: {applicant_data['total_assets'] * 0.5:.2f} AED
Other Assets: {applicant_data['total_assets'] * 0.1:.2f} AED
TOTAL ASSETS: {applicant_data['total_assets']:.2f} AED

LIABILITIES:
Car Loan: {applicant_data['total_liabilities'] * 0.6:.2f} AED
Credit Card: {applicant_data['total_liabilities'] * 0.3:.2f} AED
Personal Loan: {applicant_data['total_liabilities'] * 0.1:.2f} AED
TOTAL LIABILITIES: {applicant_data['total_liabilities']:.2f} AED

NET WORTH: {applicant_data['net_worth']:.2f} AED
════════════════════════════════════════════
"""
        
        # Credit report
        credit_report_text = f"""
CREDIT BUREAU REPORT
════════════════════════════════════════════
Applicant: {applicant_data.get('name', 'Ahmed Mohammed Al-Rashid')}
Report Date: {datetime.now().strftime('%Y-%m-%d')}

CREDIT SCORE: {applicant_data['credit_score']}
Rating: {
    'Excellent' if applicant_data['credit_score'] > 750 else
    'Good' if applicant_data['credit_score'] > 650 else
    'Fair' if applicant_data['credit_score'] > 550 else 'Poor'
}

Payment History: {'Good' if applicant_data['credit_score'] > 600 else 'Fair'}
Outstanding Debt: {applicant_data['total_liabilities']:.2f} AED
Credit Utilization: {applicant_data['dti_ratio']:.1f}%
════════════════════════════════════════════
"""
        
        return {
            "emirates_id": emirates_id_text,
            "bank_statement": bank_statement_text,
            "resume": resume_text,
            "assets_liabilities": assets_liabilities_text,
            "credit_report": credit_report_text
        }


def main():
    """Generate synthetic dataset"""
    print("=" * 60)
    print("SYNTHETIC DATA GENERATOR")
    print("=" * 60)
    
    # Generate dataset
    generator = SyntheticDataGenerator(num_samples=1000)
    df = generator.generate_dataset()
    
    # Display statistics
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    print(f"Total Samples: {len(df)}")
    print(f"Eligible: {df['is_eligible'].sum()} ({df['is_eligible'].mean() * 100:.1f}%)")
    print(f"Not Eligible: {(1 - df['is_eligible']).sum()} ({(1 - df['is_eligible']).mean() * 100:.1f}%)")
    print(f"\nAverage Monthly Income: {df['monthly_income'].mean():.2f} AED")
    print(f"Average Family Size: {df['family_size'].mean():.1f}")
    print(f"Average Net Worth: {df['net_worth'].mean():.2f} AED")
    print(f"\nEmployment Distribution:")
    print(df['employment_status'].value_counts())
    
    # Save dataset
    print("\n" + "=" * 60)
    print("SAVING DATASET")
    print("=" * 60)
    csv_path, json_path, stats_path = generator.save_dataset(df)
    
    # Generate sample documents for first 5 applicants
    print("\n" + "=" * 60)
    print("GENERATING SAMPLE DOCUMENTS")
    print("=" * 60)
    for i in range(min(5, len(df))):
        applicant = df.iloc[i].to_dict()
        applicant['name'] = f"Applicant_{i+1}"
        docs = generator.generate_sample_documents(applicant)
        
        doc_dir = f"data/synthetic/documents/applicant_{i+1}"
        Path(doc_dir).mkdir(parents=True, exist_ok=True)
        
        for doc_type, content in docs.items():
            doc_path = f"{doc_dir}/{doc_type}.txt"
            with open(doc_path, "w") as f:
                f.write(content)
        
        print(f"✓ Generated documents for Applicant {i+1}")
    
    print("\n" + "=" * 60)
    print("✓ SYNTHETIC DATA GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
