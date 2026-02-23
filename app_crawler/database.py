"""Database layer for storing crawler paths using SQLite."""
import sqlite3
import json
import uuid
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
                description TEXT,
                is_active INTEGER DEFAULT 1,
                last_step_number INTEGER DEFAULT 0
            )
        """)
        
        # Create directed graph tables
        
        # Create graph_nodes table (represents UI states)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_nodes (
                node_id TEXT PRIMARY KEY,
                app_package TEXT,
                activity_name TEXT,
                state_hash TEXT UNIQUE,
                dom_snapshot TEXT,
                screenshot_path TEXT,
                element_count INTEGER,
                is_initial_state INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create graph_edges table (represents transitions/actions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS graph_edges (
                edge_id TEXT PRIMARY KEY,
                from_node_id TEXT,
                to_node_id TEXT,
                action_type TEXT,
                element_selector TEXT,
                element_text TEXT,
                element_attributes TEXT,
                input_value TEXT,
                is_valid INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_node_id) REFERENCES graph_nodes(node_id),
                FOREIGN KEY (to_node_id) REFERENCES graph_nodes(node_id)
            )
        """)
        
        # Create journeys table (represents completed paths/cycles)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journeys (
                journey_id TEXT PRIMARY KEY,
                app_package TEXT,
                start_node_id TEXT,
                end_node_id TEXT,
                path_edges TEXT,  -- JSON array of edge IDs
                journey_type TEXT, -- 'cycle', 'linear', 'dead_end'
                step_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (start_node_id) REFERENCES graph_nodes(node_id),
                FOREIGN KEY (end_node_id) REFERENCES graph_nodes(node_id)
            )
        """)
        
        # Create path_steps table (legacy compatibility)
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
        
        # Create indexes for faster queries (after all tables are created)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paths_app_package 
            ON paths(app_package)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_app_package 
            ON graph_nodes(app_package)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nodes_state_hash 
            ON graph_nodes(state_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_from_node 
            ON graph_edges(from_node_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_edges_to_node 
            ON graph_edges(to_node_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_journeys_app_package 
            ON journeys(app_package)
        """)
        
        # Migrate existing schema if needed
        self._migrate_schema(cursor)
        
        conn.commit()
        conn.close()
    
    def clean_database(self):
        """Clean and reset the database to a fresh state.
        
        This will:
        1. Drop all existing tables
        2. Recreate fresh database structure with directed graph tables
        3. Reset to clean state ready for new crawling sessions
        """
        print("🧹 Cleaning database...")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            print(f"   📋 Found {len(tables)} tables to clean")
            
            # Drop all existing tables
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # Keep SQLite internal table
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                    print(f"   🗑️  Dropped table: {table_name}")
        
        # Recreate fresh database structure
        cursor.execute("VACUUM")  # Optimize the database file
        conn.commit()
        conn.close()
        
        # Reinitialize with fresh structure
        print("   🏗️  Creating fresh database structure...")
        self.init_database()
        
        print("✅ Database cleaned successfully!")
        print("   📍 Ready for new directed graph crawling sessions")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics.
        
        Returns:
            Dictionary with table counts and sizes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                stats[f"{table_name}_count"] = count
        
        conn.close()
        return stats
    
    @property
    def connection(self):
        """Get database connection for advanced operations."""
        return sqlite3.connect(self.db_path)
    
    def _migrate_schema(self, cursor):
        """Apply schema migrations for existing databases."""
        # Check if new columns exist
        cursor.execute("PRAGMA table_info(paths)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_active' not in columns:
            cursor.execute("ALTER TABLE paths ADD COLUMN is_active INTEGER DEFAULT 1")
        
        if 'last_step_number' not in columns:
            cursor.execute("ALTER TABLE paths ADD COLUMN last_step_number INTEGER DEFAULT 0")
            
            # Backfill last_step_number for existing paths
            cursor.execute("""
                UPDATE paths SET last_step_number = (
                    SELECT COALESCE(MAX(step_number), 0)
                    FROM path_steps 
                    WHERE path_steps.path_id = paths.path_id
                )
            """)
    
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
    
    def get_active_path_for_app(self, app_package: str) -> Optional[Dict[str, Any]]:
        """Get the active path for a specific app package.
        
        Args:
            app_package: Package name or bundle ID
            
        Returns:
            Active path dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM paths 
            WHERE app_package = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """, (app_package,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def create_or_get_active_path(self, app_package: str, name: str, 
                                 platform: str, description: str = "") -> str:
        """Get existing active path or create new one for app package.
        
        Args:
            app_package: Package name or bundle ID
            name: Human-readable name for new paths
            platform: 'android' or 'ios'
            description: Optional description
            
        Returns:
            Path ID of active path
        """
        # Try to get existing active path
        active_path = self.get_active_path_for_app(app_package)
        
        if active_path:
            return active_path['path_id']
        
        # Create new path
        new_path_id = f"path_{uuid.uuid4().hex[:8]}"
        self.create_path(
            path_id=new_path_id,
            name=name,
            platform=platform,
            app_package=app_package,
            description=description
        )
        
        return new_path_id
    
    def set_path_active(self, path_id: str, is_active: bool) -> bool:
        """Set the active status of a path.
        
        Args:
            path_id: Path identifier
            is_active: Whether path should be active
            
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE paths 
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE path_id = ?
        """, (1 if is_active else 0, path_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def update_last_step_number(self, path_id: str, step_number: int) -> bool:
        """Update the last step number for a path.
        
        Args:
            path_id: Path identifier
            step_number: Last completed step number
            
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE paths 
            SET last_step_number = ?, updated_at = CURRENT_TIMESTAMP
            WHERE path_id = ?
        """, (step_number, path_id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    # ===== DIRECTED GRAPH METHODS =====
    
    def create_or_get_node(self, app_package: str, activity_name: str, 
                          state_hash: str, dom_snapshot: str = "", 
                          screenshot_path: str = "", element_count: int = 0,
                          is_initial_state: bool = False) -> str:
        """Create or get existing node by state hash.
        
        Args:
            app_package: Package name
            activity_name: Current activity name
            state_hash: Unique hash for this UI state
            dom_snapshot: DOM content snapshot
            screenshot_path: Path to screenshot
            element_count: Number of elements on screen
            is_initial_state: Whether this is the initial app state
            
        Returns:
            Node ID
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if node already exists
        cursor.execute("""
            SELECT node_id FROM graph_nodes 
            WHERE state_hash = ?
        """, (state_hash,))
        
        existing_node = cursor.fetchone()
        if existing_node:
            conn.close()
            return existing_node['node_id']
        
        # Create new node
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        cursor.execute("""
            INSERT INTO graph_nodes 
            (node_id, app_package, activity_name, state_hash, dom_snapshot, 
             screenshot_path, element_count, is_initial_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (node_id, app_package, activity_name, state_hash, dom_snapshot[:5000], 
              screenshot_path, element_count, 1 if is_initial_state else 0))
        
        conn.commit()
        conn.close()
        
        return node_id
    
    def create_edge(self, from_node_id: str, to_node_id: str, action_type: str,
                   element_selector: str, element_text: str = "", 
                   element_attributes: Optional[Dict] = None,
                   input_value: str = "", is_valid: bool = True) -> str:
        """Create an edge representing an action transition.
        
        Args:
            from_node_id: Source node ID
            to_node_id: Target node ID (None if no state change)
            action_type: Type of action (click, input, etc.)
            element_selector: Element selector used
            element_text: Text content of element
            element_attributes: Element attributes as dict
            input_value: Input value if applicable
            is_valid: Whether this action causes valid state transition
            
        Returns:
            Edge ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        edge_id = f"edge_{uuid.uuid4().hex[:8]}"
        attributes_json = json.dumps(element_attributes) if element_attributes else ""
        
        cursor.execute("""
            INSERT INTO graph_edges 
            (edge_id, from_node_id, to_node_id, action_type, element_selector,
             element_text, element_attributes, input_value, is_valid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (edge_id, from_node_id, to_node_id, action_type, element_selector,
              element_text, attributes_json, input_value, 1 if is_valid else 0))
        
        conn.commit()
        conn.close()
        
        return edge_id
    
    def update_edge_success(self, edge_id: str, success: bool):
        """Update edge success/failure statistics.
        
        Args:
            edge_id: Edge identifier
            success: Whether the action was successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if success:
            cursor.execute("""
                UPDATE graph_edges 
                SET success_count = success_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE edge_id = ?
            """, (edge_id,))
        else:
            cursor.execute("""
                UPDATE graph_edges 
                SET failure_count = failure_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE edge_id = ?
            """, (edge_id,))
        
        conn.commit()
        conn.close()
    
    def get_node_by_hash(self, state_hash: str) -> Optional[Dict[str, Any]]:
        """Get node by state hash.
        
        Args:
            state_hash: State hash to search for
            
        Returns:
            Node dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM graph_nodes WHERE state_hash = ?
        """, (state_hash,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_edges_from_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all edges originating from a node.
        
        Args:
            node_id: Source node ID
            
        Returns:
            List of edge dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM graph_edges 
            WHERE from_node_id = ?
            ORDER BY created_at
        """, (node_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def detect_cycle(self, start_node_id: str, current_path: List[str]) -> Optional[List[str]]:
        """Detect if current path forms a cycle.
        
        Args:
            start_node_id: Starting node ID
            current_path: List of node IDs in current path
            
        Returns:
            List of node IDs forming cycle, or None if no cycle
        """
        if start_node_id in current_path:
            # Found cycle
            cycle_start_index = current_path.index(start_node_id)
            return current_path[cycle_start_index:] + [start_node_id]
        
        return None
    
    def create_journey(self, app_package: str, start_node_id: str, 
                      end_node_id: str, path_edges: List[str], journey_type: str) -> str:
        """Create a journey record for completed path.
        
        Args:
            app_package: Package name
            start_node_id: Starting node
            end_node_id: Ending node
            path_edges: List of edge IDs in the journey
            journey_type: 'cycle', 'linear', or 'dead_end'
            
        Returns:
            Journey ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        journey_id = f"journey_{uuid.uuid4().hex[:8]}"
        edges_json = json.dumps(path_edges)
        
        cursor.execute("""
            INSERT INTO journeys 
            (journey_id, app_package, start_node_id, end_node_id, 
             path_edges, journey_type, step_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (journey_id, app_package, start_node_id, end_node_id, 
              edges_json, journey_type, len(path_edges)))
        
        conn.commit()
        conn.close()
        
        return journey_id
    
    def get_unexplored_edges_from_node(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all edges from a node that haven't been fully explored.
        
        Args:
            node_id: The node ID to check
            
        Returns:
            List of edge dictionaries that could lead to unexplored states
        """
        query = """
        SELECT e.*, n.activity_name, n.state_hash
        FROM graph_edges e
        LEFT JOIN graph_nodes n ON e.to_node_id = n.node_id
        WHERE e.from_node_id = ? AND e.is_valid = 1
        ORDER BY e.created_at DESC
        """
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (node_id,))
        
        edges = []
        for row in cursor.fetchall():
            edge_dict = dict(row)
            edges.append(edge_dict)
        
        conn.close()
        return edges
    
    def get_node_by_hash(self, state_hash: str) -> Optional[Dict[str, Any]]:
        """Get node by its state hash.
        
        Args:
            state_hash: State hash to look for
            
        Returns:
            Node dictionary or None if not found
        """
        query = """
        SELECT * FROM graph_nodes 
        WHERE state_hash = ? 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, (state_hash,))
        
        row = cursor.fetchone()
        result = dict(row) if row else None
        conn.close()
        return result
    
    def get_app_graph_stats(self, app_package: str) -> Dict[str, Any]:
        """Get graph statistics for an app.
        
        Args:
            app_package: Package name
            
        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Count nodes
        cursor.execute("""
            SELECT COUNT(*) as node_count FROM graph_nodes 
            WHERE app_package = ?
        """, (app_package,))
        node_count = cursor.fetchone()['node_count']
        
        # Count valid edges
        cursor.execute("""
            SELECT COUNT(*) as valid_edge_count FROM graph_edges e
            JOIN graph_nodes n ON e.from_node_id = n.node_id
            WHERE n.app_package = ? AND e.is_valid = 1
        """, (app_package,))
        valid_edge_count = cursor.fetchone()['valid_edge_count']
        
        # Count invalid edges  
        cursor.execute("""
            SELECT COUNT(*) as invalid_edge_count FROM graph_edges e
            JOIN graph_nodes n ON e.from_node_id = n.node_id
            WHERE n.app_package = ? AND e.is_valid = 0
        """, (app_package,))
        invalid_edge_count = cursor.fetchone()['invalid_edge_count']
        
        # Count journeys
        cursor.execute("""
            SELECT COUNT(*) as journey_count FROM journeys 
            WHERE app_package = ?
        """, (app_package,))
        journey_count = cursor.fetchone()['journey_count']
        
        # Count cycles
        cursor.execute("""
            SELECT COUNT(*) as cycle_count FROM journeys 
            WHERE app_package = ? AND journey_type = 'cycle'
        """, (app_package,))
        cycle_count = cursor.fetchone()['cycle_count']
        
        conn.close()
        
        return {
            'app_package': app_package,
            'node_count': node_count,
            'valid_edge_count': valid_edge_count,
            'invalid_edge_count': invalid_edge_count,
            'journey_count': journey_count, 
            'cycle_count': cycle_count,
            'coverage_ratio': valid_edge_count / max(1, valid_edge_count + invalid_edge_count)
        }

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
