"""
MasterDatasetGenerator: Orchestrate all generators to create complete datasets
Ensures consistency across all documents, generates 10/100/500 applications
Production-ready with proper logging and progress tracking
"""

import os
import json
import csv
import random
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .person_generator import PersonGenerator
from .bank_statement_generator import BankStatementGenerator
from .emirates_id_generator import EmiratesIDGenerator
from .employment_letter_generator import EmploymentLetterGenerator
from .resume_generator import ResumeGenerator
from .asset_generator import AssetLiabilityGenerator
from .credit_report_generator import CreditReportGenerator
from .config import (
    TEST_CASE_PROFILES,
    INCOME_DISTRIBUTION,
    INCOME_RANGES,
    FAMILY_SIZE_DISTRIBUTION,
    HOUSING_DISTRIBUTION,
    EmploymentType,
    GOVERNMENT_EMPLOYERS,
    PRIVATE_EMPLOYERS,
    JOB_TITLES,
    DEFAULT_RANDOM_SEED
)


class MasterDatasetGenerator:
    """Master orchestrator for complete dataset generation."""
    
    def __init__(self, seed: int = DEFAULT_RANDOM_SEED, base_path: str = "data"):
        """
        Initialize MasterDatasetGenerator.
        
        Args:
            seed: Random seed for reproducibility
            base_path: Base path for data output
        """
        if seed is not None:
            random.seed(seed)
        
        self.seed = seed
        self.base_path = Path(base_path)
        self.documents_path = self.base_path / "processed" / "documents"
        self.raw_path = self.base_path / "raw"
        
        # Create directories
        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.raw_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize generators
        self.person_gen = PersonGenerator(seed)
        self.bank_gen = BankStatementGenerator()
        self.id_gen = EmiratesIDGenerator()
        self.employment_gen = EmploymentLetterGenerator()
        self.resume_gen = ResumeGenerator()
        self.asset_gen = AssetLiabilityGenerator()
        self.credit_gen = CreditReportGenerator()
        
        self.applications = []
    
    def generate_dataset(
        self,
        test_cases: int = 10,
        training_size: int = 100,
        bulk_size: int = 500
    ) -> Dict[str, Any]:
        """
        Generate complete dataset.
        
        Args:
            test_cases: Number of curated test cases
            training_size: Number of training applications
            bulk_size: Number of bulk applications
            
        Returns:
            Dict: Summary of generated data
        """
        print("\n" + "="*70)
        print("MASTER DATASET GENERATION")
        print("="*70)
        
        # Generate test cases
        print(f"\n[1/3] Generating {test_cases} curated test cases...")
        test_apps = self._generate_test_cases(test_cases)
        self.applications.extend(test_apps)
        
        # Generate training dataset
        print(f"[2/3] Generating {training_size} training applications...")
        training_apps = self._generate_random_applications(training_size, "training")
        self.applications.extend(training_apps)
        
        # Generate bulk dataset
        print(f"[3/3] Generating {bulk_size} bulk applications...")
        bulk_apps = self._generate_random_applications(bulk_size, "bulk")
        self.applications.extend(bulk_apps)
        
        # Save metadata
        self._save_metadata()
        
        summary = {
            "total_applications": len(self.applications),
            "test_cases": test_cases,
            "training": training_size,
            "bulk": bulk_size,
            "documents_generated": len(self.applications) * 6,  # 6 docs per app
            "base_path": str(self.base_path),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n{'='*70}")
        print(f"✓ Dataset generation complete!")
        print(f"  Total Applications: {summary['total_applications']}")
        print(f"  Total Documents: {summary['documents_generated']}")
        print(f"  Location: {summary['base_path']}")
        print(f"{'='*70}\n")
        
        return summary
    
    def _generate_test_cases(self, num_cases: int) -> List[Dict[str, Any]]:
        """
        Generate curated test cases from configuration.
        
        Args:
            num_cases: Number of test cases to generate
            
        Returns:
            List: Test case applications
        """
        test_apps = []
        
        # Get configured test cases
        configured_tests = list(TEST_CASE_PROFILES.items())[:num_cases]
        
        for test_id, profile in configured_tests:
            print(f"  • {test_id}: {profile['name']} - {profile['scenario']}")
            
            app = self._create_application(
                name=profile['name'],
                monthly_income=profile['monthly_income'],
                family_size=profile['family_size'],
                employment_status=profile.get('employment_status'),
                marital_status=profile.get('marital_status'),
                housing_type=profile.get('housing'),
                employment_years=profile.get('employment_years', 3),
                app_type="test",
                test_id=test_id,
                special_profile=profile
            )
            
            test_apps.append(app)
        
        return test_apps
    
    def _generate_random_applications(
        self,
        num_applications: int,
        app_type: str = "training"
    ) -> List[Dict[str, Any]]:
        """
        Generate random applications following distributions.
        
        Args:
            num_applications: Number of applications to generate
            app_type: Type of application ("training" or "bulk")
            
        Returns:
            List: Generated applications
        """
        apps = []
        
        for i in range(num_applications):
            # Generate basic person data
            person = self.person_gen.generate_person()
            
            # Determine income level based on distribution
            income_level = random.choices(
                list(INCOME_RANGES.keys()),
                weights=[INCOME_DISTRIBUTION[k] for k in INCOME_RANGES.keys()],
                k=1
            )[0]
            
            monthly_income = random.uniform(*INCOME_RANGES[income_level])
            
            # Determine employment status based on income
            if monthly_income < 3000:
                employment_status = "Unemployed"
                employment_years = 0
                employer = None
                position = None
            else:
                employment_status = random.choices(
                    ["Government", "Private", "Self-employed"],
                    weights=[0.35, 0.40, 0.25],
                    k=1
                )[0]
                employment_years = random.randint(1, 15)
                
                if employment_status == "Government":
                    employer = random.choice(GOVERNMENT_EMPLOYERS)[1]
                    position = random.choice(JOB_TITLES["Government"])
                elif employment_status == "Private":
                    employer = random.choice(PRIVATE_EMPLOYERS)[1]
                    position = random.choice(JOB_TITLES["Private"])
                else:
                    employer = None
                    position = random.choice(JOB_TITLES["Self-employed"])
            
            # Housing type
            housing_type = random.choices(
                list(HOUSING_DISTRIBUTION.keys()),
                weights=[HOUSING_DISTRIBUTION[k] for k in HOUSING_DISTRIBUTION.keys()],
                k=1
            )[0]
            
            # Create application
            app = self._create_application(
                name=person['full_name'],
                monthly_income=round(monthly_income, 0),
                family_size=person['family_size'],
                employment_status=employment_status,
                marital_status=person['marital_status'],
                housing_type=housing_type,
                employment_years=employment_years,
                app_type=app_type,
                test_id=None,
                person_data=person,
                employer=employer,
                position=position
            )
            
            apps.append(app)
            
            # Progress indicator
            if (i + 1) % 50 == 0:
                print(f"  • Generated {i + 1}/{num_applications}")
        
        print(f"  • Generated {num_applications}/{num_applications} ✓")
        return apps
    
    def _create_application(
        self,
        name: str,
        monthly_income: float,
        family_size: int,
        employment_status: str,
        marital_status: str,
        housing_type: str,
        employment_years: int,
        app_type: str,
        test_id: str = None,
        special_profile: Dict = None,
        person_data: Dict = None,
        employer: str = None,
        position: str = None
    ) -> Dict[str, Any]:
        """
        Create complete application with all documents.
        
        Args:
            name, monthly_income, family_size, etc.: Application details
            app_type: Type ("test", "training", "bulk")
            test_id: Test case ID if applicable
            special_profile: Special profile configurations
            person_data: Pre-generated person data
            employer: Employer name
            position: Job position
            
        Returns:
            Dict: Complete application record
        """
        # Generate or use provided person data
        if person_data is None:
            person_data = self.person_gen.generate_person()
        else:
            # Ensure name and family size match
            person_data['full_name'] = name
            person_data['family_size'] = family_size
        
        # Create application directory
        app_id = f"APP-{len(self.applications) + 1:06d}"
        app_dir = self.documents_path / app_id
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Handle special income cases
        actual_income = monthly_income
        if special_profile and special_profile.get('income_variable'):
            # Variable income (self-employed)
            actual_income = monthly_income * random.uniform(0.8, 1.2)
        elif special_profile and special_profile.get('secondary_income'):
            actual_income = monthly_income + special_profile.get('secondary_income', 0)
        
        # Handle special asset cases
        total_assets = 0
        total_liabilities = 0
        
        if special_profile and special_profile.get('total_assets'):
            total_assets = special_profile['total_assets']
            total_liabilities = special_profile.get('total_liabilities', 0)
        
        # Generate documents
        # 1. Bank Statement
        bank_stmt = self.bank_gen.generate_statement(
            account_holder=person_data['full_name'],
            monthly_income=actual_income,
            family_size=family_size,
            output_path=str(app_dir / "bank_statement.pdf")
        )
        
        # 2. Emirates ID
        id_card = self.id_gen.generate_id_card(
            full_name=person_data['full_name'],
            emirates_id=person_data['emirates_id'],
            date_of_birth=person_data['date_of_birth'],
            output_path=str(app_dir / "emirates_id.png")
        )
        
        # 3. Employment Letter (if employed)
        employment_letter = None
        if employment_status != "Unemployed":
            employment_letter = self.employment_gen.generate_letter(
                employee_name=person_data['full_name'],
                monthly_salary=actual_income,
                years_employed=employment_years,
                position=position,
                employment_type=employment_status,
                output_path=str(app_dir / "employment_letter.pdf")
            )
        
        # 4. Resume
        resume = self.resume_gen.generate_resume(
            full_name=person_data['full_name'],
            email=person_data['email'],
            phone=person_data['phone'],
            education_level=person_data['education_level'],
            current_position=position or "Job Seeker",
            years_experience=employment_years,
            current_employer=employer,
            employment_type=employment_status,
            output_path=str(app_dir / "resume.pdf")
        )
        
        # 5. Assets & Liabilities
        if housing_type != "Live with family":
            if "Own" in housing_type:
                total_liabilities = max(100000, monthly_income * 12 * random.uniform(2, 4))
        
        assets_liabilities = self.asset_gen.generate_assets_liabilities(
            full_name=person_data['full_name'],
            monthly_income=actual_income,
            family_size=family_size,
            housing_type=housing_type,
            output_path=str(app_dir / "assets_liabilities.xlsx")
        )
        
        total_assets = assets_liabilities['total_assets']
        total_liabilities = assets_liabilities['total_liabilities']
        
        # 6. Credit Report
        credit_report = self.credit_gen.generate_credit_report(
            full_name=person_data['full_name'],
            emirates_id=person_data['emirates_id'],
            monthly_income=actual_income,
            total_liabilities=total_liabilities,
            output_json_path=str(app_dir / "credit_report.json"),
            output_pdf_path=str(app_dir / "credit_report.pdf")
        )
        
        # Build application record
        application = {
            "application_id": app_id,
            "application_type": app_type,
            "test_case_id": test_id,
            "submission_date": datetime.now().isoformat(),
            "documents_path": str(app_dir),
            
            # Personal
            "full_name": person_data['full_name'],
            "emirates_id": person_data['emirates_id'],
            "date_of_birth": person_data['date_of_birth'],
            "age": person_data['age'],
            "email": person_data['email'],
            "phone": person_data['phone'],
            
            # Family
            "marital_status": marital_status,
            "family_size": family_size,
            "dependents": family_size - 1,
            
            # Employment
            "employment_status": employment_status,
            "employer": employer,
            "position": position,
            "years_employed": employment_years,
            
            # Financial
            "monthly_income": round(actual_income, 2),
            "housing_type": housing_type,
            "total_assets": round(total_assets, 0),
            "total_liabilities": round(total_liabilities, 0),
            "net_worth": round(total_assets - total_liabilities, 0),
            "credit_score": credit_report['credit_score'],
            "credit_rating": credit_report['credit_rating'],
            
            # Education
            "education_level": person_data['education_level'],
            
            # Documents
            "has_bank_statement": True,
            "has_emirates_id": True,
            "has_employment_letter": employment_letter is not None,
            "has_resume": True,
            "has_assets_liabilities": True,
            "has_credit_report": True,
            
            # Expected decision (for test cases)
            "expected_decision": special_profile.get('expected_decision') if special_profile else None
        }
        
        return application
    
    def _save_metadata(self) -> None:
        """Save application metadata to CSV and JSON."""
        # CSV format for easy viewing
        csv_path = self.raw_path / "applications_metadata.csv"
        
        if self.applications:
            fieldnames = [
                "application_id", "application_type", "test_case_id",
                "full_name", "emirates_id", "age", "marital_status",
                "family_size", "employment_status", "monthly_income",
                "total_assets", "total_liabilities", "net_worth",
                "credit_score", "expected_decision"
            ]
            
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for app in self.applications:
                    row = {key: app.get(key, "") for key in fieldnames}
                    writer.writerow(row)
        
        # JSON format for complete data
        json_path = self.raw_path / "applications_complete.json"
        with open(json_path, 'w') as f:
            json.dump(self.applications, f, indent=2, default=str)
        
        print(f"  ✓ Metadata saved to {csv_path}")
        print(f"  ✓ Complete data saved to {json_path}")


# Quick test and main execution
if __name__ == "__main__":
    gen = MasterDatasetGenerator(seed=42, base_path="data")
    
    summary = gen.generate_dataset(
        test_cases=10,
        training_size=100,
        bulk_size=500
    )
    
    print(f"\nGeneration Summary:")
    print(f"  Total Applications: {summary['total_applications']}")
    print(f"  Total Documents: {summary['documents_generated']}")
    print(f"  Base Path: {summary['base_path']}")
