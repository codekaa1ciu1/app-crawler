#!/usr/bin/env python3
"""
Fix screenshot paths in the database to match actual files.
"""

import os
import sys
from app_crawler.database import CrawlerDatabase

def fix_screenshot_paths():
    """Fix screenshot paths in database to match actual files."""
    print("🔧 Fixing screenshot paths in database...")
    
    db = CrawlerDatabase('crawler_paths.db')
    paths = db.get_all_paths()
    
    for path in paths:
        path_id = path['path_id']
        print(f"\n📁 Processing path: {path_id}")
        
        # Check what screenshot files actually exist for this path
        screenshot_dir = os.path.join('screenshots', path_id)
        if os.path.exists(screenshot_dir):
            actual_files = [f for f in os.listdir(screenshot_dir) if f.endswith('.png')]
            actual_files.sort()
            print(f"   Found {len(actual_files)} actual screenshot files")
            
            # Get steps for this path
            steps = db.get_path_steps(path_id)
            print(f"   Database has {len(steps)} steps")
            
            # Update each step with correct screenshot path
            for i, step in enumerate(steps):
                step_number = step['step_number']
                old_path = step.get('screenshot_path', '')
                
                if i < len(actual_files):
                    # Map step to actual file
                    actual_file = actual_files[i]
                    new_relative_path = f"{path_id}/{actual_file}"
                    
                    print(f"   Step {step_number}: {old_path} -> {new_relative_path}")
                    
                    # Update the database
                    conn = db.db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE path_steps 
                        SET screenshot_path = ?
                        WHERE path_id = ? AND step_number = ?
                    """, (new_relative_path, path_id, step_number))
                    conn.commit()
                    conn.close()
                else:
                    print(f"   Step {step_number}: No matching file found")
        else:
            print(f"   No screenshot directory found at {screenshot_dir}")
    
    print("\n✅ Screenshot path fixing complete!")

def db_connection(self):
    """Get database connection (helper method)."""
    import sqlite3
    return sqlite3.connect(self.db_path)

# Add the helper method to CrawlerDatabase temporarily
CrawlerDatabase.db_connection = db_connection

if __name__ == "__main__":
    fix_screenshot_paths()