---
title: Algorithmic trading notes and experiments
date: 2025-09
category: quant
repository: algo_trading
private: true
skills: [market-data, pandas, documents, python]

summary: >-
  A concise written overview of algorithmic trading (strategies, the maths behind them, risk and
  evaluation) and a first notebook of experiments on Indian stocks.
status: Notes
---

## What it is

My starting point in quantitative trading, before building backtesting engines.

- **Notes (Typst):** an academic-style overview of algorithmic trading: what an algorithmic trading system is made of (signals, sizing, execution, risk management, backtesting), price models such as geometric Brownian motion and mean-reverting processes, signals as statistical forecasts, common strategies, risk and evaluation, and practical engineering issues.
- **Notebook:** first experiments on Indian stocks (Reliance, TCS, Tata Steel) using Yahoo Finance data, such as how often three green candles are followed by a red one.

These questions led directly to the [Strategy Backtester](/projects/strategy-backtester/), which builds the execution and bias checks properly.
