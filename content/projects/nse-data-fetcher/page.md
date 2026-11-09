## The problem

Getting clean historical prices for a list of Indian stocks into Excel usually means a script, an API key or a lot of copying. This app is for people who just want the spreadsheet.

## What I built

- **Flexible input:** single symbols, whole index lists (NIFTY 50, NIFTY Bank, SENSEX), or a list pasted in or loaded from a file. Symbols are validated against the full NSE equity list, with autocomplete.
- **Batch download** of open, high, low, close and volume at a selectable interval, via Yahoo Finance.
- **Excel output** with one sheet per symbol.
- **Robust to flaky sources:** index constituents and the equity list are refreshed live from NSE's public endpoints on a background thread at startup; if those fail, the app falls back to bundled lists instead of crashing.
- **Packaged apps:** PyInstaller builds for Windows and macOS (as folders rather than single files, so they start quickly), built on each platform and published to GitHub Releases by a workflow when a version is tagged.
