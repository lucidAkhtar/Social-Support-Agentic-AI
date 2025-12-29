"""
Test the extraction agent on the synthetic dataset.

This script runs the extraction agent on all 260 generated applications and
produces a detailed report of extraction success rates, quality scores, and issues.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import sys

from src.agents.extraction_agent import ExtractionAgent
from src.models.extraction_models import (
    ExtractionStatus, VerificationStatus, DocumentType, ExtractionBatchResult
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_applications_list(data_folder: str = "data") -> List[tuple]:
    """Load list of all generated applications."""
    processed_path = Path(data_folder) / "processed" / "documents"
    
    if not processed_path.exists():
        logger.error(f"Data folder not found: {processed_path}")
        return []
    
    applications = []
    for app_folder in sorted(processed_path.glob("APP-*")):
        if app_folder.is_dir():
            app_id = app_folder.name
            applications.append((app_id, str(app_folder)))
    
    logger.info(f"Found {len(applications)} applications to extract")
    return applications


def run_extraction(applications: List[tuple], max_apps: int = None) -> ExtractionBatchResult:
    """Run extraction on applications."""
    logger.info("=" * 80)
    logger.info("STARTING EXTRACTION AGENT")
    logger.info("=" * 80)
    
    # Limit applications if requested
    if max_apps:
        applications = applications[:max_apps]
    
    # Initialize extraction agent
    agent = ExtractionAgent()
    
    logger.info(f"Processing {len(applications)} applications...")
    
    # Run batch extraction
    result = agent.extract_batch(applications)
    
    return result


def print_extraction_summary(result: ExtractionBatchResult) -> None:
    """Print extraction summary statistics."""
    print("\n" + "=" * 80)
    print("EXTRACTION RESULTS SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal Applications: {result.total_applications}")
    print(f"Successful Extractions: {result.successful_extractions}")
    print(f"Partial Extractions: {result.partial_extractions}")
    print(f"Failed Extractions: {result.failed_extractions}")
    print(f"Success Rate: {result.success_rate():.1%}")
    
    print(f"\nExtraction Time: {result.extraction_time_ms:.0f}ms ({result.extraction_time_ms/1000:.1f}s)")
    print(f"Average Quality Score: {result.average_quality_score:.2f}/1.0")
    
    # Document success rates
    print("\nDocument Type Success Rates:")
    print("-" * 80)
    for doc_type, rate in result.document_success_rates.items():
        bar_length = int(rate * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"{doc_type.value:20s} {bar} {rate:.1%}")


def print_test_case_results(result: ExtractionBatchResult) -> None:
    """Print results for test cases."""
    print("\n" + "=" * 80)
    print("TEST CASE EXTRACTION RESULTS")
    print("=" * 80)
    
    test_cases = [
        ("APP-000001", "Ahmed Al Mazrouei - APPROVED"),
        ("APP-000002", "Fatima Al Maktoum - DECLINED"),
        ("APP-000003", "Mohammed Al Nuaimi - APPROVED"),
        ("APP-000004", "Layla Al Falahi - CONFLICT"),
        ("APP-000005", "Omar Al Kaabi - INCOMPLETE"),
    ]
    
    for app_id, description in test_cases:
        app = next((a for a in result.applications if a.application_id == app_id), None)
        
        if app:
            status_emoji = {
                VerificationStatus.VERIFIED: "✅",
                VerificationStatus.INCOMPLETE: "❌",
                VerificationStatus.CONFLICTED: "⚠️",
            }.get(app.verification_status, "❓")
            
            print(f"\n{status_emoji} {app_id}: {description}")
            print(f"   Status: {app.verification_status.value}")
            print(f"   Quality Score: {app.data_quality_score:.2f}")
            print(f"   Documents Extracted: {len(app.extraction_metadata)}/6")
            
            if app.missing_documents:
                print(f"   Missing Documents: {', '.join(d.value for d in app.missing_documents)}")
            
            if app.consistency_issues:
                print(f"   Issues: {', '.join(app.consistency_issues[:2])}")
            
            # Show extracted data
            if app.personal_info.full_name:
                print(f"   Name: {app.personal_info.full_name}")
            if app.employment_info.current_employer:
                print(f"   Employer: {app.employment_info.current_employer}")
            if app.employment_info.monthly_salary:
                print(f"   Salary: AED {app.employment_info.monthly_salary:,.0f}")


def print_quality_analysis(result: ExtractionBatchResult) -> None:
    """Print quality analysis."""
    print("\n" + "=" * 80)
    print("EXTRACTION QUALITY ANALYSIS")
    print("=" * 80)
    
    # Group by quality score ranges
    quality_ranges = {
        "Excellent (0.9-1.0)": [],
        "Good (0.7-0.9)": [],
        "Fair (0.5-0.7)": [],
        "Poor (< 0.5)": [],
    }
    
    for app in result.applications:
        if app.data_quality_score >= 0.9:
            quality_ranges["Excellent (0.9-1.0)"].append(app)
        elif app.data_quality_score >= 0.7:
            quality_ranges["Good (0.7-0.9)"].append(app)
        elif app.data_quality_score >= 0.5:
            quality_ranges["Fair (0.5-0.7)"].append(app)
        else:
            quality_ranges["Poor (< 0.5)"].append(app)
    
    print("\nQuality Score Distribution:")
    for range_name, apps in quality_ranges.items():
        pct = len(apps) / len(result.applications) * 100 if result.applications else 0
        print(f"{range_name}: {len(apps)} ({pct:.1f}%)")


def print_document_issues(result: ExtractionBatchResult) -> None:
    """Print detailed document extraction issues."""
    print("\n" + "=" * 80)
    print("DOCUMENT EXTRACTION ISSUES")
    print("=" * 80)
    
    # Find applications with missing documents
    missing_docs = [a for a in result.applications if a.missing_documents]
    
    if missing_docs:
        print(f"\nApplications with Missing Documents ({len(missing_docs)}):")
        for app in missing_docs[:5]:  # Show first 5
            print(f"  {app.application_id}: Missing {[d.value for d in app.missing_documents]}")
    
    # Find applications with extraction errors
    with_errors = [a for a in result.applications 
                   if any(m.errors for m in a.extraction_metadata.values())]
    
    if with_errors:
        print(f"\nApplications with Extraction Errors ({len(with_errors)}):")
        for app in with_errors[:5]:  # Show first 5
            for doc_type, metadata in app.extraction_metadata.items():
                if metadata.errors:
                    print(f"  {app.application_id} - {doc_type.value}: {metadata.errors[0]}")


def save_extraction_results(result: ExtractionBatchResult, output_file: str = "extraction_results.json") -> None:
    """Save extraction results to JSON."""
    logger.info(f"Saving extraction results to {output_file}")
    
    # Convert to serializable format
    data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_applications": result.total_applications,
            "successful_extractions": result.successful_extractions,
            "partial_extractions": result.partial_extractions,
            "failed_extractions": result.failed_extractions,
            "success_rate": result.success_rate(),
            "extraction_time_ms": result.extraction_time_ms,
            "average_quality_score": result.average_quality_score,
        },
        "document_success_rates": {
            doc_type.value: rate for doc_type, rate in result.document_success_rates.items()
        },
        "applications": []
    }
    
    # Add per-application results
    for app in result.applications:
        app_data = {
            "application_id": app.application_id,
            "verification_status": app.verification_status.value,
            "data_quality_score": app.data_quality_score,
            "extracted_documents": list(app.extraction_metadata.keys()),
            "missing_documents": [d.value for d in app.missing_documents],
            "personal_info": {
                "full_name": app.personal_info.full_name,
                "emirates_id": app.personal_info.emirates_id,
                "date_of_birth": app.personal_info.date_of_birth.isoformat() if app.personal_info.date_of_birth else None,
            },
            "employment_info": {
                "employer": app.employment_info.current_employer,
                "job_title": app.employment_info.job_title,
                "monthly_salary": app.employment_info.monthly_salary,
            }
        }
        
        # Add extracted amounts if available
        if app.bank_statement:
            monthly_income = app.bank_statement.extract_monthly_income()
            app_data["bank_statement"] = {
                "monthly_income": monthly_income,
                "closing_balance": app.bank_statement.closing_balance,
                "transactions_count": len(app.bank_statement.transactions),
            }
        
        if app.assets_liabilities:
            app_data["financial_position"] = {
                "total_assets": app.assets_liabilities.total_assets,
                "total_liabilities": app.assets_liabilities.total_liabilities,
                "net_worth": app.assets_liabilities.calculate_net_worth(),
            }
        
        if app.credit_report:
            app_data["credit_report"] = {
                "credit_score": app.credit_report.credit_score,
                "score_rating": app.credit_report.score_rating,
            }
        
        data["applications"].append(app_data)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved results to {output_file}")


def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("EXTRACTION AGENT TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check if running test mode (first 10 apps) or full mode
    test_mode = len(sys.argv) > 1 and sys.argv[1] == "test"
    max_apps = 10 if test_mode else None
    
    # Load applications
    applications = load_applications_list()
    
    if not applications:
        logger.error("No applications found. Please run data generation first.")
        return 1
    
    # Run extraction
    result = run_extraction(applications, max_apps=max_apps)
    
    # Print results
    print_extraction_summary(result)
    print_test_case_results(result)
    print_quality_analysis(result)
    print_document_issues(result)
    
    # Save results
    output_file = "extraction_results_test.json" if test_mode else "extraction_results.json"
    save_extraction_results(result, output_file)
    
    print("\n" + "=" * 80)
    print(f"Extraction completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    return 0 if result.success_rate() > 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
