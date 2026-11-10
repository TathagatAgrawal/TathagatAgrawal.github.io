---
title: Neural network from scratch
date: 2025-07
category: ml
repository: MNIST_from_scratch
private: true
skills: [python, pandas]

summary: >-
  A neural network for MNIST digit recognition written with nothing but NumPy: forward pass,
  backpropagation and training loop by hand.
status: Complete
---

## What it is

An exercise in understanding what deep-learning libraries do for you. The network classifies MNIST handwritten digits using only NumPy, with every piece written by hand:

- **Forward propagation** with ReLU activations and a softmax output layer.
- **Backpropagation:** the gradients of the loss with respect to every weight and bias, derived and coded directly.
- **Training:** mini-batch gradient descent with a learning-rate schedule that decays over epochs.
- **Evaluation:** prediction accuracy on held-out images.
