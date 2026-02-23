#!/usr/bin/env python3
"""
Test script for the Enhanced BFS crawler with directed graph tracking.

This script validates the new graph-based approach where:
- Each UI state is a graph node
- Each action is a graph edge
- Valid edges represent successful UI transitions
- Invalid edges represent failed actions
- Journey cycles detect completed navigation loops

Usage:
    python runner/test_directed_graph_crawl.py
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app_crawler.crawler import AppCrawler
from app_crawler.database import CrawlerDatabase
from app_crawler.ai_service import AIService

def test_directed_graph_crawl():
    """Test the new directed graph implementation with Wikipedia app."""
    print("=" * 60)
    print("🧪 Testing Enhanced BFS Crawler with Directed Graph")
    print("=" * 60)
    
    # Configuration
    APP_PACKAGE = "org.wikipedia"
    DEVICE_ID = "emulator-5554"
    MAX_STEPS = 500  # Small number for testing
    
    print(f"📱 App Package: {APP_PACKAGE}")
    print(f"🔧 Device ID: {DEVICE_ID}")
    print(f"🎯 Max Steps: {MAX_STEPS}")
    print(f"📈 Strategy: Enhanced BFS + Directed Graph + Systematic Element Testing")
    
    # Initialize services
    ai_service = AIService()
    db = CrawlerDatabase()
    
    # Initialize crawler with graph tracking
    crawler = AppCrawler(
        app_package=APP_PACKAGE,
        device_id=DEVICE_ID,
        db=db,
        ai=ai_service
    )
    
    print("\n🚀 Starting directed graph crawl...")
    try:
        # Start the enhanced crawl with graph tracking
        crawler.start_crawl(max_steps=MAX_STEPS)
        
        print("\n✅ Directed graph crawl completed successfully!")
        
        # Display graph statistics
        print("\n📊 Final Graph Analysis:")
        graph_stats = db.get_app_graph_stats(APP_PACKAGE)
        print(f"   🏗️  Graph Nodes: {graph_stats.get('node_count', 0)}")
        print(f"   🔗 Graph Edges: {graph_stats.get('edge_count', 0)}")
        print(f"   ✅ Valid Transitions: {graph_stats.get('valid_edges', 0)}")
        print(f"   ❌ Invalid Actions: {graph_stats.get('invalid_edges', 0)}")
        print(f"   🔄 Journey Cycles: {graph_stats.get('journey_cycles', 0)}")
        
        # Validate graph structure
        print("\n🔍 Graph Structure Validation:")
        
        # Get all nodes for this app
        query = "SELECT * FROM graph_nodes WHERE app_package = ?"
        cursor = db.connection.cursor()
        cursor.execute(query, (APP_PACKAGE,))
        nodes = cursor.fetchall()
        
        print(f"   📍 Total nodes created: {len(nodes)}")
        
        # Get all edges for this app
        edge_query = """
        SELECT e.*, n1.activity_name as from_activity, n2.activity_name as to_activity
        FROM graph_edges e
        JOIN graph_nodes n1 ON e.from_node_id = n1.node_id
        LEFT JOIN graph_nodes n2 ON e.to_node_id = n2.node_id
        WHERE n1.app_package = ?
        """
        cursor.execute(edge_query, (APP_PACKAGE,))
        edges = cursor.fetchall()
        
        print(f"   🔗 Total edges created: {len(edges)}")
        
        if edges:
            valid_edges = [e for e in edges if e[7]]  # is_valid column
            invalid_edges = [e for e in edges if not e[7]]
            
            print(f"   ✅ Valid edges: {len(valid_edges)}")
            print(f"   ❌ Invalid edges: {len(invalid_edges)}")
            
            # Show some example edges
            print(f"\n📋 Example Edges (showing first 3):")
            for i, edge in enumerate(edges[:3]):
                validity = "✅" if edge[7] else "❌"
                action_type = edge[3]  # action_type column
                element_text = edge[5] or edge[4]  # element_text or element_selector
                from_activity = edge[8] or "Unknown"  # from_activity
                to_activity = edge[9] or "No Change"  # to_activity
                
                print(f"   {i+1}. {validity} {action_type}('{element_text}') {from_activity} → {to_activity}")
        
        # Get journey information
        journey_query = "SELECT * FROM journeys WHERE app_package = ?"
        cursor.execute(journey_query, (APP_PACKAGE,))
        journeys = cursor.fetchall()
        
        if journeys:
            print(f"\n🔄 Journey Cycles Detected: {len(journeys)}")
            for i, journey in enumerate(journeys):
                journey_type = journey[5]  # journey_type column
                path_edges = journey[4]  # path_edges column (JSON)
                print(f"   {i+1}. {journey_type} cycle with {len(path_edges.split(',')) if path_edges else 0} edges")
        else:
            print(f"\n🔄 No journey cycles detected yet")
        
        print(f"\n🎉 Directed graph validation completed!")
        print(f"📝 Graph data persisted in database for analysis")
        
    except KeyboardInterrupt:
        print("\n⏹️  Crawl interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during crawl: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            crawler.disconnect()
        except:
            pass
    
    print("\n" + "=" * 60)
    print("🏁 Directed Graph Crawler Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_directed_graph_crawl()