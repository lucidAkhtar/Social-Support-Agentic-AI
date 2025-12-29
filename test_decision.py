"""
Test Decision Agent - Phase 5
Tests the DecisionAgent on all 50 validated applications.
Generates comprehensive decision statistics and reports.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from src.agents.decision_agent import DecisionAgent, DecisionResult, serialize_decision


class DecisionTestSuite:
    """Comprehensive testing suite for DecisionAgent"""
    
    def __init__(self, validation_results_path: str):
        self.validation_results_path = validation_results_path
        self.agent = DecisionAgent(validation_results_path)
        self.decisions = []
        
    def run_decision_tests(self, num_apps: int = None) -> List[DecisionResult]:
        """Run decision process on all validated applications"""
        print("\n" + "="*80)
        print("PHASE 5: DECISION AGENT TEST SUITE")
        print("="*80)
        
        # Load validation results to get app IDs
        with open(self.validation_results_path, 'r') as f:
            validation_data = json.load(f)
        
        app_ids = [app['application_id'] for app in validation_data.get('applications', [])]
        if num_apps:
            app_ids = app_ids[:num_apps]
        
        print(f"\nProcessing {len(app_ids)} applications...")
        
        start_time = time.time()
        self.decisions = self.agent.decide_batch(app_ids)
        duration = time.time() - start_time
        
        print(f"✓ Decisions completed in {duration:.2f}s ({duration/len(self.decisions):.0f}ms per app)")
        
        return self.decisions
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not self.decisions:
            return {}
        
        summary = self.agent.generate_summary_report(self.decisions)
        
        return summary
    
    def generate_decision_breakdown(self) -> Dict[str, Any]:
        """Detailed breakdown by decision type"""
        breakdown = {
            'by_decision': defaultdict(list),
            'by_confidence': defaultdict(list),
            'by_appeals_eligibility': defaultdict(list),
        }
        
        for decision in self.decisions:
            breakdown['by_decision'][decision.final_decision.value].append(decision.application_id)
            breakdown['by_confidence'][decision.confidence_level].append(decision.application_id)
            
            eligibility = 'eligible' if decision.appeals_eligible else 'ineligible'
            breakdown['by_appeals_eligibility'][eligibility].append(decision.application_id)
        
        return {
            'decisions': {k: len(v) for k, v in breakdown['by_decision'].items()},
            'confidence_levels': {k: len(v) for k, v in breakdown['by_confidence'].items()},
            'appeals_eligibility': {k: len(v) for k, v in breakdown['by_appeals_eligibility'].items()},
        }
    
    def generate_decision_analysis(self) -> Dict[str, Any]:
        """Analyze decision patterns and score distributions"""
        if not self.decisions:
            return {}
        
        import numpy as np
        
        validation_scores = [d.decision_scores.validation_score for d in self.decisions]
        ml_confidences = [d.decision_scores.ml_confidence for d in self.decisions]
        combined_scores = [d.decision_scores.combined_score for d in self.decisions]
        rule_scores = [d.decision_scores.business_rule_score for d in self.decisions]
        
        return {
            'validation_score': {
                'mean': round(np.mean(validation_scores), 4),
                'std': round(np.std(validation_scores), 4),
                'min': round(np.min(validation_scores), 4),
                'max': round(np.max(validation_scores), 4),
            },
            'ml_confidence': {
                'mean': round(np.mean(ml_confidences), 4),
                'std': round(np.std(ml_confidences), 4),
                'min': round(np.min(ml_confidences), 4),
                'max': round(np.max(ml_confidences), 4),
            },
            'combined_score': {
                'mean': round(np.mean(combined_scores), 4),
                'std': round(np.std(combined_scores), 4),
                'min': round(np.min(combined_scores), 4),
                'max': round(np.max(combined_scores), 4),
            },
            'business_rule_score': {
                'mean': round(np.mean(rule_scores), 4),
                'std': round(np.std(rule_scores), 4),
                'min': round(np.min(rule_scores), 4),
                'max': round(np.max(rule_scores), 4),
            },
        }
    
    def generate_critical_flags_report(self) -> Dict[str, Any]:
        """Report on critical flags and reasons for denial/review"""
        flags_count = defaultdict(int)
        reasons_by_decision = {
            'APPROVE': [],
            'DENY': [],
            'NEEDS_REVIEW': [],
        }
        
        for decision in self.decisions:
            decision_type = decision.final_decision.value
            
            # Collect flags
            for flag in decision.critical_flags:
                flags_count[flag] += 1
            
            # Collect reasons (first finding)
            if decision.findings:
                reasons_by_decision[decision_type].append({
                    'app_id': decision.application_id,
                    'primary_reason': decision.findings[0].message,
                    'severity': decision.findings[0].severity,
                })
        
        return {
            'critical_flags': dict(flags_count),
            'reasons_by_decision_type': reasons_by_decision,
        }
    
    def print_summary_report(self):
        """Print formatted summary report"""
        summary = self.generate_summary_report()
        
        print("\n" + "-"*80)
        print("DECISION SUMMARY")
        print("-"*80)
        
        print(f"\nTotal Applications Processed: {summary['total_applications']}")
        print(f"\nDecision Breakdown:")
        print(f"  ✓ APPROVE:       {summary['decisions']['approve']:3d} ({summary['decisions']['approve_pct']:5.1f}%)")
        print(f"  ✗ DENY:          {summary['decisions']['deny']:3d} ({summary['decisions']['deny_pct']:5.1f}%)")
        print(f"  ? NEEDS_REVIEW:  {summary['decisions']['needs_review']:3d} ({summary['decisions']['needs_review_pct']:5.1f}%)")
        
        print(f"\nConfidence Distribution:")
        conf = summary['confidence_distribution']
        print(f"  HIGH:   {conf['high']:2d}")
        print(f"  MEDIUM: {conf['medium']:2d}")
        print(f"  LOW:    {conf['low']:2d}")
        
        print(f"\nAverage Scores:")
        scores = summary['average_scores']
        print(f"  Validation Score: {scores['validation_score']:.4f}")
        print(f"  ML Confidence:    {scores['ml_confidence']:.4f}")
        print(f"  Combined Score:   {scores['combined_score']:.4f}")
        
        print(f"\nAppeals Eligible: {summary['appeals_eligible']} applications")
    
    def print_decision_breakdown(self):
        """Print decision breakdown"""
        breakdown = self.generate_decision_breakdown()
        
        print("\n" + "-"*80)
        print("DECISION BREAKDOWN")
        print("-"*80)
        
        print("\nDecisions by Type:")
        for decision_type, count in breakdown['decisions'].items():
            print(f"  {decision_type:15s}: {count:3d}")
        
        print("\nConfidence Levels:")
        for conf_level, count in breakdown['confidence_levels'].items():
            print(f"  {conf_level:15s}: {count:3d}")
    
    def print_analysis_report(self):
        """Print detailed analysis"""
        analysis = self.generate_decision_analysis()
        
        print("\n" + "-"*80)
        print("SCORE ANALYSIS")
        print("-"*80)
        
        for score_name, stats in analysis.items():
            print(f"\n{score_name.replace('_', ' ').title()}:")
            print(f"  Mean:  {stats['mean']:.4f}")
            print(f"  StdDev: {stats['std']:.4f}")
            print(f"  Range: {stats['min']:.4f} - {stats['max']:.4f}")
    
    def print_critical_flags_report(self):
        """Print critical findings"""
        report = self.generate_critical_flags_report()
        
        print("\n" + "-"*80)
        print("CRITICAL FLAGS & FINDINGS")
        print("-"*80)
        
        if report['critical_flags']:
            print("\nCritical Flags:")
            for flag, count in report['critical_flags'].items():
                print(f"  {flag}: {count}")
        else:
            print("\nNo critical flags detected")
        
        print("\nTop Reasons by Decision Type:")
        for decision_type, reasons in report['reasons_by_decision_type'].items():
            if reasons:
                print(f"\n{decision_type}:")
                for i, reason in enumerate(reasons[:3], 1):
                    print(f"  {i}. {reason['app_id']}: {reason['primary_reason']}")
    
    def export_decisions_json(self, output_path: str = None):
        """Export all decisions to JSON"""
        if output_path is None:
            output_path = str(Path(self.validation_results_path).parent / 'decision_results.json')
        
        output_data = {
            'timestamp': self.decisions[0].timestamp if self.decisions else '',
            'total_decisions': len(self.decisions),
            'summary': self.generate_summary_report(),
            'breakdown': self.generate_decision_breakdown(),
            'analysis': self.generate_decision_analysis(),
            'critical_flags': self.generate_critical_flags_report(),
            'decisions': [serialize_decision(d) for d in self.decisions],
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n✓ Decisions exported to {output_path}")
        return output_path
    
    def print_approval_samples(self, num_samples: int = 3):
        """Print sample approvals"""
        approvals = [d for d in self.decisions if d.final_decision.value == 'APPROVE']
        
        if not approvals:
            return
        
        print("\n" + "-"*80)
        print(f"SAMPLE APPROVALS (showing {min(num_samples, len(approvals))})")
        print("-"*80)
        
        for decision in approvals[:num_samples]:
            print(f"\n📋 {decision.application_id}")
            print(f"   Decision: {decision.final_decision.value} ({decision.confidence_level})")
            print(f"   Scores: Validation={decision.decision_scores.validation_score:.2f}, "
                  f"ML={decision.decision_scores.ml_confidence:.2f}, "
                  f"Combined={decision.decision_scores.combined_score:.2f}")
            print(f"   Rationale: {decision.rationale}")
    
    def print_denial_samples(self, num_samples: int = 3):
        """Print sample denials"""
        denials = [d for d in self.decisions if d.final_decision.value == 'DENY']
        
        if not denials:
            return
        
        print("\n" + "-"*80)
        print(f"SAMPLE DENIALS (showing {min(num_samples, len(denials))})")
        print("-"*80)
        
        for decision in denials[:num_samples]:
            print(f"\n📋 {decision.application_id}")
            print(f"   Decision: {decision.final_decision.value} ({decision.confidence_level})")
            print(f"   Critical Flags: {', '.join(decision.critical_flags) if decision.critical_flags else 'None'}")
            print(f"   Primary Finding: {decision.findings[0].message if decision.findings else 'None'}")
    
    def print_review_samples(self, num_samples: int = 3):
        """Print sample needs-review"""
        reviews = [d for d in self.decisions if d.final_decision.value == 'NEEDS_REVIEW']
        
        if not reviews:
            return
        
        print("\n" + "-"*80)
        print(f"SAMPLE NEEDS_REVIEW (showing {min(num_samples, len(reviews))})")
        print("-"*80)
        
        for decision in reviews[:num_samples]:
            print(f"\n📋 {decision.application_id}")
            print(f"   Decision: {decision.final_decision.value} ({decision.confidence_level})")
            print(f"   Combined Score: {decision.decision_scores.combined_score:.2f}")
            if decision.recommended_actions:
                print(f"   Recommended Actions:")
                for action in decision.recommended_actions:
                    print(f"     - {action}")


def main():
    """Run Phase 5 Decision Agent tests"""
    validation_path = 'validation_test_results.json'
    
    # Create test suite
    suite = DecisionTestSuite(validation_path)
    
    # Run decision tests
    suite.run_decision_tests()
    
    # Generate and print reports
    suite.print_summary_report()
    suite.print_decision_breakdown()
    suite.print_analysis_report()
    suite.print_critical_flags_report()
    
    # Print sample decisions
    suite.print_approval_samples(3)
    suite.print_denial_samples(3)
    suite.print_review_samples(3)
    
    # Export results
    suite.export_decisions_json()
    
    print("\n" + "="*80)
    print("PHASE 5 DECISION TESTING COMPLETE ✓")
    print("="*80)


if __name__ == '__main__':
    main()
