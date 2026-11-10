---
title: ITR Fetch
date: 2026-11
category: tools
repository: computax-client-file-download
skills: [desktop-apps, web-frontend, javascript, testing, python]

summary: >-
  A desktop tool for tax practitioners who use CompuTax: finds a client's returns and tax
  computations across years and copies them into one folder, with nothing to install.
status: Released for Windows and macOS

resume:
  title: ITR Fetch
  tech: Python, JavaScript, PyInstaller, GitHub Actions
  bullets:
    - Built a **desktop tool for a tax practice** that finds a client's returns and computations across years in CompuTax data folders and copies them into one folder per client, never overwriting or modifying source files.
    - Shipped it as standalone Windows and macOS apps with a local browser interface and fuzzy client search, built and released automatically by GitHub Actions.
  short: one-click desktop tool that collects a client's tax documents across years
---

## The problem

Tax practitioners using CompuTax keep each year's files in a separate folder. Pulling together one client's income-tax returns (ITR-V) and computation sheets across several years means opening folder after folder and copying files by hand.

## What I built

A small app that does it in one step: choose the CompuTax folder once, search for a client by ID or name, pick the years and a destination, and click **Copy files**. Each client gets one folder; files without the year in their name get it added (for example `ITRV_109B_2021.pdf`).

- **Safe by design:** it never changes anything inside the CompuTax folder and never overwrites a file in the destination. The only thing it saves is the location of the CompuTax folder.
- **Nothing to install:** a single app for Windows and for Apple-silicon Macs. It opens in the browser, listens only on the local machine, and quits a few seconds after the tab is closed.
- **Fuzzy client search** in plain JavaScript, with its own tests alongside the Python tests.
- **Automatic releases:** pushing a version tag makes GitHub Actions build both apps and attach them to a release.

It was built for a real practice, which is why it puts plain-language setup steps (including getting past the unsigned-app warnings on Windows and macOS) in the README.
