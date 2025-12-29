"""
Test suite for Validation Agent - Phase 3.

Validates 50 applications and produces comprehensive validation report.
Tests cross-document consistency, conflict detection, and quality scoring.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from src.agents.extraction_agent import ExtractionAgent
from src.agents.validation_agent import ValidationAgent, ValidationStatus
from src.models.extraction_models import ApplicationExtraction

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationTestSuite:
    """Comprehensive validation test suite."""
    
    def __init__(self):
        self.extraction_agent = ExtractionAgent()
        self.validation_agent = ValidationAgent()
        self.data_dir = Path("data/processed/documents")
    
    def load_extracted_applications(self, limit: int = None) -> List[tuple]:
        """Load extracted application data."""
        applications = []
        app_dirs = sorted(self.data_dir.glob("APP-*"))
        
        if limit:
            app_dirs = app_dirs[:limit]
        
        for app_dir in app_dirs:
            applications.append((app_dir.name, str(app_dir)))
        
        return applications
    
    def run_validation_tests(self) -> Dict:
        """Run validation on all applications."""
        logger.info("=" * 80)
        logger.info("PHASE 3: VALIDATION AGENT TESTING")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        # Load applications
        applications = self.load_extracted_applications()
        logger.info(f"\nLoading {len(applications)} extracted applications...")
        
        # Run extractions (should already be cached from Phase 2)
        validation_results = []
        
        for app_id, app_path in applications:
            try:
                # Extract (if not already done)
                extraction = self.extraction_agent.extract_application(app_id, app_path)
                
                if not extraction:
                    logger.warning(f"Failed to extract {app_id}")
                    continue
                
                # Validate
                validation_result = self.validation_agent.validate_application(extraction)
                validation_results.append(validation_result)
                
            except Exception as e:
                logger.error(f"Error processing {app_id}: {e}")
                continue
        
        # Analyze results
        analysis = self._analyze_validation_results(validation_results)
        analysis['total_duration_seconds'] = (datetime.now() - start_time).total_seconds()
        
        # Print reports
        self._print_summary_report(analysis)
        self._print_validation_status_breakdown(validation_results)
        self._print_top_issues(validation_results)
        self._print_per_category_analysis(validation_results)
        
        # Save detailed results
        self._save_detailed_results(validation_results, analysis)
        
        return analysis
    
    @staticmethod
    def _analyze_validation_results(results) -> Dict:
        """Analyze validation results."""
        analysis = {
            'total_tested': len(results),
            'passed': sum(1 for r in results if r.validation_status == ValidationStatus.PASSED),
            'passed_with_warnings': sum(1 for r in results 
                                       if r.validation_status == ValidationStatus.PASSED_WITH_WARNINGS),
            'needs_review': sum(1 for r in results if r.validation_status == ValidationStatus.NEEDS_REVIEW),
            'failed': sum(1 for r in results if r.validation_status == ValidationStatus.FAILED),
            'avg_quality_score': sum(r.quality_score for r in results) / len(results) if results else 0,
            'avg_consistency_score': sum(r.consistency_score for r in results) / len(results) if results else 0,
            'avg_completeness_score': sum(r.completeness_score for r in results) / len(results) if results else 0,
            'total_findings': sum(len(r.findings) for r in results),
            'total_critical': sum(len(r.critical_issues()) for r in results),
            'total_high': sum(len(r.high_issues()) for r in results),
        }
        return analysis
    
    def _print_summary_report(self, analysis: Dict):
        """Print validation summary report."""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION SUMMARY REPORT")
        logger.info("=" * 80)
        logger.info(f"\nTotal Applications Validated: {analysis['total_tested']}")
        
        if analysis['total_tested'] == 0:
            logger.warning("No applications were validated. Check extraction results.")
            return
        
        logger.info(f"\nValidation Status Breakdown:")
        logger.info(f"  ✅ Passed:                   {analysis['passed']} ({analysis['passed']/analysis['total_tested']*100:.1f}%)")
        logger.info(f"  ⚠️  Passed with Warnings:    {analysis['passed_with_warnings']} ({analysis['passed_with_warnings']/analysis['total_tested']*100:.1f}%)")
        logger.info(f"  🔍 Needs Review:            {analysis['needs_review']} ({analysis['needs_review']/analysis['total_tested']*100:.1f}%)")
        logger.info(f"  ❌ Failed:                   {analysis['failed']} ({analysis['failed']/analysis['total_tested']*100:.1f}%)")
        
        logger.info(f"\nQuality Metrics:")
        logger.info(f"  Average Quality Score:      {analysis['avg_quality_score']:.2f}/1.0")
        logger.info(f"  Average Consistency Score:  {analysis['avg_consistency_score']:.2f}/1.0")
        logger.info(f"  Average Completeness Score: {analysis['avg_completeness_score']:.2f}/1.0")
        
        logger.info(f"\nFinding Counts:")
        logger.info(f"  Total Findings:             {analysis['total_findings']}")
        logger.info(f"  Critical Issues:            {analysis['total_critical']}")
        logger.info(f"  High Severity Issues:       {analysis['total_high']}")
        
        logger.info(f"\nProcessing Time:            {analysis['total_duration_seconds']:.1f} seconds")
        logger.info(f"Average per Application:    {analysis['total_duration_seconds']/analysis['total_tested']*1000:.0f}ms")
    
    @staticmethod
    def _print_validation_status_breakdown(results):
        """Print validation status breakdown."""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION STATUS BREAKDOWN")
        logger.info("=" * 80)
        
        for status in [ValidationStatus.PASSED, ValidationStatus.PASSED_WITH_WARNINGS,
                      ValidationStatus.NEEDS_REVIEW, ValidationStatus.FAILED]:
            matching = [r for r in results if r.validation_status == status]
            if matching:
                logger.info(f"\n{status.value.upper()}:")
                for result in matching[:5]:  # Show first 5
                    logger.info(f"  • {result.application_id}: Quality {result.quality_score:.2f}, "
                              f"Issues {len(result.findings)}")
                if len(matching) > 5:
                    logger.info(f"  ... and {len(matching) - 5} more")
    
    @staticmethod
    def _print_top_issues(results):
        """Print top issues across all applications."""
        logger.info("\n" + "=" * 80)
        logger.info("TOP VALIDATION ISSUES")
        logger.info("=" * 80)
        
        # Collect all findings
        all_findings = []
        for result in results:
            for finding in result.findings:
                all_findings.append((finding.category, finding.finding_type, finding.severity))
        
        # Count occurrences
        from collections import Counter
        issue_counts = Counter(all_findings)
        
        logger.info("\nMost Common Issues:")
        for (category, ftype, severity), count in issue_counts.most_common(10):
            logger.info(f"  • {category}/{ftype} ({severity.value}): {count} occurrences")
    
    @staticmethod
    def _print_per_category_analysis(results):
        """Print analysis by validation category."""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION BY CATEGORY")
        logger.info("=" * 80)
        
        categories = set()
        for result in results:
            for finding in result.findings:
                categories.add(finding.category)
        
        for category in sorted(categories):
            findings_in_cat = []
            for result in results:
                for finding in result.findings:
                    if finding.category == category:
                        findings_in_cat.append(finding)
            
            if findings_in_cat:
                logger.info(f"\n{category.upper()}:")
                logger.info(f"  Total Issues: {len(findings_in_cat)}")
                
                # Count by severity
                from collections import Counter
                severity_counts = Counter(f.severity for f in findings_in_cat)
                for severity in ['critical', 'high', 'medium', 'low', 'info']:
                    count = severity_counts.get(severity, 0)
                    if count > 0:
                        logger.info(f"    {severity.title()}: {count}")
    
    @staticmethod
    def _save_detailed_results(results, analysis):
        """Save detailed validation results to JSON."""
        output = {
            'timestamp': datetime.now().isoformat(),
            'summary': analysis,
            'applications': []
        }
        
        for result in results:
            app_data = {
                'application_id': result.application_id,
                'validation_status': result.validation_status.value,
                'quality_score': result.quality_score,
                'consistency_score': result.consistency_score,
                'completeness_score': result.completeness_score,
                'scores_by_category': {
                    'personal_info': result.personal_info_score,
                    'employment': result.employment_score,
                    'income': result.income_score,
                    'assets': result.assets_score,
                    'credit': result.credit_score,
                },
                'documents_validated': result.documents_validated,
                'findings_count': len(result.findings),
                'findings': [
                    {
                        'category': f.category,
                        'type': f.finding_type,
                        'severity': f.severity.value,
                        'message': f.message,
                        'auto_resolvable': f.auto_resolvable,
                    }
                    for f in result.findings
                ],
                'validation_duration_ms': result.validation_duration_ms,
            }
            output['applications'].append(app_data)
        
        output_path = Path("validation_test_results.json")
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"\n✅ Detailed results saved to: {output_path}")


def main():
    """Run validation test suite."""
    suite = ValidationTestSuite()
    analysis = suite.run_validation_tests()
    
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION TESTING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Status: ✅ COMPLETE")
    logger.info(f"Results saved to: validation_test_results.json")


if __name__ == "__main__":
    main()
