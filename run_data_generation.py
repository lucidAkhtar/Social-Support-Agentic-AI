#!/usr/bin/env python3
"""
Dataset Generation Runner
Execute to generate complete synthetic dataset: 10 test + 100 training + 500 bulk
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.synthetic_generators import MasterDatasetGenerator


def main():
    """Generate complete dataset."""
    
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  SOCIAL SUPPORT AI - SYNTHETIC DATASET GENERATOR                   ║
    ║  Abu Dhabi Government Context                                      ║
    ║  Production-Grade Multimodal Data Generation                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize master generator with fixed seed for reproducibility
    generator = MasterDatasetGenerator(seed=42, base_path="data")
    
    # Generate complete dataset
    summary = generator.generate_dataset(
        test_cases=10,      # 10 curated test scenarios
        training_size=100,   # 100 for ML training
        bulk_size=500       # 500 for performance demo
    )
    
    # Print final summary
    print(f"""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  GENERATION COMPLETE ✓                                             ║
    ║                                                                    ║
    ║  Dataset Summary:                                                  ║
    ║  • Total Applications: {summary['total_applications']:<5}                                    ║
    ║  • Total Documents:   {summary['documents_generated']:<5}                                  ║
    ║  • Test Cases:        {summary['test_cases']:<5}  (curated scenarios)            ║
    ║  • Training Set:      {summary['training']:<5}  (ML model training)            ║
    ║  • Bulk Set:          {summary['bulk']:<5}  (performance demo)              ║
    ║                                                                    ║
    ║  Location: {summary['base_path']}                          ║
    ║                                                                    ║
    ║  Files Generated:                                                  ║
    ║  • CSV Metadata:      data/raw/applications_metadata.csv           ║
    ║  • JSON Complete:     data/raw/applications_complete.json          ║
    ║  • Documents:         data/processed/documents/APP-*/               ║
    ║                                                                    ║
    ║  Next Steps:                                                       ║
    ║  1. Run extraction agent on test set (10 apps)                    ║
    ║  2. Validate extracted data against sources                        ║
    ║  3. Train ML model on training set (100 apps)                     ║
    ║  4. Demo with bulk set (500 apps) for performance                 ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
