---
title: Semantic segmentation with U-Net
date: 2025-07
category: ml
repository: UNET_semantic_segmentation
skills: [computer-vision, pytorch, visualisation, python]

summary: >-
  A U-Net written in PyTorch that separates pets from the background in Oxford-IIIT Pet images,
  pixel by pixel.
result: Pixel accuracy on the training images rose from 75.9% to 91.9% over 10 epochs.
status: Complete

resume:
  title: Semantic Segmentation using U-Net
  tech: PyTorch, U-Net, CNN, Segmentation
  bullets:
    - Implemented the U-Net architecture for binary semantic segmentation on the Oxford-IIIT Pet dataset.
    - Designed and optimized data pre-processing pipelines (augmentation, normalization, resizing) and trained the network with binary cross-entropy loss and Adam optimizer.
    - Achieved high segmentation accuracy of 91.89%.
  variants:
    general:
      tech: PyTorch
      short: binary segmentation on the Oxford-IIIT Pet dataset with augmentation pipelines; 91.89% segmentation accuracy.
  short: U-Net for binary segmentation of the Oxford-IIIT Pet dataset
---

## The problem

Semantic segmentation labels every pixel of an image. Here the task is binary: pet or background, on the Oxford-IIIT Pet dataset.

## What I built

- A **U-Net** in PyTorch: an encoder that compresses the image, a decoder that expands it back to full size, and skip connections that carry fine detail across.
- A **data pipeline** that resizes images and masks to 128×128 (bilinear for images, nearest-neighbour for masks so labels stay crisp) and turns the dataset's three-way trimaps into binary masks.
- Training with binary cross-entropy and Adam for 10 epochs, with plots of the predictions.

## Result

Pixel accuracy on the training images rose from 75.9% after the first epoch to 91.9% after the tenth, with the loss still falling.

![Two line charts: training accuracy rising from about 76% to 92% and training loss falling from 0.50 to 0.20 over 10 epochs.](figures/training-curves.webp "Training accuracy and loss over 10 epochs.")

![Three rows of cat photos, each with its ground-truth mask and the model's predicted mask. The predictions capture the animal's overall shape but spill into nearby background.](figures/predictions.webp "Input images, ground-truth masks and the model's predictions. Images from the Oxford-IIIT Pet dataset (Parkhi et al., 2012, CC BY-SA 4.0).")

## Limits

The accuracy above is measured on the training images; the notebook does not score a held-out test split. The predicted masks get the overall shape right but blur edges and leak into similar-looking background, which more epochs, augmentation and a Dice or IoU metric would address.
