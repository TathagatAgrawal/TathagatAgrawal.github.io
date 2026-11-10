---
title: Invoice Generator
date: 2026-10
category: tools
repository: invoice-generator
private: true
skills: [documents, fastapi, pydantic, web-frontend, testing, python]

summary: >-
  A web app for professional invoices: nine templates, correct tax handling, and a live preview
  that is the real PDF layout, rendered by Typst as you type.
status: MVP complete

resume:
  tech: Python, FastAPI, Typst, Pydantic, JavaScript
  bullets:
    - Built an **invoice web app** with a live preview that is the real PDF, rendered by **Typst** as you type; nine templates with safe customisation and archival PDF/A-2b output with embedded fonts.
    - Implemented an exact-decimal **calculation engine** (per-line discounts, multiple tax rates such as CGST + SGST, tax-inclusive pricing, rounding rules) and locale-aware formatting, tested against every template and edge case in CI.
  short: invoice web app with Typst-rendered live PDF preview and an exact tax engine
---

## The problem

Small businesses and freelancers in India need invoices that look professional and get taxes right: GST split into CGST and SGST, tax-inclusive prices, discounts and rounding. Most free tools get one of those wrong, or show a preview that doesn't match the PDF.

## What I built

- **Any kind of line item:** goods, services, hours, fees and expenses, with quantity, unit, item codes (SKU, HSN, SAC), per-line discounts and any number of tax rates per line, grouped into sections with optional subtotals.
- **Taxes done properly:** a per-rate breakdown (for example CGST + SGST), tax-inclusive pricing, per-rate or per-line tax rounding and cash rounding of the total. All maths uses exact decimals.
- **A preview that is the PDF:** the invoice is rendered by Typst as you type, so what you see is exactly what downloads. Downloads are archival PDF/A-2b files with bundled fonts, identical on every machine.
- **Nine templates,** from Swiss-minimal to an old-style bill-head, each customisable within safe limits (contrast-checked accent colours, font pairings, density, paper size, PAID/DRAFT stamps).
- **Locale-aware formatting:** `₹1,41,170.00` for India, `1.234,50 €` for Germany, and the amount in words.
- **Your business on every invoice:** logo, tax IDs, payment details and a UPI or payment-link QR code.

## Quality

CI runs formatting, linting and the test suite on every push: calculation invariants, every template against every edge case, and the API. The full design (requirements, architecture, calculation engine, rendering, security, roadmap) is written up in fifteen design documents.

## Status

The MVP is deliberately stateless: your invoice and business details stay in your browser. Accounts, a database, client and catalogue management and gap-free invoice numbering are the next milestones.
