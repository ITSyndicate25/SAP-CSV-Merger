<div align="center">
  <img src="fujifilm_bg.png" alt="SAP CSV Merger" width="120" height="80" style="border-radius: 12px;">

  # 📊 SAP CSV Merger

  **Merge daily SAP CSV files in one click — no manual Excel wrangling.**

  <p>
    <img src="https://img.shields.io/badge/python-3.14%2B-blue?style=flat&logo=python" alt="Python 3.14+">
    <img src="https://img.shields.io/badge/platform-Windows-lightgrey?style=flat&logo=windows" alt="Windows">
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat" alt="MIT License">
    <img src="https://img.shields.io/badge/status-production-brightgreen?style=flat" alt="Production Ready">
  </p>
</div>

---

## 🚀 What It Does

SAP CSV Merger connects to your **shared SAP folder**, detects daily CSV files by date range, and **merges them into one clean file** — ready for export. No more opening twenty CSV files and copy-pasting cells.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔗 **Auto-detect SAP Folder** | Reads from the configured SAP network share |
| 📅 **Date Range Filter** | Pick `From` and `To` dates — only matching files are loaded |
| 📁 **Available Files Panel** | See which files exist for your range at a glance |
| 🔍 **Live CSV Preview** | Select any file to inspect its contents before merging |
| 🔄 **Smart Merge** | Combines all files in range into a single dataset |
| 📤 **One-Click Export** | Save the merged result as a CSV file |
| 🎨 **Clean GUI** | Built with Tkinter — lightweight, no browser needed |

---

## 📥 Installation

### Option 1 — Installer (Recommended)

Download the latest `SAP_CSV_Merger_Setup_1.0.0.exe` from [Releases](https://github.com/ITSyndicate25/SAP-CSV-Merger/releases).

1. Run the installer
2. Follow the on-screen prompts
3. Launch from Start Menu or Desktop shortcut

### Option 2 — Installer Script

```batch
git clone https://github.com/ITSyndicate25/SAP-CSV-Merger.git
cd SAP-CSV-Merger
install.bat
```

Installs to `%LOCALAPPDATA%\SAP CSV Merger` with Start Menu and Desktop shortcuts.

### Option 3 — Run from Source

```bash
# Requirements: Python 3.10+
pip install pillow      # for icon support (optional)
python sap_merge.py
```

> **No dependencies required** — only uses Python standard library (`tkinter`, `csv`, `datetime`, `pathlib`).

---

## 🖥️ How To Use

```
  1. LAUNCH the app
  2. CLICK "Detect Files"   → loads available CSV files from SAP folder
  3. PICK a date range       → narrows the file list
  4. CLICK a file            → previews its contents on the right
  5. CLICK "Merge Selected"  → combines all matched files
  6. CLICK "Export"          → saves the merged CSV wherever you want
```

> 💡 **Pro tip:** Use the preview panel to verify column structure before merging.

---

## 🏗️ Project Structure

```
SAP-CSV-Merger/
├── .github/workflows/    # GitHub Actions automation
│   ├── ci.yml            # Build verification on push/PR
│   └── release.yml       # Automated release on tag push
├── sap_merge.py          # Main application logic & GUI
├── theme.py              # Colors, typography, spacing tokens
├── CONTEXT.md            # Business context & requirements
├── install.bat           # Batch installer
├── installer.iss         # Inno Setup script
├── sap_csv_merger.spec   # PyInstaller build config
├── fujifilm_bg.png       # Application icon
├── icon.ico              # Windows ICO icon
├── .gitignore
├── LICENSE
└── README.md             # You are here ✨
```

---

## ⚙️ Configuration

Edit the top of `sap_merge.py` to adjust these constants:

| Constant | Default | Description |
|----------|---------|-------------|
| `MAPPED_FOLDER` | `Z:\iSAP_IF` | Path to the shared SAP network folder |
| `DATE_FORMAT` | `%Y%m%d` | Date format in filenames (e.g. `20260702`) |
| `DATE_COLUMN_INDEX` | `12` | Zero-based column index containing the date |

---

## ❓ FAQ

<details>
<summary><b>🪟 The GUI looks wrong on my screen</b></summary>
<br>
The app uses a responsive two-column layout. If sections are cut off, try:
- Maximizing the window (F11)
- Adjusting your screen resolution to at least 1280×720
</details>

<details>
<summary><b>🔌 Can't connect to the SAP folder</b></summary>
<br>
Ensure the network drive `Z:\` is mapped and accessible. The status indicator at the top of the app will show green when connected. If not, mount the SAP share in Windows Explorer first.
</details>

<details>
<summary><b>📄 Why does the preview show letters (A, B, C...) instead of real column names?</b></summary>
<br>
The SAP CSV files don't include a header row. Column letters (A–AF) are synthetic labels matching the SAP report layout. Data starts on the first row.
</details>

<details>
<summary><b>🗑️ How do I uninstall?</b></summary>
<br>
Go to <b>Control Panel → Programs → Programs and Features</b>, find "SAP CSV Merger", and click Uninstall. Or run `%LOCALAPPDATA%\SAP CSV Merger\uninstall.bat`.
</details>

---

## 🛠️ Building From Source

```bash
# Build standalone executable
pip install pyinstaller
pyinstaller sap_csv_merger.spec --clean

# Output: dist/SAP_CSV_Merger/SAP_CSV_Merger.exe
```

---

## 🚀 Release Process

This project uses GitHub Actions to automate releases.

### Creating a Release

1. **Update version** in `installer.iss` (`#define MyAppVersion`)
2. **Commit changes**
3. **Create and push a tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. **GitHub Actions automatically:**
   - Builds the Windows executable with PyInstaller
   - Creates a ZIP archive
   - Publishes a GitHub Release with both files

### Manual Build (without GitHub Actions)

```bash
# Build executable
pyinstaller sap_csv_merger.spec --clean

# Create ZIP (PowerShell)
Compress-Archive -Path dist/SAP_CSV_Merger -DestinationPath SAP_CSV_Merger.zip
```

### Inno Setup Installer (Optional)

To create the `.exe` installer:
1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Open `installer.iss` in Inno Setup
3. Click **Build → Compile**
4. Output: `installer/SAP_CSV_Merger_Setup_1.0.0.exe`

> **Note:** Inno Setup is not included in GitHub Actions workflow due to licensing. Build the installer locally if needed.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.

---

<div align="center">
  <p>Built with ❤️ by <a href="https://github.com/ITSyndicate25">ITSyndicate25</a></p>
  <p>
    <a href="https://github.com/ITSyndicate25/SAP-CSV-Merger/issues">🐛 Report Bug</a>
    ·
    <a href="https://github.com/ITSyndicate25/SAP-CSV-Merger/issues">✨ Request Feature</a>
  </p>
</div>
