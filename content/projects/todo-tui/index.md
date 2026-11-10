---
title: Terminal to-do app
date: 2026-08
category: practice
repository: todo-tui
private: true
skills: [cli-tui, testing, python]

summary: >-
  A keyboard-driven to-do app for the terminal with multiple lists, built with Textual, that
  stores each list as a plain Markdown checklist.
status: In progress
---

## What it is

A to-do app that lives in the terminal and is driven entirely from the keyboard, built with Textual.

- **Multiple lists** in a sidebar, with modals for adding and editing tasks and lists.
- **Plain-text storage:** each list is its own Markdown checklist file, so lists stay readable and editable outside the app.
- **Layered code,** documented in an architecture note, with tests, linting and formatting checks run in CI.

It is a work in progress; features land through pull requests.
