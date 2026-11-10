---
authors: [Agrawal T, Kumar M]
year: 2025
title: Analysis of Grokking-Induced Rigidity in Neural Networks using Transfer Learning
venue: "In: Proceedings of Data Analytics and Management, ICDAM"
summary: >-
  An MLP grokked on MNIST reached 90.4% validation accuracy but adapted far worse when
  fine-tuned on Fashion-MNIST than conventionally trained models; weight, loss-landscape and
  Hessian analyses point to rigidity from a flatter loss surface.
thesis: grokking-thesis
---

## Overview

Grokking improves a network's accuracy on the task it was trained on, but what does it do to its ability to learn something new? This paper uses transfer learning as a probe. The same small MLP was pre-trained on MNIST three ways: standard training on all 60,000 images, standard training on 1,500 images, and grokking-inducing training on those 1,500 images with large initial weights. Each model was then fine-tuned on Fashion-MNIST with identical settings.

![Training and validation accuracy of the grokked model over 100,000 epochs on a log scale. Training accuracy reaches 100% around 3,000 epochs; validation accuracy stays low until about 10,000 epochs and then climbs to about 90%.](figures/grokked-pretraining.webp "Grokking: training accuracy saturates early, validation accuracy jumps thousands of epochs later.")

## Results

The grokked model was the best on MNIST, with 100% training and 90.4% validation accuracy. It was also by far the worst at adapting: after fine-tuning on Fashion-MNIST it reached about 16.5% validation accuracy, while the two standard models reached about 71% and 70%.

![Training accuracy on Fashion-MNIST over 75 fine-tuning epochs: the two standard models climb to about 0.72, while the grokked model stays between 0.12 and 0.25.](figures/fine-tuning-accuracy.webp "Training accuracy while fine-tuning on Fashion-MNIST. The grokked model barely adapts.")

Analyses of the weight changes, the loss landscape and the eigenvalue spectrum of the loss Hessian point to the same cause: the grokked model sits in a flatter region of the loss surface and its weights barely move during fine-tuning, so grokking appears to buy accuracy on the source task at the cost of flexibility. For an overview of grokking itself, see the [review](/research/grokking-review/).
