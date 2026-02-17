"""Database layer for storing crawler paths using SQLite."""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any


class CrawlerDatabase:
    """SQLite database manager for crawler paths."""
    
    def __init__(self, db_path: str = "crawler_paths.db"):
        """Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create paths table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id TEXT UNIQUE,
                name TEXT,
                platform TEXT,
                app_package TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        # Create path_steps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS path_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id TEXT,
                step_number INTEGER,
                action_type TEXT,
                element_selector TEXT,
                element_attributes TEXT,
                input_value TEXT,
                screenshot_path TEXT,
                dom_snapshot TEXT,
                ai_reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (path_id) REFERENCES paths(path_id)
            )
        """)
        
        # Create human_interventions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS human_interventions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id TEXT,
                step_number INTEGER,
                intervention_type TEXT,
                ai_question TEXT,
                human_response TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (path_id) REFERENCES paths(path_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_path(self, path_id: str, name: str, platform: str, 
                   app_package: str, description: str = "") -> int:
        """Create a new crawler path.
        
        Args:
            path_id: Unique identifier for the path
            name: Human-readable name
            platform: 'android' or 'ios'
            app_package: Package name or bundle ID
            description: Optional description
            
        Returns:
            Database ID of created path
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO paths (path_id, name, platform, app_package, description)
            VALUES (?, ?, ?, ?, ?)
        """, (path_id, name, platform, app_package, description))
        
        path_db_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return path_db_id
    
    def add_path_step(self, path_id: str, step_number: int, action_type: str,
                     element_selector: str, element_attributes: Dict[str, Any],
                     input_value: Optional[str] = None,
                     screenshot_path: Optional[str] = None,
                     dom_snapshot: Optional[str] = None,
                     ai_reasoning: Optional[str] = None) -> int:
        """Add a step to a crawler path.
        
        Args:
            path_id: Path identifier
            step_number: Sequential step number
            action_type: Type of action (click, input, swipe, etc.)
            element_selector: Selector for the element
            element_attributes: JSON-serializable dict of element attributes
            input_value: Value to input (for input actions)
            screenshot_path: Path to screenshot
            dom_snapshot: DOM tree at this step
            ai_reasoning: AI's reasoning for this action
            
        Returns:
            Database ID of created step
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO path_steps (
                path_id, step_number, action_type, element_selector,
                element_attributes, input_value, screenshot_path,
                dom_snapshot, ai_reasoning
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            path_id, step_number, action_type, element_selector,
            json.dumps(element_attributes), input_value, screenshot_path,
            dom_snapshot, ai_reasoning
        ))
        
        step_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return step_id
    
    def add_human_intervention(self, path_id: str, step_number: int,
                              intervention_type: str, ai_question: str,
                              human_response: str) -> int:
        """Record a human intervention in the crawling process.
        
        Args:
            path_id: Path identifier
            step_number: Step where intervention occurred
            intervention_type: Type of intervention needed
            ai_question: Question posed by AI
            human_response: Human's response
            
        Returns:
            Database ID of intervention record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO human_interventions (
                path_id, step_number, intervention_type, ai_question, human_response
            )
            VALUES (?, ?, ?, ?, ?)
        """, (path_id, step_number, intervention_type, ai_question, human_response))
        
        intervention_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return intervention_id
    
    def get_all_paths(self) -> List[Dict[str, Any]]:
        """Get all crawler paths.
        
        Returns:
            List of path dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*, COUNT(ps.id) as step_count
            FROM paths p
            LEFT JOIN path_steps ps ON p.path_id = ps.path_id
            GROUP BY p.id
            ORDER BY p.created_at DESC
        """)
        
        paths = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return paths
    
    def get_path_by_id(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific path by its ID.
        
        Args:
            path_id: Path identifier
            
        Returns:
            Path dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM paths WHERE path_id = ?", (path_id,))
        row = cursor.fetchone()
        
        if row is None:
            conn.close()
            return None
        
        path = dict(row)
        conn.close()
        
        return path
    
    def get_path_steps(self, path_id: str) -> List[Dict[str, Any]]:
        """Get all steps for a specific path.
        
        Args:
            path_id: Path identifier
            
        Returns:
            List of step dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM path_steps
            WHERE path_id = ?
            ORDER BY step_number ASC
        """, (path_id,))
        
        steps = []
        for row in cursor.fetchall():
            step = dict(row)
            # Parse JSON attributes
            if step['element_attributes']:
                step['element_attributes'] = json.loads(step['element_attributes'])
            steps.append(step)
        
        conn.close()
        return steps
    
    def get_human_interventions(self, path_id: str) -> List[Dict[str, Any]]:
        """Get all human interventions for a path.
        
        Args:
            path_id: Path identifier
            
        Returns:
            List of intervention dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM human_interventions
            WHERE path_id = ?
            ORDER BY step_number ASC
        """, (path_id,))
        
        interventions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return interventions
    
    def update_path(self, path_id: str, name: Optional[str] = None,
                   description: Optional[str] = None) -> bool:
        """Update path metadata.
        
        Args:
            path_id: Path identifier
            name: New name (optional)
            description: New description (optional)
            
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(path_id)
        
        query = f"UPDATE paths SET {', '.join(updates)} WHERE path_id = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_path(self, path_id: str) -> bool:
        """Delete a path and all its steps.
        
        Args:
            path_id: Path identifier
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete steps first (due to foreign key)
        cursor.execute("DELETE FROM path_steps WHERE path_id = ?", (path_id,))
        cursor.execute("DELETE FROM human_interventions WHERE path_id = ?", (path_id,))
        cursor.execute("DELETE FROM paths WHERE path_id = ?", (path_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
