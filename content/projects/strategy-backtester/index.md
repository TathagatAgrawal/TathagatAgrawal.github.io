---
title: Strategy Backtester
date: 2026-08
category: quant
repository: strategy-backtester
skills: [backtesting, risk-metrics, market-data, pandas, testing, cli-tui, visualisation, python]

summary: >-
  An event-driven backtesting engine written from scratch, with slippage and cost modelling and
  lookahead-bias prevention enforced by tests.
status: Complete

resume:
  tech: Python, pandas, NumPy, CCXT, Typer, Rich, pytest, Matplotlib
  bullets:
    - Built an event-driven backtesting engine from scratch, with realistic slippage and transaction-cost modeling and structural lookahead-bias prevention enforced by a dedicated regression suite.
    - Implemented order-execution logic including limit/stop fills and bracket (OCO) take-profit/stop-loss orders, plus a same-bar-close comparison mode to quantify realistic vs. naive fill timing.
    - Built a CCXT-based market-data collector and a full performance-analytics suite (Sharpe, Sortino, CAGR, max drawdown, win rate, cost transparency), validated end-to-end against &nbsp;9 months of real BTC/USDT hourly data.
    - Shipped two trading strategies (SMA crossover, RSI mean-reversion) behind a Typer/Rich CLI supporting CSV/JSON export and equity-curve/drawdown chart plotting.
  variants:
    general:
      bullets:
        - Built an event-driven backtesting engine from scratch with slippage and transaction-cost modeling, limit/stop and bracket (OCO) orders, and lookahead-bias prevention enforced by a dedicated regression suite.
        - Built a CCXT market-data collector and analytics suite (Sharpe, Sortino, CAGR, max drawdown, win rate), validated on 9 months of real BTC/USDT hourly data; shipped SMA crossover and RSI mean-reversion strategies.
  short: event-driven backtesting engine with cost modelling and lookahead-bias tests
---

## The problem

Backtesting libraries hide the details that decide whether a backtest can be trusted: when an order fills, at what price, what it costs, and whether the strategy accidentally used tomorrow's data. I wrote an engine from scratch, without backtrader, zipline or backtesting.py, to get each of those details right and test them.

## What I built

- **Event-driven core:** market data, signals, orders and fills flow as events in time order, so a strategy can only ever see the past.
- **Lookahead-bias prevention:** enforced structurally by the data handler and checked by a dedicated regression suite.
- **Realistic execution:** slippage, commission, limit and stop fills, and bracket take-profit and stop-loss orders with one-cancels-other behaviour. A comparison mode measures how much a naive same-bar-close fill flatters results.
- **Data and analytics:** a CCXT collector for crypto market data and a performance suite (Sharpe, Sortino, CAGR, maximum drawdown, win rate and a breakdown of costs).
- **Strategies:** an SMA crossover and an RSI mean-reversion strategy with real bracket orders.
- **CLI:** a Typer and Rich command line with CSV and JSON export and equity-curve and drawdown charts.

Both strategies were validated end to end on about nine months of real BTC/USDT hourly data. The design is documented in eight short design documents in the repository, from the event system to execution and analytics.
