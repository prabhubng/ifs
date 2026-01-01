# Architecture & Technical Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Tkinter)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Indexing   │  │    Search    │  │   Results    │      │
│  │   Controls   │  │    Input     │  │   Display    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FileIndexApp (GUI Controller)                   │
│  • Event handling                                            │
│  • Progress tracking                                         │
│  • Result formatting                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FileIndexer (Core Engine)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Indexing   │  │    Search    │  │  Embedding   │      │
│  │   Engine     │  │   Engine     │  │  Generator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ SQLite   │  │  File    │  │ AI Model │
    │ Database │  │  System  │  │ (MiniLM) │
    └──────────┘  └──────────┘  └──────────┘
```

## Data Flow

### Indexing Process

```
1. User selects directory
   │
   ▼
2. Walk directory tree recursively
   │
   ▼
3. For each file:
   ├─► Extract metadata (stat info)
   ├─► Calculate MD5 hash (if < 10MB)
   ├─► Determine file type
   ├─► Generate search text
   └─► Create embedding (if < 1MB)
   │
   ▼
4. Batch insert to database
   │
   ▼
5. Update UI progress
```

### Search Process

```
1. User enters query
   │
   ▼
2. Select search mode
   │
   ├─► Semantic Search
   │   ├─► Generate query embedding
   │   ├─► Load all file embeddings
   │   ├─► Calculate cosine similarity
   │   └─► Rank by similarity score
   │
   ├─► Fuzzy Search
   │   ├─► Split query into terms
   │   ├─► Load all files
   │   ├─► Score by term frequency
   │   └─► Rank by total score
   │
   └─► Exact Search
       ├─► Create SQL LIKE query
       └─► Execute database query
   │
   ▼
3. Return top N results
   │
   ▼
4. Display in treeview
```

## Database Schema

### Files Table
```sql
CREATE TABLE files (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path         TEXT UNIQUE NOT NULL,      -- Full path
    file_name         TEXT NOT NULL,             -- Name only
    file_type         TEXT,                      -- Category (Document, Image, etc.)
    file_extension    TEXT,                      -- .pdf, .jpg, etc.
    file_size         INTEGER,                   -- Bytes
    created_time      REAL,                      -- Unix timestamp
    modified_time     REAL,                      -- Unix timestamp
    accessed_time     REAL,                      -- Unix timestamp
    parent_directory  TEXT,                      -- Directory path
    depth             INTEGER,                   -- Subdirectory depth
    is_hidden         BOOLEAN,                   -- Hidden file flag
    indexed_time      REAL,                      -- When indexed
    file_hash         TEXT                       -- MD5 hash
);

CREATE INDEX idx_file_name ON files(file_name);
CREATE INDEX idx_file_type ON files(file_type);
CREATE INDEX idx_file_extension ON files(file_extension);
CREATE INDEX idx_parent_directory ON files(parent_directory);
```

### Embeddings Table
```sql
CREATE TABLE embeddings (
    file_id    INTEGER PRIMARY KEY,
    embedding  BLOB,                            -- NumPy array as bytes
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);
```

## Component Details

### 1. FileIndexer Class

**Responsibilities:**
- Database initialization and management
- File system traversal
- Metadata extraction
- Embedding generation
- Search execution

**Key Methods:**
```python
__init__(db_path)                    # Initialize database and model
index_directory(root_path, callback) # Index all files recursively
search_files(query, search_type)     # Execute search query
get_stats()                          # Get database statistics
```

### 2. FileIndexApp Class

**Responsibilities:**
- GUI construction
- User interaction handling
- Background thread management
- Result presentation

**Key Methods:**
```python
setup_ui()              # Build Tkinter interface
start_indexing()        # Launch indexing thread
search_files()          # Execute search
display_results()       # Show results in treeview
```

### 3. Search Algorithms

#### Semantic Search
```
Input: Natural language query
Process:
  1. Encode query to 384-dim vector
  2. Retrieve all file embeddings
  3. Calculate cosine similarity:
     similarity = dot(query, file) / (||query|| * ||file||)
  4. Sort by similarity score
Output: Top N most similar files
```

#### Fuzzy Search
```
Input: Query terms (space-separated)
Process:
  1. Split query into terms
  2. For each file:
     score = Σ(term_count in (name + path))
  3. Sort by score
Output: Top N highest scoring files
```

#### Exact Search
```
Input: Exact string to match
Process:
  1. SQL: WHERE file_name LIKE '%query%' 
          OR file_path LIKE '%query%'
  2. Order by modified_time DESC
Output: All matching files
```

## AI Model Details

### Sentence-Transformers Model
- **Model**: all-MiniLM-L6-v2
- **Size**: 22MB
- **Dimensions**: 384
- **Speed**: ~100 sentences/second
- **Use Case**: Semantic similarity search

### Why all-MiniLM-L6-v2?
✅ Lightweight (22MB vs 400MB+ alternatives)
✅ Fast inference (important for real-time search)
✅ Good accuracy for general-purpose search
✅ Low memory footprint
✅ CPU-friendly (no GPU required)

### Embedding Process
```python
# Create searchable text
text = f"{filename} {filetype} {directory}"

