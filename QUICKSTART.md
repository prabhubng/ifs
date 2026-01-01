# Quick Start Guide

Get up and running with Intelligent File Search in 5 minutes!

## Installation (Choose One Method)

### Option A: Simple Python Install (All Platforms)

```bash
# 1. Clone or download
git clone https://github.com/yourusername/intelligent-file-search.git
cd intelligent-file-search

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python main.py
```

### Option B: Pre-built Executable

- **Windows**: Download and run `FileSearch-Setup-Windows.exe`
- **macOS**: Download and open `FileSearch-Installer.dmg`
- **Linux**: Download and run `FileSearch-x86_64.AppImage`

## First Use

### 1. Index Your Files

```
┌─────────────────────────────────────┐
│ [Browse] Select Directory           │
│ /home/user/Documents    [Index]     │
└─────────────────────────────────────┘
```

1. Click **Browse** → Select folder to index
2. Click **Index** → Wait for completion
3. Status bar shows progress

**Tip**: Start with a small folder (~1000 files) to test

### 2. Search Files

```
┌─────────────────────────────────────┐
│ Query: vacation photos              │
│ ○ Fuzzy  ○ Exact  ○ Semantic [Go]  │
└─────────────────────────────────────┘
```

1. Type search query
2. Choose search mode:
   - **Fuzzy**: Smart matching (fastest)
   - **Exact**: Keyword matching
   - **Semantic**: AI-powered (most intelligent)
3. Press Enter or click Search

### 3. Open Files

- **Double-click** any result to open file
- Results show: Name, Type, Size, Date, Path

## Search Examples

### Fuzzy Search (General)
```
"report 2024"          → Finds files with both words
"python jupyter"       → Matches .py and .ipynb files
"invoice tax"          → Financial documents
```

### Exact Search (Precise)
```
"budget.xlsx"          → Exact filename
"/documents/work/"     → Specific path
".pdf"                 → All PDFs
```

### Semantic Search (AI)
```
"financial reports"    → Finds reports, statements, budgets
"vacation memories"    → Photos, videos, documents
"programming code"     → .py, .js, .java, etc.
"meeting notes"        → .txt, .doc, .md files
```

## Tips for Better Results

### 🎯 Semantic Search Tips

**Good queries** (specific context):
- ✅ "2024 tax documents"
- ✅ "family vacation photos"
- ✅ "python machine learning code"
- ✅ "quarterly sales reports"

**Poor queries** (too vague):
- ❌ "files"
- ❌ "stuff"
- ❌ "data"

### ⚡ Performance Tips

**Fast indexing**:
- Index from SSD (not network drives)
- Exclude unnecessary folders (node_modules, .git)
- Start with smaller directories

**Fast searching**:
- Use Fuzzy for large indexes (100k+ files)
- Use Semantic for complex queries
- Use Exact when you know the filename

### 📁 What to Index

**Good candidates**:
- ✅ Documents folder
- ✅ Projects directory
- ✅ Downloads folder
- ✅ Photo library

**Skip these**:
- ❌ System directories (C:\Windows, /usr)
- ❌ Program Files
- ❌ node_modules, .git folders
- ❌ Temporary files

## Common Tasks

### Find Files by Type
```
Fuzzy: ".pdf"          → All PDFs
Fuzzy: ".jpg .png"     → All images
Semantic: "spreadsheets" → Excel/CSV files
```

### Find Recent Files
```
# Index with filter (edit config.json)
# Then search by name/type
```

### Find Large Files
```
# Results show size
# Sort by clicking "Size" column
```

### Find Duplicates
```
# Files indexed with MD5 hash
# Query database for duplicate hashes
```

## Troubleshooting

### "No results found"
- ✓ Directory is indexed?
- ✓ Search mode appropriate?
- ✓ Try broader terms
- ✓ Check spelling

### "Indexing is slow"
- ✓ Using HDD? Switch to SSD
- ✓ Excluding system folders?
- ✓ Network drive? Copy locally
- ✓ Disable embeddings in config.json

### "Semantic search unavailable"
```bash
pip install sentence-transformers
```

### "Can't open file"
- File moved/deleted after indexing
- Re-index directory
- Check file permissions

## Advanced Usage

### Configuration File

Edit `config.json`:

```json
{
    "search": {
        "default_mode": "fuzzy",
        "max_results": 50
    },
    "indexing": {
        "skip_hidden_files": true,
        "generate_embeddings": true
    }
}
```

### CLI Usage

```bash
# Index directory
python -c "from main import FileIndexer; FileIndexer().index_directory('/path/to/dir')"

# Search
python -c "from main import FileIndexer; print(FileIndexer().search_files('query'))"
```

### Scheduled Indexing

**Windows** (Task Scheduler):
```
Program: python
Arguments: main.py --auto-index
```

**Linux/macOS** (cron):
```bash
0 2 * * * python3 /path/to/main.py --auto-index
```

## Keyboard Shortcuts

- `Enter` in search box → Search
- `Double-click` result → Open file
- `Ctrl+Q` → Quit (Linux/Windows)
- `Cmd+Q` → Quit (macOS)

## Next Steps

1. ✓ Index your main folders
2. ✓ Try different search modes
3. ✓ Configure preferences
4. ✓ Set up scheduled re-indexing
5. ✓ Read full documentation (README.md)

## Getting Help

- 📖 Full docs: `README.md`
- 🔧 Installation: `INSTALL.md`
- 🐛 Issues: GitHub Issues
- ⚙️ Config: `config.json`

---

**You're ready to go! Start indexing and searching. 🚀**
