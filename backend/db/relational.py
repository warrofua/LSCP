"""
SQLite Database for LSCP
Stores concepts, relationships, delta scores, and bridge mechanisms
"""
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json

class LSCPDatabase:
    """Manages the relational database for LSCP"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()

    def _initialize_db(self):
        """Create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Concepts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                coordinates_x REAL,
                coordinates_y REAL,
                coordinates_z REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Relationships table (edges)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_a_id INTEGER NOT NULL,
                concept_b_id INTEGER NOT NULL,
                human_distance REAL NOT NULL,
                latent_distance REAL NOT NULL,
                delta REAL NOT NULL,
                bridge_mechanism TEXT,
                internal_monologue TEXT,
                relationship_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (concept_a_id) REFERENCES concepts(id),
                FOREIGN KEY (concept_b_id) REFERENCES concepts(id),
                UNIQUE(concept_a_id, concept_b_id)
            )
        """)

        # Add internal_monologue column if it doesn't exist (migration)
        try:
            cursor.execute("ALTER TABLE relationships ADD COLUMN internal_monologue TEXT")
            print("  ✓ Added internal_monologue column to relationships table")
        except Exception:
            pass  # Column already exists

        # Scans table (audit log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anchor_concept_id INTEGER NOT NULL,
                human_vector TEXT NOT NULL,
                latent_vector TEXT NOT NULL,
                avg_delta REAL NOT NULL,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (anchor_concept_id) REFERENCES concepts(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_delta ON relationships(delta)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(scan_timestamp)")

        self.conn.commit()

    def add_concept(self, name: str) -> int:
        """Add a concept and return its ID"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO concepts (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Concept already exists, return existing ID
            cursor.execute("SELECT id FROM concepts WHERE name = ?", (name,))
            return cursor.fetchone()[0]

    def get_concept_id(self, name: str) -> Optional[int]:
        """Get concept ID by name"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM concepts WHERE name = ?", (name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def add_relationship(
        self,
        concept_a: str,
        concept_b: str,
        human_distance: float,
        latent_distance: float,
        delta: float,
        bridge_mechanism: Optional[str] = None,
        internal_monologue: Optional[str] = None,
        relationship_type: str = "semantic"
    ) -> int:
        """Add a relationship between two concepts"""
        concept_a_id = self.add_concept(concept_a)
        concept_b_id = self.add_concept(concept_b)

        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO relationships
                (concept_a_id, concept_b_id, human_distance, latent_distance, delta, bridge_mechanism, internal_monologue, relationship_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (concept_a_id, concept_b_id, human_distance, latent_distance, delta, bridge_mechanism, internal_monologue, relationship_type))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Relationship exists, update it
            cursor.execute("""
                UPDATE relationships
                SET human_distance = ?, latent_distance = ?, delta = ?, bridge_mechanism = ?, internal_monologue = ?, relationship_type = ?
                WHERE concept_a_id = ? AND concept_b_id = ?
            """, (human_distance, latent_distance, delta, bridge_mechanism, internal_monologue, relationship_type, concept_a_id, concept_b_id))
            self.conn.commit()
            return cursor.lastrowid

    def add_scan(
        self,
        anchor_concept: str,
        human_vector: List[str],
        latent_vector: List[str],
        avg_delta: float
    ) -> int:
        """Record a complete scan operation"""
        concept_id = self.add_concept(anchor_concept)

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO scans (anchor_concept_id, human_vector, latent_vector, avg_delta)
            VALUES (?, ?, ?, ?)
        """, (concept_id, json.dumps(human_vector), json.dumps(latent_vector), avg_delta))
        self.conn.commit()
        return cursor.lastrowid

    def get_high_delta_relationships(self, threshold: float = 0.3, limit: int = 100) -> List[Dict]:
        """Get relationships with high delta scores"""
        import struct

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                c1.name as concept_a,
                c2.name as concept_b,
                r.human_distance,
                r.latent_distance,
                r.delta,
                r.bridge_mechanism
            FROM relationships r
            JOIN concepts c1 ON r.concept_a_id = c1.id
            JOIN concepts c2 ON r.concept_b_id = c2.id
            WHERE r.delta >= ?
            ORDER BY r.delta DESC
            LIMIT ?
        """, (threshold, limit))

        results = []
        for row in cursor.fetchall():
            # Handle both blob (corrupted) and real (normal) formats
            human_dist = row['human_distance']
            if isinstance(human_dist, bytes):
                # Decode 4-byte IEEE 754 float from blob
                human_dist = struct.unpack('f', human_dist)[0]
            else:
                human_dist = float(human_dist)

            latent_dist = float(row['latent_distance'])
            delta = float(row['delta'])

            results.append({
                'concept_a': row['concept_a'],
                'concept_b': row['concept_b'],
                'human_distance': human_dist,
                'latent_distance': latent_dist,
                'delta': delta,
                'bridge_mechanism': row['bridge_mechanism']
            })
        return results

    def get_concept_neighbors(self, concept_name: str) -> Dict[str, List[Dict]]:
        """Get all neighbors of a concept, split by human and latent"""
        concept_id = self.get_concept_id(concept_name)
        if not concept_id:
            return {"human": [], "latent": []}

        cursor = self.conn.cursor()

        # Get all relationships for this concept
        cursor.execute("""
            SELECT
                c2.name as neighbor,
                r.human_distance,
                r.latent_distance,
                r.delta,
                r.bridge_mechanism
            FROM relationships r
            JOIN concepts c2 ON r.concept_b_id = c2.id
            WHERE r.concept_a_id = ?
            ORDER BY r.delta DESC
        """, (concept_id,))

        relationships = [dict(row) for row in cursor.fetchall()]
        return {
            "concept": concept_name,
            "relationships": relationships
        }

    def update_coordinates(self, concept_name: str, x: float, y: float, z: float):
        """Update 3D coordinates for a concept (for UMAP projection)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE concepts
            SET coordinates_x = ?, coordinates_y = ?, coordinates_z = ?, updated_at = CURRENT_TIMESTAMP
            WHERE name = ?
        """, (x, y, z, concept_name))
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
