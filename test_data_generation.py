#!/usr/bin/env python3
"""
Quick Test - Generate small dataset to verify everything works
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data.synthetic_generators import MasterDatasetGenerator


def main():
    """Generate test dataset."""
    
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  QUICK TEST - SMALL DATASET GENERATION                             ║
    ║  Testing all generators with minimal dataset                       ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize master generator
    generator = MasterDatasetGenerator(seed=42, base_path="data")
    
    # Generate small test dataset
    print("\nGenerating sample dataset (3 test + 10 training + 50 bulk)...\n")
    
    summary = generator.generate_dataset(
        test_cases=3,       # Just 3 for quick test
        training_size=10,   # Just 10 for quick test
        bulk_size=50        # Just 50 for quick test
    )
    
    # Print summary
    print(f"""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  TEST GENERATION COMPLETE ✓                                        ║
    ║                                                                    ║
    ║  Generated:                                                        ║
    ║  • Total Applications: {summary['total_applications']:<3}                                     ║
    ║  • Total Documents:   {summary['documents_generated']:<3}                                   ║
    ║                                                                    ║
    ║  Location: {summary['base_path']}                          ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verify directory structure
    import os
    data_path = Path(summary['base_path'])
    
    print(f"\n📂 Directory Structure:")
    if (data_path / "raw").exists():
        print(f"  ✓ data/raw/ - Metadata files")
        csv_file = data_path / "raw" / "applications_metadata.csv"
        if csv_file.exists():
            with open(csv_file) as f:
                lines = f.readlines()
            print(f"    • applications_metadata.csv ({len(lines)-1} records)")
    
    if (data_path / "processed" / "documents").exists():
        docs_path = data_path / "processed" / "documents"
        num_apps = len([d for d in docs_path.iterdir() if d.is_dir()])
        print(f"  ✓ data/processed/documents/ - {num_apps} application folders")
        
        # Show sample
        sample_app = list(docs_path.iterdir())[0]
        if sample_app.is_dir():
            docs = list(sample_app.glob("*"))
            print(f"\n  Sample Application ({sample_app.name}):")
            for doc in sorted(docs):
                size_kb = doc.stat().st_size / 1024
                print(f"    • {doc.name} ({size_kb:.1f} KB)")
    
    print(f"\n✓ Test generation successful! Ready for full dataset generation.\n")


if __name__ == "__main__":
    main()
