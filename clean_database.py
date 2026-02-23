#!/usr/bin/env python3
"""
Database cleanup script for app crawler.

This script will clean and reset the database to a fresh state with
the new directed graph structure ready for crawling.

Usage:
    python clean_database.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app_crawler.database import CrawlerDatabase

def main():
    """Clean the crawler database."""
    print("=" * 60)
    print("🧹 App Crawler Database Cleanup")
    print("=" * 60)
    
    # Check for --force flag
    force_cleanup = "--force" in sys.argv or "-f" in sys.argv
    
    # Show current database stats
    db = CrawlerDatabase()
    
    print("\n📊 Current Database State:")
    try:
        stats = db.get_database_stats()
        if stats:
            for table_stat, count in stats.items():
                table_name = table_stat.replace('_count', '')
                print(f"   📋 {table_name}: {count} records")
        else:
            print("   📋 No tables found")
    except Exception as e:
        print(f"   ❌ Error reading current stats: {e}")
    
    # Confirm cleanup
    if not force_cleanup:
        print("\n⚠️  This will delete ALL crawler data and reset to fresh state!")
        print("   🗑️  All paths, steps, and graph data will be removed")
        print("   🏗️  Database will be recreated with new directed graph structure")
        
        confirm = input("\n🤔 Are you sure you want to clean the database? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("\n⏹️  Database cleanup cancelled")
            print("   📊 Database remains unchanged")
            print("\n" + "=" * 60)
            return 0
    else:
        print("\n🚀 Force cleanup mode enabled (--force flag)")
    
    print("\n🚀 Proceeding with database cleanup...")
    
    try:
        # Clean the database
        db.clean_database()
        
        # Show new stats
        print("\n📊 Database After Cleanup:")
        new_stats = db.get_database_stats()
        if new_stats:
            for table_stat, count in new_stats.items():
                table_name = table_stat.replace('_count', '')
                print(f"   📋 {table_name}: {count} records")
        else:
            print("   📋 All tables clean and ready")
            
        print("\n🎉 Database cleanup completed successfully!")
        print("   ✅ Ready for new directed graph crawling sessions")
        print("   🚀 You can now run: python runner/test_directed_graph_crawl.py")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        return 1
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())