#!/usr/bin/env python3
"""
Rigorous Phase 2 Testing - 50 Applications (5 from each of 10 test cases)

This script:
1. Generates 50 test applications (5 instances of each test case)
2. Runs extraction on all 50
3. Generates comprehensive test report with:
   - Per-test-case analysis
   - Document extraction success rates
   - Quality metrics
   - Consistency analysis
   - Error tracking
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import sys
import csv

from src.agents.extraction_agent import ExtractionAgent
from src.models.extraction_models import (
    ExtractionStatus, VerificationStatus, DocumentType, ExtractionBatchResult
)
from data.synthetic_generators.master_dataset_generator import MasterDatasetGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RigorousTestSuite:
    """Comprehensive testing suite for extraction agent."""
    
    def __init__(self):
        self.test_cases = {
            'test_001': {'name': 'Ahmed Al Mazrouei', 'scenario': 'APPROVED - Classic Eligible', 'expected': 'approve'},
            'test_002': {'name': 'Fatima Al Maktoum', 'scenario': 'DECLINED - High Income', 'expected': 'decline'},
            'test_003': {'name': 'Mohammed Al Nuaimi', 'scenario': 'APPROVED - Large Family', 'expected': 'approve'},
            'test_004': {'name': 'Layla Al Falahi', 'scenario': 'CONFLICT - Income Mismatch', 'expected': 'conflict'},
            'test_005': {'name': 'Omar Al Kaabi', 'scenario': 'INCOMPLETE - Missing Docs', 'expected': 'incomplete'},
            'test_006': {'name': 'Sara Al Mansoori', 'scenario': 'ENABLEMENT - Single Parent', 'expected': 'enablement'},
            'test_007': {'name': 'Noor Al Suwaidi', 'scenario': 'ENABLEMENT - Graduate', 'expected': 'enablement'},
            'test_008': {'name': 'Khalid Al Heemi', 'scenario': 'CONDITIONAL - Variable Income', 'expected': 'conditional'},
            'test_009': {'name': 'Amira Al Dhaheri', 'scenario': 'DECLINED - Asset Rich', 'expected': 'decline'},
            'test_010': {'name': 'Youssef Al Bloushi', 'scenario': 'APPROVED - Multi-Income', 'expected': 'approve'},
        }
    
    def generate_test_dataset(self, variations_per_case: int = 5) -> List[Tuple[str, str]]:
        """Generate test applications (5 instances of each test case)."""
        print("\n" + "="*80)
        print("GENERATING RIGOROUS TEST DATASET")
        print("="*80)
        
        # Initialize generator
        generator = MasterDatasetGenerator(seed=42, base_path="data")
        
        # Clear existing test data
        import shutil
        docs_path = Path("data/processed/documents")
        if docs_path.exists():
            shutil.rmtree(docs_path)
        docs_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\nGenerating {len(self.test_cases)} test cases with {variations_per_case} variations each...")
        print(f"Total applications to generate: {len(self.test_cases) * variations_per_case}\n")
        
        applications = []
        app_counter = 1
        
        # Generate each test case 5 times with variations
        for test_id, test_info in self.test_cases.items():
            print(f"[{test_id}] {test_info['name']} - {test_info['scenario']}")
            
            for variation in range(variations_per_case):
                # Create application from test case
                app_id = f"APP-{app_counter:06d}"
                
                app = generator._create_application(
                    name=f"{test_info['name']} (v{variation+1})",
                    monthly_income=5000 + (variation * 500),  # Vary income slightly
                    family_size=3 + variation,  # Vary family size
                    employment_status="Government",
                    marital_status="Married",
                    housing_type="Rent",
                    employment_years=5 + variation,
                    app_type="test",
                    test_id=test_id,
                    person_data=None,
                    employer="ADNOC Group"
                )
                
                generator.applications.append(app)
                applications.append((app_id, str(docs_path / app_id)))
                app_counter += 1
            
            print(f"  ✓ Generated {variations_per_case} variations\n")
        
        # Save metadata
        generator._save_metadata()
        
        print(f"\n✓ Generated {len(applications)} test applications")
        print(f"  Stored in: data/processed/documents/\n")
        
        return applications
    
    def run_extraction_tests(self, applications: List[Tuple[str, str]]) -> Dict:
        """Run extraction on all test applications."""
        print("\n" + "="*80)
        print("RUNNING EXTRACTION TESTS")
        print("="*80)
        
        agent = ExtractionAgent()
        start_time = datetime.now()
        
        print(f"\nProcessing {len(applications)} applications...\n")
        
        result = agent.extract_batch(applications)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            'result': result,
            'duration': duration,
            'start_time': start_time,
            'end_time': end_time
        }
    
    def analyze_by_test_case(self, result) -> Dict:
        """Analyze results grouped by test case."""
        analysis = {}
        
        for app in result.applications:
            test_case_id = app.application_id.split('-')[1]  # Extract number
            test_idx = int(test_case_id) // 10  # Map to 0-9
            test_key = f"test_{test_idx:03d}"
            
            if test_key not in analysis:
                analysis[test_key] = {
                    'count': 0,
                    'successful': 0,
                    'failed': 0,
                    'quality_scores': [],
                    'missing_docs': [],
                    'errors': [],
                    'apps': []
                }
            
            analysis[test_key]['count'] += 1
            analysis[test_key]['quality_scores'].append(app.data_quality_score or 0)
            analysis[test_key]['apps'].append(app)
            
            if app.is_fully_extracted():
                analysis[test_key]['successful'] += 1
            else:
                analysis[test_key]['failed'] += 1
                
            if app.missing_documents:
                analysis[test_key]['missing_docs'].extend(
                    [d.value for d in app.missing_documents]
                )
            
            for metadata in app.extraction_metadata.values():
                if metadata.errors:
                    analysis[test_key]['errors'].extend(metadata.errors)
        
        return analysis
    
    def print_summary_report(self, test_data: Dict) -> None:
        """Print comprehensive summary report."""
        result = test_data['result']
        
        print("\n" + "="*80)
        print("PHASE 2 RIGOROUS TESTING RESULTS")
        print("="*80)
        
        print(f"\n📊 OVERALL STATISTICS")
        print("-"*80)
        print(f"Total Applications Tested: {result.total_applications}")
        print(f"Successful Extractions: {result.successful_extractions} ({result.success_rate():.1%})")
        print(f"Partial Extractions: {result.partial_extractions}")
        print(f"Failed Extractions: {result.failed_extractions}")
        print(f"\nTotal Processing Time: {test_data['duration']:.1f}s")
        print(f"Average Time per App: {test_data['duration']/result.total_applications*1000:.0f}ms")
        print(f"Average Quality Score: {result.average_quality_score:.2f}/1.0")
        
        # Document success rates
        print(f"\n📄 DOCUMENT TYPE SUCCESS RATES")
        print("-"*80)
        for doc_type, rate in result.document_success_rates.items():
            bar_length = int(rate * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            status = "✅" if rate == 1.0 else "⚠️" if rate > 0.8 else "❌"
            print(f"{status} {doc_type.value:20s} {bar} {rate:.1%}")
    
    def print_per_testcase_report(self, analysis: Dict, test_data: Dict) -> None:
        """Print detailed per-test-case report."""
        print("\n" + "="*80)
        print("PER-TEST-CASE ANALYSIS")
        print("="*80)
        
        for test_key in sorted(self.test_cases.keys()):
            if test_key not in analysis:
                continue
            
            data = analysis[test_key]
            test_info = self.test_cases[test_key]
            
            success_rate = data['successful'] / data['count'] if data['count'] > 0 else 0
            avg_quality = sum(data['quality_scores']) / len(data['quality_scores']) if data['quality_scores'] else 0
            
            status_emoji = {
                'approve': '✅',
                'decline': '❌',
                'conflict': '⚠️',
                'incomplete': '❓',
                'enablement': '🚀',
                'conditional': '🔄'
            }.get(test_info['expected'], '❓')
            
            print(f"\n{status_emoji} {test_key}: {test_info['name']}")
            print(f"   Scenario: {test_info['scenario']}")
            print(f"   Expected: {test_info['expected'].upper()}")
            print(f"   ─" * 40)
            print(f"   Instances Tested: {data['count']}")
            print(f"   Success Rate: {success_rate:.1%} ({data['successful']}/{data['count']})")
            print(f"   Avg Quality Score: {avg_quality:.2f}/1.0")
            
            if data['missing_docs']:
                from collections import Counter
                doc_count = Counter(data['missing_docs'])
                print(f"   Missing Docs: {dict(doc_count)}")
            
            if data['errors']:
                from collections import Counter
                error_count = Counter(data['errors'])
                print(f"   Top Errors:")
                for error, count in error_count.most_common(2):
                    print(f"     • {error} ({count}x)")
    
    def print_quality_distribution(self, result) -> None:
        """Print quality score distribution."""
        print("\n" + "="*80)
        print("QUALITY SCORE DISTRIBUTION")
        print("="*80)
        
        ranges = {
            'Excellent (0.9-1.0)': [],
            'Good (0.7-0.9)': [],
            'Fair (0.5-0.7)': [],
            'Poor (< 0.5)': []
        }
        
        for app in result.applications:
            score = app.data_quality_score or 0
            if score >= 0.9:
                ranges['Excellent (0.9-1.0)'].append(app)
            elif score >= 0.7:
                ranges['Good (0.7-0.9)'].append(app)
            elif score >= 0.5:
                ranges['Fair (0.5-0.7)'].append(app)
            else:
                ranges['Poor (< 0.5)'].append(app)
        
        total = len(result.applications)
        for range_name, apps in ranges.items():
            count = len(apps)
            pct = count / total * 100 if total > 0 else 0
            bar_length = int(pct / 100 * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            print(f"{range_name:25s} {bar} {count:3d} ({pct:5.1f}%)")
    
    def print_error_analysis(self, result) -> None:
        """Print detailed error analysis."""
        print("\n" + "="*80)
        print("ERROR ANALYSIS")
        print("="*80)
        
        all_errors = []
        apps_with_errors = []
        
        for app in result.applications:
            app_errors = []
            for doc_type, metadata in app.extraction_metadata.items():
                if metadata.errors:
                    for error in metadata.errors:
                        all_errors.append(error)
                        app_errors.append((doc_type.value, error))
            
            if app_errors:
                apps_with_errors.append((app.application_id, app_errors))
        
        if all_errors:
            from collections import Counter
            error_count = Counter(all_errors)
            
            print(f"\nMost Common Errors (Top 10):")
            for error, count in error_count.most_common(10):
                pct = count / len(result.applications) * 100
                print(f"  • {error} ({count}x, {pct:.1f}%)")
        else:
            print("\n✅ No extraction errors found!")
        
        if apps_with_errors:
            print(f"\nApplications with Errors ({len(apps_with_errors)}):")
            for app_id, errors in apps_with_errors[:5]:
                print(f"  • {app_id}:")
                for doc, error in errors[:2]:
                    print(f"    - {doc}: {error}")
    
    def save_detailed_results(self, result, analysis, test_data) -> None:
        """Save comprehensive results to JSON."""
        output_file = "rigorous_test_results.json"
        
        data = {
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_applications": result.total_applications,
                "total_duration_seconds": test_data['duration'],
                "start_time": test_data['start_time'].isoformat(),
                "end_time": test_data['end_time'].isoformat(),
            },
            "summary": {
                "successful_extractions": result.successful_extractions,
                "partial_extractions": result.partial_extractions,
                "failed_extractions": result.failed_extractions,
                "success_rate": result.success_rate(),
                "average_quality_score": result.average_quality_score,
            },
            "document_success_rates": {
                doc_type.value: rate 
                for doc_type, rate in result.document_success_rates.items()
            },
            "per_test_case": {},
            "applications": []
        }
        
        # Add per-test-case analysis
        for test_key, test_data_item in analysis.items():
            data["per_test_case"][test_key] = {
                "count": test_data_item['count'],
                "successful": test_data_item['successful'],
                "failed": test_data_item['failed'],
                "success_rate": test_data_item['successful'] / test_data_item['count'] if test_data_item['count'] > 0 else 0,
                "average_quality_score": sum(test_data_item['quality_scores']) / len(test_data_item['quality_scores']) if test_data_item['quality_scores'] else 0,
                "errors": list(set(test_data_item['errors']))[:5]
            }
        
        # Add detailed application results
        for app in result.applications:
            app_data = {
                "application_id": app.application_id,
                "verification_status": app.verification_status.value,
                "data_quality_score": app.data_quality_score,
                "documents_extracted": list(app.extraction_metadata.keys()),
                "missing_documents": [d.value for d in app.missing_documents],
                "extraction_metadata": {
                    doc.value: {
                        "status": app.get_extraction_status(doc).value if app.get_extraction_status(doc) else None,
                        "confidence": app.extraction_metadata.get(doc, {}).confidence if doc in app.extraction_metadata else None
                    }
                    for doc in DocumentType
                }
            }
            
            # Add extracted data summaries
            if app.personal_info.full_name:
                app_data["personal_info"] = {
                    "full_name": app.personal_info.full_name,
                    "emirates_id": app.personal_info.emirates_id,
                    "date_of_birth": str(app.personal_info.date_of_birth) if app.personal_info.date_of_birth else None
                }
            
            if app.employment_info.current_employer:
                app_data["employment_info"] = {
                    "employer": app.employment_info.current_employer,
                    "position": app.employment_info.job_title,
                    "salary": app.employment_info.monthly_salary
                }
            
            if app.bank_statement:
                app_data["bank_statement"] = {
                    "monthly_income": app.bank_statement.extract_monthly_income(),
                    "closing_balance": app.bank_statement.closing_balance,
                    "transactions_count": len(app.bank_statement.transactions)
                }
            
            data["applications"].append(app_data)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Detailed results saved to {output_file}")


def main():
    """Run rigorous testing suite."""
    print("\n" + "="*80)
    print("PHASE 2: RIGOROUS EXTRACTION TESTING")
    print("="*80)
    print("\nTest Configuration:")
    print("  - 10 test case scenarios")
    print("  - 5 variations per test case")
    print("  - Total: 50 applications")
    print("\nTest Cases:")
    
    suite = RigorousTestSuite()
    
    for test_key, info in suite.test_cases.items():
        print(f"  [{test_key}] {info['name']} - {info['scenario']}")
    
    # Generate test dataset
    applications = suite.generate_test_dataset(variations_per_case=5)
    
    # Run extraction tests
    test_data = suite.run_extraction_tests(applications)
    result = test_data['result']
    
    # Analyze results
    analysis = suite.analyze_by_test_case(result)
    
    # Print reports
    suite.print_summary_report(test_data)
    suite.print_per_testcase_report(analysis, test_data)
    suite.print_quality_distribution(result)
    suite.print_error_analysis(result)
    
    # Save results
    suite.save_detailed_results(result, analysis, test_data)
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
    print(f"\n✅ Tested {result.total_applications} applications")
    print(f"✅ Success Rate: {result.success_rate():.1%}")
    print(f"✅ Results saved to: rigorous_test_results.json\n")
    
    return 0 if result.success_rate() > 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
