---
title: Trade Filter ML
date: 2026-11
category: quant
repository: trade-filter-ml
private: true
skills: [experiment-design, gradient-boosting, scikit-learn, calibration, optuna, mlflow, shap, pandas, market-data, risk-metrics, python]

summary: >-
  A leakage-safe meta-labeling study with a pre-registered holdout, asking whether ML can filter
  a simple trading rule's signals well enough to matter after costs.
result: >-
  On a pre-registered holdout the filter improved all three strategies, but no gain was
  statistically distinguishable from zero.
status: Complete

resume:
  tech: Python, LightGBM, scikit-learn, Optuna, MLflow, SHAP, pandas
  bullets:
    - Built a leakage-safe **meta-labeling pipeline** (triple-barrier labels with overlap-aware weights, purged and embargoed cross-validation, nested tuning) to test whether ML can filter rule-based trading signals after costs.
    - Guarded against false discovery with **negative controls** (random filters of equal size), the **deflated Sharpe ratio** and **PBO**, and a **pre-registered holdout**; reported an honest null result (+0.035 to +0.067 R per trade, every 95% interval spanning zero).
  short: leakage-safe meta-labeling study with a pre-registered holdout and an honestly reported null result
---

## The question

Simple trading rules such as breakouts and moving-average crossovers fire often and, after costs, mostly lose money. Meta-labeling trains a second model that looks at each signal when it fires and decides whether to take it. The question: can such a filter, using only information available at that moment, beat both the unfiltered rule and a random filter that keeps the same share of trades?

It is very easy to fool yourself here. Overlapping trades leak information between training and test folds, repeated tuning overfits the validation data, and a filter that keeps fewer trades can look better by chance alone. The project is built around not falling for any of these.

## What I built

- **Labels:** triple-barrier labels (take-profit, stop-loss and time limit) with sample weights that account for overlapping trades.
- **Validation:** purged and embargoed cross-validation, with hyperparameters tuned in an inner loop so the outer score is never used for tuning.
- **Negative controls:** every filter is compared against 2,000 random filters that keep the same share of trades, and against shuffled labels.
- **Overfitting statistics:** the deflated Sharpe ratio and the probability of backtest overfitting, to account for how many configurations were tried.
- **A pre-registered holdout:** the code refuses to touch the holdout period (January 2025 to October 2026) until the final configuration is written down and frozen.
- Five development experiments (model family, feature groups, training scope, decision rule, tuning budget) chose that configuration: a LightGBM model, Platt-calibrated, that sizes positions by its confidence.

## Result

On the holdout, the frozen filter improved the average trade for all three strategies, including the EMA crossover, which was never used during development. But every 95% interval includes zero, so the pre-registered success criteria were not met. I report it as a null result.

![Dot plot of the change in average R per trade for three strategies on the holdout. All estimates are positive (+0.067, +0.035, +0.042), every 95% interval crosses zero, and the development estimates (diamonds) are higher.](figures/holdout-lift.webp "Change in average R per unit of risk from filtering: holdout estimates with 95% intervals (dots) against the development estimates (diamonds).")

The negative control asks a stricter question: does the model beat filters that throw away the same share of trades at random? It did for the Donchian breakout, narrowly missed the 95% criterion for the EMA crossover, and did not for Bollinger + RSI.

![Three histograms of the average R of 2,000 random filters per strategy, each with a vertical line for the model filter, which beats 99.6%, 81.6% and 94.8% of them.](figures/holdout-random-filters.webp "The model filter (line) against 2,000 random filters that keep the same share of trades (bars).")

```table
file: results/holdout.csv
caption: Holdout results, January 2025 to October 2026. "Change in R" is the filtered minus the unfiltered average trade, per unit of risk.
columns:
  scope: Strategy
  coverage: Trades kept
  expectancy_diff: Change in R
  expectancy_diff_low: 95% low
  expectancy_diff_high: 95% high
  random_percentile: Beats random
  cal_auc: AUC
format:
  coverage: "{:.0%}"
  expectancy_diff: "{:+.3f}"
  expectancy_diff_low: "{:+.3f}"
  expectancy_diff_high: "{:+.3f}"
  random_percentile: "{:.1f}%"
  cal_auc: "{:.2f}"
labels:
  donchian: Donchian breakout
  bb_rsi: Bollinger + RSI fade
  ema_cross: EMA crossover (held out)
```

## What I learned

In development, a small signal from volatility, trend strength and volume at the moment of the signal beat random filters of the same size. On the holdout it pointed the same way at about half the size and could not be confirmed. Neither the filter nor any setting I tested makes these strategies reliably profitable after costs. Building the guardrails first is what made it possible to say that with confidence instead of publishing an overfit backtest.
