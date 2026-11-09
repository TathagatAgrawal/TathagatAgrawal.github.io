## The problem

Most retail backtesting tools make it easy to find a strategy that looks great on past data and hard to tell whether it will hold up. I wanted a tool where designing a strategy is quick, but every result comes with the checks needed to judge it.

## What I built

A web app on top of [NautilusTrader](https://github.com/nautechsystems/nautilus_trader), which does all the simulation; the app translates strategies into it and orchestrates runs.

- **Strategy builder:** parameters, 24 TA-Lib indicators, ALL/ANY/NOT condition trees with comparisons and crossovers, stop loss, take profit, trailing stops and position sizing. Strategies can also be edited as JSON, are validated live with located errors, and are saved as immutable versions. Six starter strategies come with tutorials.
- **Markets:** fuzzy search over about 15,000 US and Indian (NSE) securities built from the exchanges' official symbol files. Indian stocks run in rupees with NSE/BSE session times.
- **Backtests:** daily bars, run in background worker processes with live progress and cancellation. Reports show performance against buy-and-hold, equity, drawdown, trades on the price chart and a trade log, with an Excel export.
- **Optimisation:** grid, random or Bayesian (TPE) search with Optuna over any strategy's parameters, optionally with metric constraints, validated on a holdout or walk-forward windows.
- **Overfitting diagnostics:** out-of-sample against in-sample Sharpe, the Deflated Sharpe Ratio, the stability of the best parameters' neighbourhood, walk-forward efficiency, and an "overfit" badge that explains which rule it fired.

## How I know it's right

- Look-ahead tests: truncating future data never changes past indicator values or signals, for every indicator and preset.
- Engine scenarios with hand-computed fills: next-open timing, slippage, stops intrabar and on gaps, trailing stops, reversals and accounting reconciliation.
- Cross-validation against vectorbt, an independent backtesting engine, with the known differences documented.
- The Deflated Sharpe Ratio reproduces Bailey and López de Prado's worked example, and optimising pure noise is never labelled robust.

## Status

The first version runs locally. Backtested results are hypothetical; market data comes from Yahoo Finance for personal use only.
