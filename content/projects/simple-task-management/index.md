---
title: Simple Task Management
date: 2026-11
category: tools
repository: simple-task-management
private: false
skills: [fastapi, databases, web-frontend, javascript, testing, python]

summary: >-
  A one-page task board built for a real CA firm and shaped by how they work: deadlines, recurring
  compliance filings and a thread of updates on every task. It runs on one PC in their office and
  staff reach it privately over Tailscale.
status: Deployed for the firm

resume:
  tech: Python, FastAPI, SQLite, htmx, Tailscale, PowerShell
  bullets:
    - Built and deployed a **task board for a real CA firm**, designed around their needs (multiple assignees, due-date summaries, recurring GST, TDS and ITR filings, a full history thread per task); it is served from one Windows PC and reached privately over **Tailscale (tailnet)**.
    - 'Kept it deliberately simple to run without IT support: **FastAPI + SQLite + htmx** with no build step, automatic migrations, nightly online backups and PowerShell scripts that install, update and restore it, tested by CI on Windows, macOS and Linux.'
  short: task board built for a real CA firm, deployed privately over Tailscale
---

## The problem

A three-person CA firm tracks a steady stream of deadlines: GST returns every month, TDS every quarter, ITR and ROC filings every year. They needed one place to see what is overdue, what is due today and what is due soon, and who is doing what. Off-the-shelf project tools were too heavy for three people with no IT support, and a spreadsheet loses the history of who did what.

I built this for them, around how they actually work, and it is deployed and in use at the firm.

## What I built

- **One page:** summaries of what is overdue, due today and due in the next three days, above a To do / Doing / Done board. Cards move between columns by drag-and-drop, and each column stays sorted by due date.
- **Tasks the way a CA firm needs them:** one or more assignees, a due date, and an optional repeat (weekly, monthly, quarterly or yearly). Finishing a recurring task creates the next one, with month-end dates handled correctly, and the two link to each other.
- **A complete history:** every change (status, assignees, due date, notes, repeat) is written to the task's update thread in the same database transaction as the change, so the thread is a trustworthy record for compliance work. People are never hard-deleted, so their names stay on past comments.
- **Simple access:** one admin adds and removes people, passwords are hashed with scrypt, and there are light, dark and system themes that follow each person. A phone layout and a JSON API sit on the same code.

![The task board with demo data. Three summary panels along the top list overdue tasks, tasks due today and tasks due in the next three days. Below, the board has To do, Doing and Done columns of cards for filings such as GSTR-1 and TDS returns, each with a due date badge and the initials of the people assigned.](figures/board.webp "The board, with invented demo clients and people. Cards show how late or soon they are, a repeat badge and who is assigned.")

## Deployed over Tailscale

The app runs on one always-on Windows PC in the firm's office, bound to localhost only. [Tailscale](https://tailscale.com) Serve publishes it with HTTPS to the firm's private tailnet, so staff open it from any device they have signed in to Tailscale and it is never exposed to the public internet. An install script sets up Python, the app, a scheduled task that starts it at boot and restarts it if it crashes, and the Tailscale publishing. Further scripts report status, update and restore it, with messages written for an accountant rather than a developer. Backups run nightly using SQLite's online backup API into a cloud-synced folder.

## Design choices

The firm has no one to maintain it, so every decision favours fewer moving parts: FastAPI, Jinja2 and a single vendored htmx file, plain SQL in one module, about 220 lines of JavaScript for drag-and-drop, and no Node, Docker or separate database server. "Today" is always computed in IST from an injected clock, and the date logic is pure functions that are tested exhaustively.

## Quality

CI runs lint, format checks and the test suite on Ubuntu, Windows and macOS, and parses every Windows script with PSScriptAnalyzer. The repository also has developer documentation, an illustrated in-app user manual and the original design plan.
