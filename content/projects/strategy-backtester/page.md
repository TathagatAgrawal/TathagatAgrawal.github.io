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