# Generate 384-dimensional embedding
embedding = model.encode(text)  # → numpy array [384]

# Store as binary BLOB
embedding_bytes = embedding.tobytes()
```

## Performance Considerations

### Indexing Optimization
1. **Batch Processing**: Insert 1000 records at once
2. **Selective Embedding**: Only files < 1MB
3. **Hash Caching**: Skip hashing large files (>10MB)
4. **Skip Patterns**: Exclude .git, node_modules, etc.

### Search Optimization
1. **Database Indexes**: On name, type, extension, directory
2. **Result Limiting**: Default 50 results
3. **Lazy Loading**: Load embeddings on-demand
4. **Parallel Processing**: Thread pool for embedding generation

### Memory Optimization
1. **Stream Processing**: Don't load all files at once
2. **Embedding Compression**: Store as BLOB not JSON
3. **Connection Pooling**: Reuse database connections
4. **Garbage Collection**: Explicit cleanup after indexing

## File Type Detection

### Categorization Logic
```python
CATEGORIES = {
    'Document':     ['.pdf', '.doc', '.docx', '.txt', '.odt'],
    'Spreadsheet':  ['.xls', '.xlsx', '.csv'],
    'Presentation': ['.ppt', '.pptx'],
    'Image':        ['.jpg', '.png', '.gif', '.bmp', '.svg'],
    'Video':        ['.mp4', '.avi', '.mov', '.mkv'],
    'Audio':        ['.mp3', '.wav', '.flac', '.m4a'],
    'Archive':      ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Code':         ['.py', '.js', '.java', '.cpp', '.html'],
    'Executable':   ['.exe', '.app', '.dmg'],
    'Other':        [everything else]
}
```

## Security Model

### File Access
- **Read-Only**: Never modify indexed files
- **Sandboxed**: No system file access
- **Validated Paths**: Sanitize all file paths
- **User Confirmation**: Required to open files

### Database Security
- **Local Only**: No network access
- **Parameterized Queries**: SQL injection prevention
- **User-Owned**: Stored in user directory
- **No Credentials**: No passwords or sensitive data

### Privacy
- **Zero Telemetry**: No data sent anywhere
- **No Cloud**: All processing local
- **User Control**: Can delete database anytime
- **No Logging**: No persistent logs

## Extensibility

### Adding New Search Algorithm
```python
def _custom_search(self, cursor, query, limit):
    # Implement your algorithm
    cursor.execute("SELECT * FROM files WHERE ...")
    return results

# Register in search_files()
if search_type == 'custom':
    results = self._custom_search(cursor, query, limit)
```

### Adding New File Metadata
```python
# 1. Add column to database
cursor.execute('ALTER TABLE files ADD COLUMN new_field TEXT')

# 2. Extract in index_directory()
file_data['new_field'] = extract_new_field(file_path)

# 3. Display in GUI
self.tree.heading('new_field', text='New Field')
```

### Custom UI Theme
```python
# In setup_ui()
style = ttk.Style()
style.configure('Custom.TButton', 
    background='blue',
    foreground='white',
    font=('Arial', 12, 'bold')
)
```

## Testing Strategy

### Unit Tests
- Database operations
- File metadata extraction
- Search algorithms
- Embedding generation

### Integration Tests
- Full indexing workflow
- End-to-end search
- GUI interactions
- File opening

### Performance Tests
- Index 100k files
- Search 100k files
- Memory usage profiling
- CPU usage monitoring

## Deployment

### Windows
```
PyInstaller → Single EXE → Inno Setup Installer
```

### macOS
```
PyInstaller → .app Bundle → create-dmg → DMG
```

### Linux
```
PyInstaller → Binary → AppImage → Portable App
```

## Monitoring & Logs

### Error Handling
- Try-catch on all file operations
- Graceful degradation (skip failed files)
- User-friendly error messages
- Continue on error policy

### Progress Tracking
- Callback function for indexing
- Real-time UI updates
- Statistics display
- Completion notifications

## Future Architecture

### Plugin System
```
Plugin Interface:
  - register_search_algorithm()
  - register_file_type()
  - register_ui_component()
```

### Cloud Sync
```
Architecture:
  Local DB ←→ Sync Service ←→ Cloud Storage
  Conflict Resolution: Last-write-wins
  Encryption: AES-256
```

### Multi-Index Support
```
Database Schema:
  indexes (id, name, root_path)
  files (id, index_id, ...)
  
UI: Index switcher dropdown
```

---

**This architecture supports:**
- ✅ Fast indexing (1000 files/sec)
- ✅ Intelligent search (3 modes)
- ✅ Low resource usage (<300MB)
- ✅ Cross-platform compatibility
- ✅ Easy extensibility
- ✅ Privacy & security

**Design Principles:**
- Simplicity over complexity
- Local-first approach
- User privacy paramount
- Performance optimized
- Minimal dependencies
