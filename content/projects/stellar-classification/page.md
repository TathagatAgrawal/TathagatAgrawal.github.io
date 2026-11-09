## The problem

Classify stars into six types (red dwarf, brown dwarf, white dwarf, main sequence, supergiant, hypergiant) from four physical measurements: temperature, luminosity, radius and absolute magnitude. The dataset has 240 stars, 40 of each type, so accuracy is a fair metric.

## What I did

- **Exploratory analysis** of the features and class balance.
- **Three model families** (multilayer perceptron, support vector classifier and random forest), each trained over a grid of hyperparameters.
- **Experiment tracking with MLflow:** every run's parameters and accuracy are logged, and the best model is selected and saved automatically.
- **A Flask web app** where you enter a star's measurements and get its predicted type, shown next to a Hertzsprung–Russell diagram for reference.
