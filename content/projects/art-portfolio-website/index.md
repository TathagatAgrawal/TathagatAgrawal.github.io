---
title: Art portfolio website
date: 2026-01
category: tools
repository: mummy-art-webiste
private: true
skills: [web-frontend, javascript]

summary: >-
  A minimalist website for an artist to show their work: a gallery, a page per artwork with
  details and price, and an about page, in plain HTML, CSS and JavaScript.
status: Complete
---

## What it is

A portfolio website built for a family member who paints. The artwork is the focus: generous white space, a serif for headings, a sans-serif for text and a monospaced face for prices and dimensions.

## How it works

- **No build step:** plain HTML, CSS and JavaScript; open `index.html` and it works.
- **Data-driven gallery:** every artwork (image, description, dimensions, price) is one entry in `artworks.js`, from which the home-page gallery and each artwork's detail page are generated. Adding a painting means adding one entry.
- **Shared utilities** for formatting prices (with thousands separators and a separate currency) and dimensions.
- **Responsive layout** for phones and desktops, and an about page for the artist.
