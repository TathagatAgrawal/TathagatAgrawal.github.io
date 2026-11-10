---
title: Approximating π with coin flips
date: 2026-03
category: practice
repository: pi
private: true
skills: [python]

summary: A small simulation that estimates π from sequences of coin flips, inspired by Matt Parker's Pi Day video.
status: Complete
---

## What it is

Flip a coin until heads have pulled ahead of tails, and note the share of heads at that moment. Averaged over many such runs, that share tends to π/4. The script simulates this with NumPy and multiplies the average by four to estimate π.
