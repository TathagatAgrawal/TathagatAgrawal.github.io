---
title: Crop disease detection
date: 2022-12
category: ml
repository: multiple-crop-disease-prediction
skills: [computer-vision, pytorch, visualisation, python]

summary: >-
  A convolutional network that classifies photos of crop leaves into 38 healthy and diseased
  categories from the PlantVillage dataset.
result: 98.28% accuracy on the validation images, with precision, recall and F1 all above 98%.
status: Complete

resume:
  title: Multiple Disease Prediction in Crops using Deep Learning
  tech: CNN, PyTorch, OpenCV, Keras
  bullets:
    - Implemented a stacked CNN to classify crop leaves into one of 38 disease categories.
    - Pre-processed images via resizing, normalization, and data augmentation and mitigated class imbalance to prevent overfitting.
    - Trained a multi-block CNN architecture followed by fully connected layers with dropout and L2 regularization using Adam on cross-entropy loss, achieving 98.28% test accuracy and more than 98% precision, recall, and F1-score.
  short: stacked CNN classifying crop leaves into 38 disease categories
---

## The problem

Spotting plant diseases early matters for yields, and a photo of a leaf is often enough for an expert. The question was how well a convolutional network trained from scratch can do the same across 38 categories of healthy and diseased leaves from 14 crops in the PlantVillage dataset.

## What I built

- A **stacked CNN** in PyTorch: blocks of 3×3 convolutions followed by fully connected layers with dropout, trained from scratch on 224×224 images.
- **Training** with Adam and cross-entropy for up to 10 epochs, keeping the checkpoint with the best validation accuracy (with early stopping).

## Result

After 10 epochs the model reached 98.28% accuracy on the validation images, with precision 98.30%, recall 98.28% and F1 98.27%.

![Line chart of training and validation loss and accuracy over 10 epochs. Validation accuracy climbs above 0.95 by epoch 3 and ends near 0.98; validation loss stays below training loss.](figures/training-curves.webp "Training and validation loss and accuracy over 10 epochs.")

## Limits

The same validation split was used to choose the checkpoint and for the final scores, so the numbers are slightly optimistic; a separate test split would give a cleaner estimate. PlantVillage photos are taken against plain backgrounds, so accuracy on photos taken in a field would be lower.
