---
title: Star classification
date: 2025-08
category: ml
repository: astro-ml-stellar-classification
skills: [scikit-learn, mlflow, flask, pandas, visualisation, python]

summary: >-
  Compared MLP, SVC and Random Forest classifiers on a six-class stellar dataset, with
  experiment tracking in MLflow and a small web app for predictions.
status: Complete

resume:
  title: Star Classification using Supervised Learning Models
  tech: Scikit-learn, MLflow, Pandas, Matplotlib, NumPy, Flask, HTML
  bullets:
    - Trained and evaluated MLP, SVC, and Random Forest classifiers for six class stellar classification with rigorous hyperparameter tuning.
    - Used MLflow for experiment tracking, hyperparameter logging, and automatic selection of best-performing model.
    - Implemented a Flask web application for interactive predictions, including H-R diagram visualization.
  variants:
    general:
      tech: Scikit-learn, MLflow, Flask
      short: MLP, SVC and Random Forest classifiers for six-class stellar classification, with MLflow tracking and a Flask app.
  short: MLP, SVC and Random Forest classifiers for six-class stellar classification
---

## The problem

Classify stars into six types (red dwarf, brown dwarf, white dwarf, main sequence, supergiant, hypergiant) from four physical measurements: temperature, luminosity, radius and absolute magnitude. The dataset has 240 stars, 40 of each type, so accuracy is a fair metric.

## What I did

- **Exploratory analysis** of the features and class balance.
- **Three model families** (multilayer perceptron, support vector classifier and random forest), each trained over a grid of hyperparameters.
- **Experiment tracking with MLflow:** every run's parameters and accuracy are logged, and the best model is selected and saved automatically.
- **A Flask web app** where you enter a star's measurements and get its predicted type, shown next to a Hertzsprung–Russell diagram for reference.
