# Getting Started with LogReader v1.0

**Quick start guide to get LogReader running in 5 minutes.**

---

## Prerequisites Check

Before you begin, verify you have:

```bash
# Check Python version (need 3.10+)
python --version
```

If Python is not installed or version is < 3.10:
- **Windows**: Download from [python.org](https://www.python.org/downloads/) (check "Add to PATH")
- **macOS**: `brew install python@3.10`
- **Linux**: `sudo apt install python3.10 python3.10-venv`

---

## Installation (3 Steps)

### 1. Create Virtual Environment

```bash
cd /path/to/LogReader
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```cmd
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs PyQt6 (~50MB download).

---

## Running LogReader

```bash
python python/main.py
```

The LogReader window should open immediately.

---

## First Time Use

### Opening a Log File

1. Press **Ctrl+O** or click **File → Open**
2. Navigate to a `.log` file
3. Click **Open**
4. Watch the status bar for parsing progress

### Example Log File

If you have `helix.log` or `test_input.log` in the directory, try those first.

---

## Basic Operations

### Filtering

1. Check log level boxes at bottom (DEBUG, INFO, WARN, ERROR)
2. Table updates instantly
3. Entry count shows filtered results

### Searching

1. Type in "Search:" box
2. Results filter as you type
3. Press **Esc** to clear

### Jumping to Line

1. Enter line number in "Jump to Line:" field
2. Press **Enter** or click **Go**
3. Line is selected and centered

### Copying

1. Click to select row(s)
2. Press **Ctrl+C**
3. Paste into any text editor

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Ctrl+O** | Open file |
| **Ctrl+R** | Reload file |
| **Ctrl+C** | Copy selected rows |
| **Ctrl+Q** | Quit |
| **Esc** | Clear search |

---

## Troubleshooting

### "python: command not found"
- Python not installed or not in PATH
- Reinstall with "Add to PATH" option

### "No module named 'PyQt6'"
- Virtual environment not activated or dependencies not installed
- Run: `pip install -r requirements.txt`

### Application won't start
- Check Python version: `python --version` (must be 3.10+)
- Check if venv activated: look for `(venv)` in prompt
- Try: `pip list | grep PyQt6` to verify installation

### File won't open
- Verify file format uses ASCII field separator (char 31)
- See README.md for log format specification

---

## Next Steps

- Read [USER_GUIDE.md](USER_GUIDE.md) for detailed features
- Check [README.md](README.md) for log format details
- Review keyboard shortcuts: **Help → Keyboard Shortcuts** in app

---

## Getting Help

- **Documentation**: USER_GUIDE.md has detailed instructions
- **Issues**: Report bugs on GitHub Issues
- **Questions**: GitHub Discussions

---

**You're ready to go!** Open a log file and start exploring. 🚀
