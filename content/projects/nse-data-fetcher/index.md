---
title: NSE Data Fetcher
date: 2026-09
category: tools
repository: nse-data-fetcher
skills: [desktop-apps, market-data, excel, testing, python]

summary: >-
  A desktop app that downloads historical price data for Indian stocks and indices into Excel,
  one sheet per symbol, with no coding required.
status: Released for Windows and macOS

resume:
  tech: Python, CustomTkinter, yfinance, openpyxl, PyInstaller
  bullets:
    - Built a desktop app that downloads historical OHLCV data for Indian stocks and indices (single symbols, index constituents or pasted lists) into Excel workbooks, one sheet per symbol.
    - Packaged it as standalone Windows and macOS apps released automatically by GitHub Actions, with bundled symbol lists as a fallback when NSE's live endpoints are unavailable.
  short: desktop app that downloads Indian market data to Excel
---

## The problem

Getting clean historical prices for a list of Indian stocks into Excel usually means a script, an API key or a lot of copying. This app is for people who just want the spreadsheet.

## What I built

- **Flexible input:** single symbols, whole index lists (NIFTY 50, NIFTY Bank, SENSEX), or a list pasted in or loaded from a file. Symbols are validated against the full NSE equity list, with autocomplete.
- **Batch download** of open, high, low, close and volume at a selectable interval, via Yahoo Finance.
- **Excel output** with one sheet per symbol.
- **Robust to flaky sources:** index constituents and the equity list are refreshed live from NSE's public endpoints on a background thread at startup; if those fail, the app falls back to bundled lists instead of crashing.
- **Packaged apps:** PyInstaller builds for Windows and macOS (as folders rather than single files, so they start quickly), built on each platform and published to GitHub Releases by a workflow when a version is tagged.
