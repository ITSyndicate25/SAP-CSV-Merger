# SAP CSV Merger — Project Context

## Domain Glossary

| Term | Definition |
|------|------------|
| SAP CSV file | Daily data export from SAP system, stored as CSV in shared folder |
| File naming pattern | `YYYYMMDD_FYBPL004.csv` — date prefix + fixed report suffix |
| Shared folder | Network path `\\192.168.136.8\iSAP_log`, mapped to `Z:\iSAP_IF` |
| Monthly archive folder | Subfolder under shared folder named `YYYYMM` (e.g., `202606`) containing daily SAP files moved after month-end |
| Date range | User-selected start and end dates for merging multiple SAP files |
| Merged file | Combined output of multiple SAP CSVs, appended in date order |
| Column L | Date field inside CSV content (format: YYYYMMDD), used for validation |
| Headerless CSV | SAP files have no column headers — raw data only |
| Material code | Column D values (e.g., 898023N50) — identifies SAP materials |
| Line number | Column E — sequential row identifier within each file |

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| GUI framework | tkinter | Built into Python, zero dependencies, meets no-install requirement |
| Network mapping | Optional auto-run with disconnect | User controls connection; app can auto-connect on startup |
| File pattern | Fixed `YYYYMMDD_FYBPL004.csv` | No variation in report suffix |
| Date selection | Dropdown fields (YYYY, MM, DD) plus Today / 7 days / Month presets | Simple, no extra dependencies; presets cover the common ranges |
| Layout | Full-width tables stacked with a draggable divider over a compact filter bar | Both data areas get the window width; each can take more height on demand |
| Scaling | Logical spacing multiplied by `tk scaling`; process is DPI aware | Same proportions on 100% and 150% displays |
| CSV preview | First 10 rows in table | Quick sanity check without loading full file |
| Export location | User-selectable folder | Flexibility for different workflows |
| Error display | Status bar + popup dialogs | Info in status bar, errors in modal popups |

## CSV Structure (from actual data)

**No header row** — CSVs are raw data with 20+ columns.

| Column | Content | Notes |
|--------|---------|-------|
| A | (blank) | Unused |
| B | 1 | Constant |
| C | BYVM4 | Constant |
| D | Material codes | e.g., 898023N50, 898016N50 |
| E | Line numbers | Sequential (48, 49, 50...) |
| F | 1000 | Constant |
| G | A3-1005Y68869 | Constant |
| H | YB01 | Constant |
| I | 2511 | Constant |
| J | 0 | Constant |
| K | (blank) | Unused |
| L | **Date (YYYYMMDD)** | **Key field** — matches filename date |
| M | (blank) | Unused |
| N | 1 | Constant |
| O | Equipment IDs | Varies (A3-117E 42050, etc.) |
| P | 2511 | Constant |
| Q | Quantity | e.g., 1 EA, 2 EA |
| R-T | 0 | Constants |
| U | (blank) | Unused |
| V | PUSH | Constant |
| W | VM4-xxxxx | Varies |

## Architecture

```
┌─────────────────────────────────────┐
│           GUI (tkinter)             │
├─────────────────────────────────────┤
│  - Command bar: connection, scan    │
│  - Filter bar: dates + quick ranges │
│  - SAP files table (resizable)      │
│  - CSV preview table (resizable)    │
│  - Merge/Export/Clear action bar    │
│  - Status strip                     │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│         Core Logic                  │
├─────────────────────────────────────┤
│  - Network drive mapping            │
│  - File pattern detection           │
│  - Date range validation            │
│  - CSV reading (headerless)         │
│  - Date validation (Column L)       │
│  - CSV merging (append in order)    │
│  - Export with file dialog          │
└─────────────────────────────────────┘
```

## User Workflow

1. Launch app: `python sap_merge.py`
2. Optionally connect to network drive (auto-run or manual)
3. Enter date range (From / To, or a quick-range preset)
4. Click "Detect files" — app selects the available SAP files for that range
5. Preview files (first 10 rows displayed; drag the divider to resize)
6. Click "Merge selected" — combines files in date order
7. Click "Export merged" — choose location, save merged file

## Validation Rules

- Check if Z:\iSAP_IF exists and is accessible
- Verify each date in range has corresponding file
- Skip empty files with warning
- Skip unreadable files with error
- Ensure files are appended in ascending date order
- Handle month/year transitions in date range
