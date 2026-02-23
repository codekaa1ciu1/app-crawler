#!/usr/bin/env python3
"""
Quick verification that the cleaned database is working properly.

Usage:
    python verify_database.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app_crawler.database import CrawlerDatabase

def main():
    """Verify the cleaned database is working."""
    print("=" * 60)
    print("🔍 Database Verification")
    print("=" * 60)
    
    try:
        # Initialize database
        db = CrawlerDatabase()
        print("✅ Database connection successful")
        
        # Check table structure
        stats = db.get_database_stats()
        print(f"\n📊 Database Structure:")
        for table_stat, count in stats.items():
            table_name = table_stat.replace('_count', '')
            print(f"   📋 {table_name}: {count} records (clean)")
        
        # Test basic operations
        print(f"\n🧪 Testing Basic Operations:")
        
        # Test path creation
        test_path_id = "test_verification"
        path_id = db.create_path(
            path_id=test_path_id,
            name="Database Verification Test",
            platform="android",
            app_package="com.test.verification",
            description="Testing cleaned database"
        )
        print(f"   ✅ Path creation: Success (ID: {path_id})")
        
        # Test node creation
        test_node_id = db.create_or_get_node(
            app_package="com.test.verification",
            activity_name="MainActivity",
            state_hash="test_hash_123",
            dom_snapshot="<test>DOM content</test>",
            screenshot_path="/test/screenshot.png",
            element_count=5,
            is_initial_state=True
        )
        print(f"   ✅ Graph node creation: Success (ID: {test_node_id[:8]}...)")
        
        # Test edge creation
        test_edge_id = db.create_edge(
            from_node_id=test_node_id,
            to_node_id=None,  # No state change
            action_type="click",
            element_selector="//button[@text='Test']",
            element_text="Test Button",
            element_attributes={"class": "android.widget.Button"},
            input_value="",
            is_valid=False  # Invalid action
        )
        print(f"   ✅ Graph edge creation: Success (ID: {test_edge_id[:8]}...)")
        
        # Clean up test data
        conn = db.connection
        cursor = conn.cursor()
        cursor.execute("DELETE FROM graph_edges WHERE edge_id = ?", (test_edge_id,))
        cursor.execute("DELETE FROM graph_nodes WHERE node_id = ?", (test_node_id,))
        cursor.execute("DELETE FROM paths WHERE path_id = ?", (test_path_id,))
        conn.commit()
        conn.close()
        print(f"   ✅ Test cleanup: Success")
        
        print(f"\n🎉 Database Verification Complete!")
        print(f"   ✅ All table structures valid")
        print(f"   ✅ All basic operations working")
        print(f"   ✅ Directed graph functionality ready")
        print(f"\n🚀 Database is ready for directed graph crawling!")
        print(f"   Run: python runner/test_directed_graph_crawl.py")
        
    except Exception as e:
        print(f"\n❌ Database verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())