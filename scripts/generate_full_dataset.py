#!/usr/bin/env python3
"""
Full Dataset Generation - Optimized for M1 8GB RAM
10 test cases + 50 training + 200 bulk (total 260 apps)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.synthetic_generators import MasterDatasetGenerator


def main():
    """Generate optimized full dataset."""
    
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  FULL DATASET GENERATION - M1 OPTIMIZED                            ║
    ║  10 test cases + 50 training + 200 bulk (260 total)                ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize master generator
    generator = MasterDatasetGenerator(seed=42, base_path="data")
    
    # Generate optimized dataset
    print("\nGenerating dataset...\n")
    
    summary = generator.generate_dataset(
        test_cases=10,       # 10 curated test cases
        training_size=50,    # 50 training (reduced from 100 for M1)
        bulk_size=200        # 200 bulk (reduced from 500 for M1)
    )
    
    # Print summary
    print(f"""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  GENERATION COMPLETE ✓                                             ║
    ║                                                                    ║
    ║  Generated {summary['total_applications']} applications with 6 documents each ║
    ║  Total documents: {summary['documents_generated']}                                   ║
    ║                                                                    ║
    ║  Location: {summary['base_path']}                          ║
    ║  Timestamp: {summary['timestamp']}            ║
    ║                                                                    ║
    ║  Ready for Phase 2: Extraction Agent Implementation                ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
