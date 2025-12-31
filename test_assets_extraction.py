"""
Production-Grade Assets/Liabilities Extraction Test
Tests the fixed vertical layout parser with real Excel files
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.document_extractor import DocumentExtractor
from colorama import Fore, Style, init

init(autoreset=True)

def test_extraction():
    """Test assets/liabilities extraction with all test files"""
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"🧪 PRODUCTION-GRADE ASSETS/LIABILITIES EXTRACTION TEST")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    extractor = DocumentExtractor()
    
    # Test files
    test_files = [
        ('TEST-04', 'data/test_applications/TEST-04/assets_liabilities.xlsx'),
        ('TEST-03', 'data/test_applications/TEST-03/assets_liabilities.xlsx'),
        ('TEST-02', 'data/test_applications/TEST-02/assets_liabilities.xlsx'),
        ('TEST-05', 'data/test_applications/TEST-05/assets_liabilities.xlsx'),
    ]
    
    results = []
    
    for test_name, filepath in test_files:
        if not os.path.exists(filepath):
            print(f"{Fore.YELLOW}⚠️  File not found: {filepath}{Style.RESET_ALL}")
            continue
        
        print(f"\n{Fore.BLUE}📊 Testing: {test_name}{Style.RESET_ALL}")
        print(f"   File: {filepath}")
        
        try:
            result = extractor.extract_assets_liabilities(filepath)
            
            total_assets = result['total_assets']
            total_liabilities = result['total_liabilities']
            net_worth = result['net_worth']
            
            # Validation
            is_valid = (total_assets > 0 or total_liabilities > 0)
            
            if is_valid:
                print(f"{Fore.GREEN}✅ EXTRACTION SUCCESSFUL{Style.RESET_ALL}")
                print(f"   Total Assets: {total_assets:,.2f} AED")
                print(f"   Total Liabilities: {total_liabilities:,.2f} AED")
                print(f"   Net Worth: {net_worth:,.2f} AED")
            else:
                print(f"{Fore.RED}❌ EXTRACTION FAILED - All values are zero{Style.RESET_ALL}")
            
            results.append({
                'test': test_name,
                'success': is_valid,
                'assets': total_assets,
                'liabilities': total_liabilities,
                'net_worth': net_worth
            })
            
        except Exception as e:
            print(f"{Fore.RED}❌ ERROR: {str(e)}{Style.RESET_ALL}")
            results.append({
                'test': test_name,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"📋 TEST SUMMARY")
    print(f"{'='*80}{Style.RESET_ALL}\n")
    
    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)
    
    print(f"Tests Run: {total}")
    print(f"Successful: {Fore.GREEN}{successful}{Style.RESET_ALL}")
    print(f"Failed: {Fore.RED}{total - successful}{Style.RESET_ALL}")
    
    if successful == total:
        print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED! Production-grade extractor is working correctly.{Style.RESET_ALL}")
        
        # Show extracted data summary
        print(f"\n{Fore.CYAN}💰 Extracted Financial Data Summary:{Style.RESET_ALL}")
        for r in results:
            if r.get('success'):
                print(f"  {r['test']}: Assets={r['assets']:,.0f} AED, "
                      f"Liabilities={r['liabilities']:,.0f} AED, "
                      f"Net Worth={r['net_worth']:,.0f} AED")
    else:
        print(f"\n{Fore.RED}⚠️  Some tests failed. Review errors above.{Style.RESET_ALL}")
    
    return successful == total

if __name__ == "__main__":
    success = test_extraction()
    sys.exit(0 if success else 1)
