#!/usr/bin/env python3
"""
Unified Main Script - Runs both IndiaBix and PendulumEdu scrapers
Outputs are organized in separate folders:
- IndiaBix/output/
- pendulumedu/output/
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add both modules to path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "IndiaBix"))
sys.path.insert(0, str(root_dir / "pendulumedu"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def run_indiabix():
    """Run IndiaBix scraper and PDF generation"""
    print("\n" + "="*80)
    print(" " * 20 + "INDIABIX CURRENT AFFAIRS SCRAPER")
    print("="*80 + "\n")

    try:
        # Import IndiaBix modules
        sys.path.insert(0, str(root_dir / "IndiaBix"))
        from IndiaBix.main import main as indiabix_main

        # Run IndiaBix scraper
        result = indiabix_main()
        return result

    except Exception as e:
        logger.error(f"IndiaBix scraper failed: {str(e)}", exc_info=True)
        print(f"\n✗ IndiaBix scraper error: {str(e)}")
        return False


def run_pendulumedu():
    """Run PendulumEdu scraper and PDF generation"""
    print("\n" + "="*80)
    print(" " * 15 + "PENDULUMEDU CURRENT AFFAIRS SCRAPER")
    print("="*80 + "\n")

    try:
        # Import PendulumEdu modules
        sys.path.insert(0, str(root_dir / "pendulumedu"))
        from pendulumedu.main import main as pendulumedu_main

        # Run PendulumEdu scraper
        pendulumedu_main()
        return True

    except Exception as e:
        logger.error(f"PendulumEdu scraper failed: {str(e)}", exc_info=True)
        print(f"\n✗ PendulumEdu scraper error: {str(e)}")
        return False


def display_menu():
    """Display menu for user to choose which scraper to run"""
    print("\n" + "="*80)
    print(" " * 25 + "CURRENT AFFAIRS SCRAPER")
    print("="*80)
    print("\nChoose which scraper to run:")
    print("1. IndiaBix only")
    print("2. PendulumEdu only")
    print("3. Both (IndiaBix + PendulumEdu)")
    print("4. Exit")

    choice = input("\nEnter your choice (1-4): ").strip()
    return choice


def print_summary(indiabix_success, pendulumedu_success):
    """Print final summary"""
    print("\n" + "="*80)
    print(" " * 30 + "SUMMARY")
    print("="*80)

    print("\n📦 Output Locations:")
    print(f"   IndiaBix:    {root_dir / 'IndiaBix' / 'output'}")
    print(f"   PendulumEdu: {root_dir / 'pendulumedu' / 'output'}")

    print("\n📊 Results:")
    if indiabix_success:
        print("   ✓ IndiaBix scraper:    SUCCESS")
    else:
        print("   ✗ IndiaBix scraper:    SKIPPED/FAILED")

    if pendulumedu_success:
        print("   ✓ PendulumEdu scraper: SUCCESS")
    else:
        print("   ✗ PendulumEdu scraper: SKIPPED/FAILED")

    print("\n" + "="*80 + "\n")


def main():
    """Main orchestrator"""
    print("\n🚀 Current Affairs Scraper - Unified Entry Point")
    print(f"📍 Root Directory: {root_dir}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Uncomment below for interactive mode, or keep for automated run
    # choice = display_menu()

    # For now, run both by default
    choice = "3"

    indiabix_success = False
    pendulumedu_success = False

    if choice == "1":
        indiabix_success = run_indiabix()
    elif choice == "2":
        pendulumedu_success = run_pendulumedu()
    elif choice == "3":
        indiabix_success = run_indiabix()
        pendulumedu_success = run_pendulumedu()
    elif choice == "4":
        print("\n👋 Exiting...")
        return
    else:
        print("\n❌ Invalid choice. Please try again.")
        return main()

    # Print summary
    print_summary(indiabix_success, pendulumedu_success)

    # Return success status
    if indiabix_success or pendulumedu_success:
        print("✓ Scraping completed successfully!")
        return True
    else:
        print("✗ Scraping encountered errors. Check logs for details.")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
