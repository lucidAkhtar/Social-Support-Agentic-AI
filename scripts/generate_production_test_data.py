#!/usr/bin/env python3
"""
FAANG-Grade Test Data Generation for Social Support System
Generates realistic data with proper distribution:
- 4 APPROVED cases (low income, high need)
- 4 SOFT_DECLINE cases (borderline eligibility)
- 2 REJECT cases (high income, low need)

Author: Production Data Engineering Team
Version: 2.0 - Fixed Logic for Social Support Context
"""

import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.synthetic_generators.master_dataset_generator import MasterDatasetGenerator


class ProductionTestDataGenerator:
    """
    FAANG-grade test data generation with proper quality controls.
    
    Social Support Logic:
    - LOW income + HIGH need = APPROVED
    - MEDIUM income + MEDIUM need = SOFT_DECLINE  
    - HIGH income + LOW need = REJECT
    """
    
    def __init__(self, output_dir: str = "data/test_applications"):
        self.output_dir = Path(output_dir)
        self.generator = MasterDatasetGenerator(seed=42, base_path="data")
        
    def generate_production_test_set(self) -> Dict[str, Any]:
        """Generate production-grade test dataset with proper distribution."""
        
        print("=" * 80)
        print("FAANG-GRADE TEST DATA GENERATION")
        print("=" * 80)
        print("\nSocial Support Context:")
        print("  ✓ LOW income + HIGH family need = APPROVED")
        print("  ✓ MEDIUM income + MEDIUM need = SOFT_DECLINE")
        print("  ✓ HIGH income + LOW need = REJECT")
        print("=" * 80)
        
        # Clear existing test data
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Override generator's document path to test_applications
        self.generator.documents_path = self.output_dir
        
        # Generate test cases
        test_cases = []
        
        # APPROVED CASES (4) - Clear eligibility
        print("\n[1/3] Generating 4 APPROVED cases (LOW income, HIGH need)...")
        approved_profiles = self._create_approved_profiles()
        for i, profile in enumerate(approved_profiles, 1):
            case_id = f"approved_{i}"
            app = self._generate_application(case_id, profile)
            test_cases.append(app)
            print(f"  ✓ {case_id}: {profile['name']} - Income: {profile['monthly_income']:,} AED, Family: {profile['family_size']}")
        
        # SOFT_DECLINE CASES (4) - Borderline eligibility
        print("\n[2/3] Generating 4 SOFT_DECLINE cases (BORDERLINE eligibility)...")
        soft_decline_profiles = self._create_soft_decline_profiles()
        for i, profile in enumerate(soft_decline_profiles, 1):
            case_id = f"soft_decline_{i}"
            app = self._generate_application(case_id, profile)
            test_cases.append(app)
            print(f"  ✓ {case_id}: {profile['name']} - Income: {profile['monthly_income']:,} AED, Family: {profile['family_size']}")
        
        # REJECT CASES (2) - Clear ineligibility
        print("\n[3/3] Generating 2 REJECT cases (HIGH income, LOW need)...")
        reject_profiles = self._create_reject_profiles()
        for i, profile in enumerate(reject_profiles, 1):
            case_id = f"reject_{i}"
            app = self._generate_application(case_id, profile)
            test_cases.append(app)
            print(f"  ✓ {case_id}: {profile['name']} - Income: {profile['monthly_income']:,} AED, Family: {profile['family_size']}")
        
        # Save metadata
        self._save_metadata(test_cases)
        
        summary = {
            "total_applications": len(test_cases),
            "approved": 4,
            "soft_decline": 4,
            "reject": 2,
            "output_directory": str(self.output_dir),
            "timestamp": datetime.now().isoformat()
        }
        
        print("\n" + "=" * 80)
        print("✓ GENERATION COMPLETE")
        print("=" * 80)
        print(f"\n  Total Applications: {summary['total_applications']}")
        print(f"  • APPROVED:      {summary['approved']} cases")
        print(f"  • SOFT_DECLINE:  {summary['soft_decline']} cases")
        print(f"  • REJECT:        {summary['reject']} cases")
        print(f"\n  Output: {summary['output_directory']}")
        print("=" * 80)
        
        return summary
    
    def _create_approved_profiles(self) -> List[Dict[str, Any]]:
        """Create 4 APPROVED profiles - LOW income, HIGH need."""
        return [
            {
                "name": "Fatima Al Kaabi",
                "monthly_income": 4200,  # Very low income
                "family_size": 6,  # Large family = HIGH need
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Rent",
                "employment_years": 3,
                "total_assets": 15000,  # Low assets
                "total_liabilities": 8000,  # Some debt
                "credit_score": 650,  # Fair credit
                "scenario": "Single income, large family, financial hardship"
            },
            {
                "name": "Ahmed Al Hosani",
                "monthly_income": 5500,  # Low income
                "family_size": 5,  # Large family
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Rent",
                "employment_years": 5,
                "total_assets": 22000,
                "total_liabilities": 15000,
                "credit_score": 700,
                "scenario": "Low income with dependents, needs support"
            },
            {
                "name": "Mariam Al Qubaisi",
                "monthly_income": 3800,  # Very low income
                "family_size": 4,  # Medium family
                "employment_status": "unemployed",  # Unemployed = HIGH need
                "marital_status": "Divorced",  # Single parent
                "housing": "Live with family",
                "employment_years": 0,
                "total_assets": 8000,  # Minimal assets
                "total_liabilities": 5000,
                "credit_score": 580,  # Poor credit
                "scenario": "Unemployed single mother, urgent need"
            },
            {
                "name": "Hassan Al Mazrouei",
                "monthly_income": 6200,  # Low income
                "family_size": 5,  # Large family
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Rent",
                "employment_years": 4,
                "total_assets": 18000,
                "total_liabilities": 12000,
                "credit_score": 680,
                "scenario": "Low wage worker with large family"
            }
        ]
    
    def _create_soft_decline_profiles(self) -> List[Dict[str, Any]]:
        """Create 4 SOFT_DECLINE profiles - BORDERLINE eligibility."""
        return [
            {
                "name": "Layla Al Suwaidi",
                "monthly_income": 8500,  # At threshold
                "family_size": 3,  # Small family = MEDIUM need
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Rent",
                "employment_years": 6,
                "total_assets": 35000,
                "total_liabilities": 20000,
                "credit_score": 720,
                "scenario": "Income at threshold, modest family, borderline"
            },
            {
                "name": "Omar Al Dhaheri",
                "monthly_income": 9200,  # Slightly above threshold
                "family_size": 4,  # Medium family
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Rent",
                "employment_years": 7,
                "total_assets": 42000,
                "total_liabilities": 28000,
                "credit_score": 750,
                "scenario": "Income slightly high, some assets, borderline"
            },
            {
                "name": "Sara Al Mansoori",
                "monthly_income": 7800,  # Below threshold
                "family_size": 2,  # Small family = LOWER need
                "employment_status": "employed",
                "marital_status": "Single",
                "housing": "Rent",
                "employment_years": 5,
                "total_assets": 55000,  # Higher assets
                "total_liabilities": 18000,
                "credit_score": 780,
                "scenario": "Good credit and assets despite low income"
            },
            {
                "name": "Khalid Al Bloushi",
                "monthly_income": 8800,  # At threshold
                "family_size": 3,  # Medium family
                "employment_status": "self_employed",  # Variable income
                "marital_status": "Married",
                "housing": "Own (with mortgage)",
                "employment_years": 8,
                "total_assets": 150000,  # Property ownership
                "total_liabilities": 125000,  # High mortgage
                "credit_score": 740,
                "scenario": "Property owner, self-employed, borderline"
            }
        ]
    
    def _create_reject_profiles(self) -> List[Dict[str, Any]]:
        """Create 2 REJECT profiles - HIGH income, LOW need."""
        return [
            {
                "name": "Noor Al Maktoum",
                "monthly_income": 25000,  # HIGH income
                "family_size": 2,  # Small family = LOW need
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Own (paid off)",
                "employment_years": 12,
                "total_assets": 450000,  # Wealthy
                "total_liabilities": 50000,
                "credit_score": 850,  # Excellent credit
                "scenario": "High income professional, no financial need"
            },
            {
                "name": "Rashid Al Nuaimi",
                "monthly_income": 35000,  # Very HIGH income
                "family_size": 3,  # Medium family
                "employment_status": "employed",
                "marital_status": "Married",
                "housing": "Own (paid off)",
                "employment_years": 15,
                "total_assets": 800000,  # Very wealthy
                "total_liabilities": 30000,
                "credit_score": 900,  # Perfect credit
                "scenario": "Executive level income, clearly ineligible"
            }
        ]
    
    def _generate_application(self, case_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete application with all documents."""
        
        # Generate person data
        person_data = self.generator.person_gen.generate_person()
        person_data['full_name'] = profile['name']
        person_data['family_size'] = profile['family_size']
        
        # Create application directory
        app_dir = self.output_dir / case_id
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate documents
        # 1. Bank Statement
        bank_stmt = self.generator.bank_gen.generate_statement(
            account_holder=profile['name'],
            monthly_income=profile['monthly_income'],
            family_size=profile['family_size'],
            output_path=str(app_dir / "bank_statement.pdf")
        )
        
        # 2. Emirates ID
        id_doc = self.generator.id_gen.generate_id_card(
            full_name=profile['name'],
            emirates_id=person_data['emirates_id'],
            date_of_birth=person_data['date_of_birth'],
            output_path=str(app_dir / "emirates_id.png")
        )
        
        # 3. Employment Letter (if employed)
        if profile['employment_status'] in ['employed', 'self_employed']:
            employment_letter = self.generator.employment_gen.generate_letter(
                employee_name=profile['name'],
                monthly_salary=profile['monthly_income'],
                years_employed=profile['employment_years'],
                position="Administrative Officer" if profile['monthly_income'] < 8000 else "Manager",
                employment_type=profile['employment_status'],
                output_path=str(app_dir / "employment_letter.pdf")
            )
        else:
            employment_letter = None
        
        # 4. Resume
        resume = self.generator.resume_gen.generate_resume(
            full_name=profile['name'],
            email=person_data['email'],
            phone=person_data['phone'],
            education_level=profile.get('education', "Bachelor's Degree"),
            current_position="Administrative Officer" if profile['monthly_income'] < 8000 else "Manager",
            years_experience=profile['employment_years'],
            current_employer="Private Sector Company",
            employment_type=profile['employment_status'],
            output_path=str(app_dir / "resume.pdf")
        )
        
        # 5. Assets & Liabilities
        assets_liab = self.generator.asset_gen.generate_assets_liabilities(
            full_name=profile['name'],
            monthly_income=profile['monthly_income'],
            family_size=profile['family_size'],
            housing_type=profile['housing'],
            output_path=str(app_dir / "assets_liabilities.xlsx")
        )
        
        # Override with specific values if provided
        if 'total_assets' in profile:
            assets_liab['total_assets'] = profile['total_assets']
            assets_liab['total_liabilities'] = profile.get('total_liabilities', 0)
        
        # 6. Credit Report
        credit_report = self.generator.credit_gen.generate_credit_report(
            full_name=profile['name'],
            emirates_id=person_data['emirates_id'],
            monthly_income=profile['monthly_income'],
            total_liabilities=profile.get('total_liabilities', 0),
            output_json_path=str(app_dir / "credit_report.json"),
            output_pdf_path=str(app_dir / "credit_report.pdf")
        )
        
        # Build application record
        application = {
            "application_id": case_id.upper(),
            "case_id": case_id,
            "full_name": profile['name'],
            "monthly_income": profile['monthly_income'],
            "family_size": profile['family_size'],
            "employment_status": profile['employment_status'],
            "marital_status": profile['marital_status'],
            "housing_type": profile['housing'],
            "employment_years": profile['employment_years'],
            "total_assets": profile.get('total_assets', 0),
            "total_liabilities": profile.get('total_liabilities', 0),
            "net_worth": profile.get('total_assets', 0) - profile.get('total_liabilities', 0),
            "credit_score": profile.get('credit_score', 700),
            "scenario": profile['scenario'],
            "documents_path": str(app_dir),
            "timestamp": datetime.now().isoformat()
        }
        
        return application
    
    def _save_metadata(self, applications: List[Dict[str, Any]]):
        """Save metadata JSON file."""
        metadata_file = self.output_dir.parent / "test_applications_metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump({
                "applications": applications,
                "total_count": len(applications),
                "distribution": {
                    "approved": 4,
                    "soft_decline": 4,
                    "reject": 2
                },
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n  ✓ Metadata saved: {metadata_file}")


def main():
    """Generate production-grade test dataset."""
    
    generator = ProductionTestDataGenerator()
    summary = generator.generate_production_test_set()
    
    print("\n✨ Production-grade test data ready for demo!")
    print(f"   Run E2E test with: python tests/test_real_files_e2e.py\n")
    
    return summary


if __name__ == "__main__":
    main()
