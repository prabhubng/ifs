"""
Intelligent File System Indexer and Search
A cross-platform desktop application for indexing and searching files using natural language
"""

import os
import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import hashlib
from typing import List, Dict, Optional, Tuple
import numpy as np
import re

# For text embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    print(f"Error: {e}")
    EMBEDDINGS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Semantic search disabled.")


class FileIndexer:
    """Handles file system indexing and metadata storage"""
    
    def __init__(self, db_path: str = "file_index.db"):
        self.db_path = db_path
        self.init_database()
        
        # Initialize lightweight embedding model
        if EMBEDDINGS_AVAILABLE:
            # Using all-MiniLM-L6-v2: lightweight and fast (22MB)
            self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        else:
            self.model = None
    
    def init_database(self):
        """Initialize SQLite database with file metadata schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create files table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT,
                file_extension TEXT,
                file_size INTEGER,
                created_time REAL,
                modified_time REAL,
                accessed_time REAL,
                parent_directory TEXT,
                depth INTEGER,
                is_hidden BOOLEAN,
                indexed_time REAL,
                file_hash TEXT
            )
        ''')
        
        # Create embeddings table for semantic search
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                file_id INTEGER PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        ''')
        
        # Create index for faster searches
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON files(file_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON files(file_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_extension ON files(file_extension)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_parent_directory ON files(parent_directory)')
        
        conn.commit()
        conn.close()
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of file for duplicate detection"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
    
    def should_ignore_path(self, path: str, is_directory: bool = False) -> bool:
        """
        Check if a path should be ignored during indexing.
        Returns True if the path should be skipped.
        """
        path_parts = [p.lower() for p in Path(path).parts]
        
        # Common directory names to ignore (case-insensitive)
        ignore_dirs = {
            # Python virtual environments
            'venv', '.venv', 'env', '.env', 'virtualenv', '.virtualenv',
            'env.bak', 'venv.bak',
            # Node.js
            'node_modules', '.npm', '.yarn', '.yarn-cache',
            # Python cache and build
            '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
            '.tox', '.coverage', 'htmlcov', '.hypothesis', '.cache',
            # Build artifacts
            'build', 'dist', '.eggs',
            # IDE and editor
            '.idea', '.vscode', '.vs', '.sublime-project', '.sublime-workspace',
            # Version control
            '.git', '.svn', '.hg', '.bzr',
            # Package managers
            '.pip', '.conda',
            # Other common development files
            '.next', '.nuxt', '.output', '.temp', '.tmp',
            'coverage', '.nyc_output', '.parcel-cache',
            # Logs
            'logs',
        }
        
        # Check if any part of the path matches ignore patterns
        for part in path_parts:
            # Skip current and parent directory markers
            if part in ['.', '..']:
                continue
            
            # Check exact matches with ignore directories
            if part in ignore_dirs:
                return True
            
            # Check for egg-info directories (pattern: *.egg-info)
            if part.endswith('.egg-info'):
                return True
            
            # Check for common hidden directories (but allow some important ones)
            if part.startswith('.') and is_directory:
                # Allow some important hidden files/dirs
                if part in ['.gitignore', '.gitattributes', '.editorconfig', '.pre-commit-config.yaml']:
                    continue
                # Skip most other hidden directories
                if len(part) > 1:  # Not just '.'
                    return True
        
        # Check for specific file patterns
        if not is_directory:
            filename = os.path.basename(path)
            filename_lower = filename.lower()
            
            # Ignore common system and cache files
            system_files = {
                '.ds_store', 'thumbs.db', 'desktop.ini', '.directory',
                '.localized', '.trash', '.trashes',
            }
            
            if filename_lower in system_files:
                return True
            
            # Ignore compiled Python files
            if filename_lower.endswith(('.pyc', '.pyo', '.pyd')):
                return True
            
            # Ignore common backup and temp files
            if filename_lower.endswith(('.bak', '.tmp', '.temp', '.swp', '.swo', '~')):
                return True
            
            # Ignore package lock files (can be very large)
            if filename_lower in ['package-lock.json', 'yarn.lock', 'poetry.lock', 'pipfile.lock']:
                return True
            
            # Ignore compiled binaries in common locations
            if filename_lower.endswith(('.so', '.dylib', '.dll', '.exe')) and \
               any(part in path_parts for part in ['node_modules', 'venv', '.venv', 'env', '.env']):
                return True
        
        # Check for virtual environment by looking for pyvenv.cfg in parent directories
        if is_directory:
            # Check if this directory or any parent contains venv markers
            current_path = Path(path)
            for parent in [current_path] + list(current_path.parents):
                if parent.name.lower() in ['venv', '.venv', 'env', '.env', 'virtualenv']:
                    # Check for venv marker files
                    venv_markers = ['pyvenv.cfg', 'activate', 'activate.bat', 'activate.ps1']
                    for marker in venv_markers:
                        marker_path = parent / marker
                        if marker_path.exists():
                            return True
        
        return False
    
    def index_directory(self, root_path: str, progress_callback=None, clear_old: bool = True) -> Dict[str, int]:
        """
        Recursively index all files in a directory.
        
        Args:
            root_path: Directory path to index
            progress_callback: Optional callback function for progress updates
            clear_old: If True, clear all old indexed data before indexing (default: True)
        """
        stats = {
            'total': 0,
            'indexed': 0,
            'skipped': 0,
            'errors': 0
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        root_path = os.path.abspath(root_path)
        
        # Clear old indexing data if requested
        if clear_old:
            if progress_callback:
                progress_callback({'status': 'Clearing old index...', **stats})
            
            # Delete all files and their embeddings
            cursor.execute('DELETE FROM embeddings')
            cursor.execute('DELETE FROM files')
            conn.commit()
            
            if progress_callback:
                progress_callback({'status': 'Starting indexing...', **stats})
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Filter out directories to ignore
            filtered_dirs = []
            for d in dirnames:
                dir_path = os.path.join(dirpath, d)
                # Skip if should be ignored
                if self.should_ignore_path(dir_path, is_directory=True):
                    stats['skipped'] += 1
                    continue
                # Skip hidden directories (unless they're explicitly allowed)
                if d.startswith('.') and d not in ['.gitignore', '.gitattributes', '.editorconfig', '.pre-commit-config.yaml']:
                    stats['skipped'] += 1
                    continue
                filtered_dirs.append(d)
            
            # Update dirnames in-place to prevent os.walk from traversing ignored directories
            dirnames[:] = filtered_dirs
            
            for filename in filenames:
                stats['total'] += 1
                file_path = os.path.join(dirpath, filename)
                
                # Skip files that should be ignored
                if self.should_ignore_path(file_path, is_directory=False):
                    stats['skipped'] += 1
                    continue
                
                try:
                    # Get file metadata
                    stat_info = os.stat(file_path)
                    
                    file_data = {
                        'file_path': file_path,
                        'file_name': filename,
                        'file_type': self.get_file_type(filename),
                        'file_extension': os.path.splitext(filename)[1].lower(),
                        'file_size': stat_info.st_size,
                        'created_time': stat_info.st_ctime,
                        'modified_time': stat_info.st_mtime,
                        'accessed_time': stat_info.st_atime,
                        'parent_directory': dirpath,
                        'depth': len(Path(file_path).relative_to(root_path).parts),
                        'is_hidden': filename.startswith('.'),
                        'indexed_time': datetime.now().timestamp(),
                        'file_hash': self.calculate_file_hash(file_path) if stat_info.st_size < 10*1024*1024 else None
                    }
                    
                    # Insert or update file record
                    cursor.execute('''
                        INSERT OR REPLACE INTO files 
                        (file_path, file_name, file_type, file_extension, file_size, 
                         created_time, modified_time, accessed_time, parent_directory, 
                         depth, is_hidden, indexed_time, file_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', tuple(file_data.values()))
                    
                    file_id = cursor.lastrowid
                    
                    # Generate and store embedding for semantic search
                    if self.model and stat_info.st_size < 1024*1024:  # Only for files < 1MB
                        self.generate_embedding(cursor, file_id, file_data)
                    
                    stats['indexed'] += 1
                    
                    if progress_callback and stats['total'] % 10 == 0:
                        progress_callback(stats)
                    
                except Exception as e:
                    stats['errors'] += 1
                    print(f"Error indexing {file_path}: {e}")
        
        conn.commit()
        conn.close()
        
        return stats
    
    def generate_embedding(self, cursor, file_id: int, file_data: Dict):
        """Generate text embedding for semantic search"""
        try:
            # Create searchable text from metadata
            search_text = f"{file_data['file_name']} {file_data['file_type']} {file_data['parent_directory']}"
            
            # Generate embedding
            embedding = self.model.encode(search_text)
            embedding_bytes = embedding.tobytes()
            
            # Store embedding
            cursor.execute('''
                INSERT OR REPLACE INTO embeddings (file_id, embedding)
                VALUES (?, ?)
            ''', (file_id, embedding_bytes))
        except Exception as e:
            print(f"Error generating embedding for file {file_id}: {e}")
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = os.path.splitext(filename)[1].lower()
        
        type_map = {
            '.txt': 'Text',
            '.doc': 'Document', '.docx': 'Document', '.pdf': 'Document', '.odt': 'Document',
            '.xls': 'Spreadsheet', '.xlsx': 'Spreadsheet', '.csv': 'Spreadsheet',
            '.ppt': 'Presentation', '.pptx': 'Presentation',
            '.jpg': 'Image', '.jpeg': 'Image', '.png': 'Image', '.gif': 'Image', '.bmp': 'Image', '.svg': 'Image',
            '.mp4': 'Video', '.avi': 'Video', '.mov': 'Video', '.mkv': 'Video',
            '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.m4a': 'Audio',
            '.zip': 'Archive', '.rar': 'Archive', '.7z': 'Archive', '.tar': 'Archive', '.gz': 'Archive',
            '.py': 'Code', '.js': 'Code', '.java': 'Code', '.cpp': 'Code', '.c': 'Code', 
            '.html': 'Code', '.css': 'Code', '.json': 'Code', '.xml': 'Code', '.sql': 'Code',
            '.exe': 'Executable', '.app': 'Executable', '.dmg': 'Executable',
        }
        
        return type_map.get(ext, 'Other')
    
    def parse_time_constraint(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Parse time constraints from query.
        Returns (time_field, cutoff_timestamp) or None.
        time_field can be 'created_time', 'modified_time', or 'accessed_time'
        """
        query_lower = query.lower()
        current_time = datetime.now().timestamp()
        
        # Patterns for time expressions
        # Match: "last X hours/days/weeks/months" or "in the last X hours/days/weeks/months"
        time_pattern = r'(?:in\s+the\s+)?last\s+(\d+)\s+(hour|hours|day|days|week|weeks|month|months)'
        match = re.search(time_pattern, query_lower)
        
        if match:
            value = int(match.group(1))
            unit = match.group(2).rstrip('s')  # Remove plural
            
            # Convert to seconds
            if unit == 'hour':
                delta_seconds = value * 3600
            elif unit == 'day':
                delta_seconds = value * 86400
            elif unit == 'week':
                delta_seconds = value * 604800
            elif unit == 'month':
                delta_seconds = value * 2592000  # Approximate 30 days
            else:
                return None
            
            cutoff_time = current_time - delta_seconds
            
            # Determine which time field to use
            if 'created' in query_lower or 'creation' in query_lower:
                return ('created_time', cutoff_time)
            elif 'modified' in query_lower or 'modification' in query_lower or 'changed' in query_lower:
                return ('modified_time', cutoff_time)
            elif 'accessed' in query_lower or 'access' in query_lower:
                return ('accessed_time', cutoff_time)
            else:
                # Default to modified_time if not specified
                return ('modified_time', cutoff_time)
        
        return None
    
    def parse_size_constraint(self, query: str) -> Optional[Tuple[str, int]]:
        """
        Parse size constraints from query.
        Returns (operator, size_in_bytes) or None.
        operator can be '<', '>', '<=', '>=', '='
        """
        query_lower = query.lower()
        
        # Patterns for size expressions
        # Match: "less than/equal to/greater than X kb/mb/gb/tb"
        size_patterns = [
            (r'smaller\s+than\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '<'),
            (r'less\s+than\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '<'),
            (r'larger\s+than\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '>'),
            (r'greater\s+than\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '>'),
            (r'bigger\s+than\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '>'),
            (r'equal\s+to\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '='),
            (r'(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)\s+or\s+less', '<='),
            (r'(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)\s+or\s+more', '>='),
            (r'(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)\s+or\s+smaller', '<='),
            (r'(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)\s+or\s+larger', '>='),
            (r'(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)\s+or\s+bigger', '>='),
            # Simpler patterns with operators (with or without spaces)
            (r'<\s*(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '<'),
            (r'>\s*(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '>'),
            (r'<=\s*(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '<='),
            (r'>=\s*(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '>='),
            (r'=\s*(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', '='),
            # Handle "files less than 2 kb" pattern
            (r'files?\s+(less|smaller|greater|larger|bigger)\s+than\s+(\d+(?:\.\d+)?)\s*(kb|mb|gb|tb)', None),
        ]
        
        for pattern, operator in size_patterns:
            match = re.search(pattern, query_lower)
            if match:
                # Handle the last pattern which has different groups
                if operator is None:
                    op_word = match.group(1)
                    value = float(match.group(2))
                    unit = match.group(3).lower()
                    if op_word in ['less', 'smaller']:
                        operator = '<'
                    elif op_word in ['greater', 'larger', 'bigger']:
                        operator = '>'
                    else:
                        continue
                else:
                    value = float(match.group(1))
                    unit = match.group(2).lower()
                
                # Convert to bytes
                multipliers = {
                    'kb': 1024,
                    'mb': 1024 * 1024,
                    'gb': 1024 * 1024 * 1024,
                    'tb': 1024 * 1024 * 1024 * 1024
                }
                
                size_bytes = int(value * multipliers.get(unit, 1))
                return (operator, size_bytes)
        
        return None
    
    def search_files(self, query: str, search_type: str = 'semantic', limit: int = 50) -> List[Dict]:
        """Search files using different methods"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results = []
        
        # Check if query contains time or size constraints
        time_constraint = self.parse_time_constraint(query)
        size_constraint = self.parse_size_constraint(query)
        
        # Route to appropriate search method
        if search_type == 'semantic' and self.model:
            # Semantic search handles time/size constraints internally
            results = self._semantic_search(cursor, query, limit)
        elif search_type == 'fuzzy':
            # Fuzzy search now handles time/size constraints internally
            results = self._fuzzy_search(cursor, query, limit)
        elif search_type == 'exact':
            # Exact search - if there are constraints, use metadata search
            if time_constraint or size_constraint:
                results = self._metadata_search(cursor, query, time_constraint, size_constraint, limit)
            else:
                results = self._exact_search(cursor, query, limit)
        else:
            # Default to fuzzy search (handles constraints)
            results = self._fuzzy_search(cursor, query, limit)
        
        conn.close()
        return results
    
    def _metadata_search(self, cursor, query: str, time_constraint: Optional[Tuple], 
                        size_constraint: Optional[Tuple], limit: int) -> List[Dict]:
        """Search files based on metadata constraints only"""
        where_clauses = []
        params = []
        
        # Apply time constraint
        if time_constraint:
            time_field, cutoff_time = time_constraint
            where_clauses.append(f"{time_field} >= ?")
            params.append(cutoff_time)
        
        # Apply size constraint
        if size_constraint:
            operator, size_bytes = size_constraint
            where_clauses.append(f"file_size {operator} ?")
            params.append(size_bytes)
        
        # Also search in file names if query has other text
        query_clean = query.lower()
        # Remove time/size patterns from query for text search
        query_clean = re.sub(r'(?:in\s+the\s+)?last\s+\d+\s+(hour|hours|day|days|week|weeks|month|months)', '', query_clean)
        query_clean = re.sub(r'(less|greater|equal|smaller|larger|bigger)\s+than\s+\d+(?:\.\d+)?\s*(kb|mb|gb|tb)', '', query_clean)
        query_clean = re.sub(r'\d+(?:\.\d+)?\s*(kb|mb|gb|tb).*', '', query_clean)
        query_clean = re.sub(r'files?\s+', '', query_clean)  # Remove "file" or "files" prefix
        query_clean = re.sub(r'\s+', ' ', query_clean)  # Normalize whitespace
        query_clean = query_clean.strip()
        
        if query_clean:
            where_clauses.append("(file_name LIKE ? OR file_path LIKE ?)")
            search_pattern = f'%{query_clean}%'
            params.extend([search_pattern, search_pattern])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor.execute(f'''
            SELECT * FROM files 
            WHERE {where_sql}
            ORDER BY modified_time DESC
            LIMIT ?
        ''', params + [limit])
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _semantic_search(self, cursor, query: str, limit: int) -> List[Dict]:
        """Semantic search using embeddings with support for time and size filters"""
        # Parse time and size constraints
        time_constraint = self.parse_time_constraint(query)
        size_constraint = self.parse_size_constraint(query)
        
        # Build SQL query with filters
        where_clauses = []
        params = []
        
        # Apply time constraint
        if time_constraint:
            time_field, cutoff_time = time_constraint
            where_clauses.append(f"{time_field} >= ?")
            params.append(cutoff_time)
        
        # Apply size constraint
        if size_constraint:
            operator, size_bytes = size_constraint
            where_clauses.append(f"file_size {operator} ?")
            params.append(size_bytes)
        
        # If we have only time/size constraints without semantic search needed
        if (time_constraint or size_constraint) and not self.model:
            # Pure metadata search
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            cursor.execute(f'''
                SELECT * FROM files 
                WHERE {where_sql}
                ORDER BY modified_time DESC
                LIMIT ?
            ''', params + [limit])
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        
        # If we have only time/size constraints, we can optimize by filtering first
        if time_constraint or size_constraint:
            # First, get filtered file IDs
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            cursor.execute(f'''
                SELECT id FROM files WHERE {where_sql}
            ''', params)
            
            filtered_ids = [row[0] for row in cursor.fetchall()]
            
            if not filtered_ids:
                return []
            
            # Only search embeddings for filtered files
            placeholders = ','.join('?' * len(filtered_ids))
            cursor.execute(f'''
                SELECT file_id, embedding FROM embeddings 
                WHERE file_id IN ({placeholders})
            ''', filtered_ids)
            
            rows = cursor.fetchall()
        else:
            # Get all embeddings (original behavior)
            cursor.execute('SELECT file_id, embedding FROM embeddings')
            rows = cursor.fetchall()
        
        if not rows:
            return []
        
        # Perform semantic search
        query_embedding = self.model.encode(query)
        
        similarities = []
        for file_id, embedding_bytes in rows:
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )
            similarities.append((file_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_ids = [file_id for file_id, _ in similarities[:limit]]
        
        if not top_ids:
            return []
        
        # Get file details
        placeholders = ','.join('?' * len(top_ids))
        cursor.execute(f'''
            SELECT * FROM files WHERE id IN ({placeholders})
        ''', top_ids)
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            result['similarity'] = next(s for fid, s in similarities if fid == result['id'])
            results.append(result)
        
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
    
    def _exact_search(self, cursor, query: str, limit: int) -> List[Dict]:
        """Exact match search"""
        cursor.execute('''
            SELECT * FROM files 
            WHERE file_name LIKE ? OR file_path LIKE ?
            ORDER BY modified_time DESC
            LIMIT ?
        ''', (f'%{query}%', f'%{query}%', limit))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _fuzzy_search(self, cursor, query: str, limit: int) -> List[Dict]:
        """Fuzzy search with ranking and support for time/size constraints"""
        # Parse time and size constraints
        time_constraint = self.parse_time_constraint(query)
        size_constraint = self.parse_size_constraint(query)
        
        # Build SQL query with filters
        where_clauses = []
        params = []
        
        # Apply time constraint
        if time_constraint:
            time_field, cutoff_time = time_constraint
            where_clauses.append(f"{time_field} >= ?")
            params.append(cutoff_time)
        
        # Apply size constraint
        if size_constraint:
            operator, size_bytes = size_constraint
            where_clauses.append(f"file_size {operator} ?")
            params.append(size_bytes)
        
        # Clean query for text search (remove time/size patterns)
        query_clean = query.lower()
        if time_constraint:
            query_clean = re.sub(r'(?:in\s+the\s+)?last\s+\d+\s+(hour|hours|day|days|week|weeks|month|months)', '', query_clean)
        if size_constraint:
            # Remove size patterns with operators
            query_clean = re.sub(r'(less|greater|equal|smaller|larger|bigger)\s+than\s+\d+(?:\.\d+)?\s*(kb|mb|gb|tb)', '', query_clean)
            query_clean = re.sub(r'[<>=]+\s*\d+(?:\.\d+)?\s*(kb|mb|gb|tb)', '', query_clean)
            query_clean = re.sub(r'\d+(?:\.\d+)?\s*(kb|mb|gb|tb)(?:\s+or\s+(less|more|smaller|larger|bigger))?', '', query_clean)
        query_clean = re.sub(r'files?\s+', '', query_clean)
        query_clean = re.sub(r'\s+', ' ', query_clean).strip()
        
        # Get files with optional filters
        if where_clauses:
            where_sql = " AND ".join(where_clauses)
            cursor.execute(f'SELECT * FROM files WHERE {where_sql}', params)
        else:
            cursor.execute('SELECT * FROM files')
        
        columns = [desc[0] for desc in cursor.description]
        all_files = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # If no text query remains after cleaning, return filtered results
        if not query_clean:
            # Sort by modified_time if no text search
            all_files.sort(key=lambda x: x['modified_time'], reverse=True)
            return all_files[:limit]
        
        # Score each file based on text matching
        query_terms = query_clean.split()
        scored_files = []
        for file in all_files:
            score = 0
            searchable = f"{file['file_name']} {file['parent_directory']}".lower()
            
            for term in query_terms:
                if term in searchable:
                    score += searchable.count(term)
            
            if score > 0:
                file['score'] = score
                scored_files.append(file)
        
        scored_files.sort(key=lambda x: x['score'], reverse=True)
        return scored_files[:limit]
    
    def get_stats(self) -> Dict:
        """Get indexing statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM files')
        total_files = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(file_size) FROM files')
        total_size = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(DISTINCT file_type) FROM files')
        file_types = cursor.fetchone()[0]
        
        cursor.execute('SELECT file_type, COUNT(*) as count FROM files GROUP BY file_type ORDER BY count DESC')
        type_distribution = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'file_types': file_types,
            'type_distribution': type_distribution
        }


class FileIndexApp:
    """Main GUI application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Intelligent File System Search")
        self.root.geometry("1200x700")
        
        # Initialize indexer
        self.indexer = FileIndexer()
        self.indexing_thread = None
        
        self.setup_ui()
        self.update_stats()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header section
        header_frame = ttk.LabelFrame(main_frame, text="Indexing", padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        header_frame.columnconfigure(1, weight=1)
        
        ttk.Label(header_frame, text="Directory:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.dir_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self.dir_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(header_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(header_frame, text="Index", command=self.start_indexing).grid(row=0, column=3)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(header_frame, textvariable=self.progress_var).grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # Search section
        search_frame = ttk.LabelFrame(main_frame, text="Search", padding="10")
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Query:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.query_var = tk.StringVar()
        query_entry = ttk.Entry(search_frame, textvariable=self.query_var)
        query_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        query_entry.bind('<Return>', lambda e: self.search_files())
        
        self.search_type_var = tk.StringVar(value='fuzzy')
        ttk.Radiobutton(search_frame, text="Fuzzy", variable=self.search_type_var, value='fuzzy').grid(row=0, column=2, padx=2)
        ttk.Radiobutton(search_frame, text="Exact", variable=self.search_type_var, value='exact').grid(row=0, column=3, padx=2)
        
        if EMBEDDINGS_AVAILABLE:
            ttk.Radiobutton(search_frame, text="Semantic", variable=self.search_type_var, value='semantic').grid(row=0, column=4, padx=2)
        
        ttk.Button(search_frame, text="Search", command=self.search_files).grid(row=0, column=5, padx=(5, 0))
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview for results
        columns = ('name', 'type', 'size', 'modified', 'path')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('name', text='File Name')
        self.tree.heading('type', text='Type')
        self.tree.heading('size', text='Size')
        self.tree.heading('modified', text='Modified')
        self.tree.heading('path', text='Path')
        
        self.tree.column('name', width=200)
        self.tree.column('type', width=100)
        self.tree.column('size', width=100)
        self.tree.column('modified', width=150)
        self.tree.column('path', width=400)
        
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind double-click to open file
        self.tree.bind('<Double-1>', self.open_file)
        
        # Stats section
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_var = tk.StringVar(value="No files indexed")
        ttk.Label(stats_frame, textvariable=self.stats_var).grid(row=0, column=0, sticky=tk.W)
    
    def browse_directory(self):
        """Open directory browser"""
        directory = filedialog.askdirectory(title="Select Directory to Index")
        if directory:
            self.dir_var.set(directory)
    
    def start_indexing(self):
        """Start indexing in background thread"""
        directory = self.dir_var.get()
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Error", "Please select a valid directory")
            return
        
        if self.indexing_thread and self.indexing_thread.is_alive():
            messagebox.showwarning("Warning", "Indexing already in progress")
            return
        
        self.progress_var.set("Indexing...")
        self.indexing_thread = threading.Thread(target=self.index_directory, args=(directory,), daemon=True)
        self.indexing_thread.start()
    
    def index_directory(self, directory):
        """Index directory with progress updates"""
        def progress_callback(stats):
            if 'status' in stats:
                # Show status message (e.g., "Clearing old index...")
                self.root.after(0, lambda: self.progress_var.set(stats['status']))
            else:
                # Show progress with counts
                self.root.after(0, lambda: self.progress_var.set(
                    f"Indexing... {stats['indexed']}/{stats['total']} files ({stats['errors']} errors)"
                ))
        
        try:
            stats = self.indexer.index_directory(directory, progress_callback)
            self.root.after(0, lambda: self.on_indexing_complete(stats))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Indexing failed: {e}"))
            self.root.after(0, lambda: self.progress_var.set("Ready"))
    
    def on_indexing_complete(self, stats):
        """Handle indexing completion"""
        self.progress_var.set(
            f"Indexed {stats['indexed']} files ({stats['errors']} errors, {stats['skipped']} skipped)"
        )
        self.update_stats()
        messagebox.showinfo("Success", f"Successfully indexed {stats['indexed']} files!")
    
    def search_files(self):
        """Perform file search"""
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return
        
        search_type = self.search_type_var.get()
        
        try:
            results = self.indexer.search_files(query, search_type)
            self.display_results(results)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")
    
    def display_results(self, results):
        """Display search results in treeview"""
        # Clear existing results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new results
        for result in results:
            size_str = self.format_size(result['file_size'])
            modified_str = datetime.fromtimestamp(result['modified_time']).strftime('%Y-%m-%d %H:%M')
            
            self.tree.insert('', tk.END, values=(
                result['file_name'],
                result['file_type'],
                size_str,
                modified_str,
                result['file_path']
            ), tags=(result['file_path'],))
        
        self.progress_var.set(f"Found {len(results)} results")
    
    def format_size(self, size):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def open_file(self, event):
        """Open selected file"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            file_path = item['tags'][0]
            
            try:
                if os.path.exists(file_path):
                    import platform
                    if platform.system() == 'Darwin':       # macOS
                        os.system(f'open "{file_path}"')
                    elif platform.system() == 'Windows':    # Windows
                        os.startfile(file_path)
                    else:                                   # Linux
                        os.system(f'xdg-open "{file_path}"')
                else:
                    messagebox.showerror("Error", "File not found")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")
    
    def update_stats(self):
        """Update statistics display"""
        stats = self.indexer.get_stats()
        
        size_str = self.format_size(stats['total_size'])
        stats_text = f"Total Files: {stats['total_files']} | Total Size: {size_str} | File Types: {stats['file_types']}"
        
        if stats['type_distribution']:
            top_types = ', '.join([f"{t[0]}: {t[1]}" for t in stats['type_distribution'][:5]])
            stats_text += f" | Top Types: {top_types}"
        
        self.stats_var.set(stats_text)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FileIndexApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
