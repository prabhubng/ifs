# Project Structure

```
intelligent-file-search/
│
├── main.py                     # Main application file (GUI + Logic)
├── requirements.txt            # Python dependencies
├── setup.py                   # Package installation config
├── config.json                # User configuration file
│
├── README.md                  # Comprehensive documentation
├── INSTALL.md                 # Platform-specific installation
├── QUICKSTART.md              # Quick start guide
├── LICENSE                    # MIT License
│
├── build.sh                   # Linux/macOS build script
├── build.bat                  # Windows build script
├── FileSearch.spec            # PyInstaller configuration
├── installer.iss              # Windows Inno Setup config
├── file-search.desktop        # Linux desktop entry
│
├── test_install.py            # Installation verification
├── .gitignore                 # Git ignore rules
│
└── file_index.db              # SQLite database (created at runtime)
```

## File Descriptions

### Core Application
- **main.py** (500+ lines)
  - `FileIndexer` class: Database operations, indexing, search
  - `FileIndexApp` class: Tkinter GUI interface
  - Search algorithms: semantic, fuzzy, exact
  - Embedding generation using sentence-transformers

### Configuration
- **config.json**
  - Database settings
  - Indexing preferences
  - Search defaults
  - UI customization
  - Model configuration

### Documentation
- **README.md**: Complete user and developer guide
- **INSTALL.md**: Step-by-step installation for each OS
- **QUICKSTART.md**: 5-minute getting started guide

### Build System
- **build.sh**: Automated build for Linux/macOS
  - Creates executable
  - Builds AppImage
  - Builds DMG
- **build.bat**: Automated build for Windows
  - Creates executable
  - Builds installer
- **FileSearch.spec**: PyInstaller configuration
  - Dependency bundling
  - Icon integration
  - Platform-specific settings

### Installation
- **setup.py**: Python package configuration
  - Dependencies
  - Entry points
  - Package metadata
- **requirements.txt**: Python package list
  - sentence-transformers
  - numpy
  - torch
  - transformers

### Platform Integration
- **installer.iss**: Windows installer configuration (Inno Setup)
- **file-search.desktop**: Linux desktop entry
- **LICENSE**: MIT License

### Testing
- **test_install.py**: Comprehensive installation tests
  - Import checks
  - Database verification
  - GUI availability
  - Embedding model test

## Key Components

### Database Schema

```sql
-- Files table
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
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
);

-- Embeddings table
CREATE TABLE embeddings (
    file_id INTEGER PRIMARY KEY,
    embedding BLOB,
    FOREIGN KEY (file_id) REFERENCES files(id)
);
```

### Search Algorithms

1. **Semantic Search**
   - Uses all-MiniLM-L6-v2 model
   - Cosine similarity matching
   - Best for natural language queries

2. **Fuzzy Search**
   - Term-based scoring
   - Partial matching
   - Fastest for large datasets

3. **Exact Search**
   - SQL LIKE queries
   - Case-insensitive
   - Good for specific filenames

## Dependencies

### Required
- Python 3.8+
- tkinter (GUI)
- sqlite3 (Database)
- hashlib (File hashing)
- threading (Background operations)

### Optional
- sentence-transformers (Semantic search)
- torch (ML backend)
- numpy (Vector operations)

## Build Process

### Windows
```
1. Install PyInstaller
2. Run build.bat
3. Choose option 2 or 3
4. Output: dist/FileSearch.exe
5. Optional: Create installer with Inno Setup
```

### macOS
```
1. Install PyInstaller
2. Run build.sh
3. Choose option 4
4. Output: dist/FileSearch.app
5. Optional: Create DMG with create-dmg
```

### Linux
```
1. Install PyInstaller
2. Run build.sh
3. Choose option 5
4. Output: dist/file-search
5. Optional: Create AppImage
```

## Development

### Adding Features

**New search algorithm:**
```python
def _new_search(self, cursor, query: str, limit: int):
    # Implement search logic
    return results
```

**New file type:**
```python
type_map = {
    '.new': 'NewType',
    # Add to get_file_type() method
}
```

**GUI customization:**
```python
# In setup_ui() method
# Add new widgets, frames, or controls
```

### Testing

```bash
# Run installation test
python test_install.py

# Test indexing
python -c "from main import FileIndexer; print(FileIndexer().index_directory('test_dir'))"

# Test search
python -c "from main import FileIndexer; print(FileIndexer().search_files('test'))"
```

## Database Maintenance

### Backup
```python
import shutil
shutil.copy('file_index.db', 'file_index_backup.db')
```

### Reset
```bash
rm file_index.db
# Restart application to create fresh database
```

### Optimize
```python
import sqlite3
conn = sqlite3.connect('file_index.db')
conn.execute('VACUUM')
conn.close()
```

## Performance Optimization

### Indexing
- Batch inserts (default: 1000)
- Thread pool for parallel processing
- Skip large files (>10MB for embeddings)
- Exclude system directories

### Search
- Database indexes on key columns
- Result limit (default: 50)
- Embedding caching
- Query preprocessing

### Memory
- Lazy loading of embeddings
- Stream processing for large directories
- Database connection pooling
- Garbage collection hints

## Security Considerations

### File Access
- Read-only operations by default
- No file modification
- User confirmation for opening files
- Path validation

### Database
- Local storage only
- No network access
- SQLite injection prevention
- Parameterized queries

### Privacy
- All data stored locally
- No telemetry
- No cloud sync
- User controls all data

## Future Enhancements

### Planned Features
- [ ] Duplicate file finder
- [ ] Advanced filters (date, size ranges)
- [ ] File preview pane
- [ ] Tag support
- [ ] Multi-directory indexing
- [ ] Export search results
- [ ] Cloud storage integration
- [ ] Scheduled re-indexing
- [ ] Dark mode UI
- [ ] Plugin system

### Under Consideration
- [ ] OCR for images
- [ ] Audio transcription
- [ ] Video thumbnail generation
- [ ] Network drive support
- [ ] Collaborative tagging
- [ ] Integration with file managers

## Contributing

1. Fork repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## Support

- GitHub Issues
- Documentation
- Community forums

---

**Last Updated**: December 21, 2024
**Version**: 1.0.0
**License**: MIT
