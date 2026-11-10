---
authors: [Agrawal T, Chauhan A, Singh A]
year: 2024
title: >-
  Advancing Linguistic Frontiers with mBERT Fine-Tuning for Hindi and English Named Entity
  Recognition Using HiNER and WikiNEuRal Datasets
venue: "In: ICCCNT 2024"
url: https://ieeexplore.ieee.org/document/10724051
url_label: Paper link
summary: >-
  Fine-tuned multilingual BERT for Hindi and English NER: F1 0.899 on HiNER and 0.946 on
  WikiNEuRal, ahead of Indic-BERT and XLM-R baselines.
project: mbert-ner
resume:
  title: >-
    Advancing Linguistic Frontiers with mBERT Fine-Tuning for Hindi and English NER Using
    HiNER and WikiNEuRal Datasets
  note: F1 of 0.899 (HiNER), 0.946 (WikiNEuRal).
---

## Overview

Named entity recognition, finding the names of people, places, organisations and so on in text, is well served for English but much less so for Hindi, which has fewer labelled datasets. This paper asks whether one multilingual model, fine-tuned separately for each language, can match models built for Indian languages. It fine-tunes `bert-base-multilingual-cased` (mBERT) on HiNER for Hindi and WikiNEuRal for English, aligning each word's entity label to its subword tokens and tuning the learning rate, batch size and epochs with a grid search.

## Results

| Dataset | Language | F1 |
| --- | --- | ---: |
| HiNER | Hindi | 0.899 |
| WikiNEuRal | English | 0.946 |

mBERT outperformed the Indic-BERT and XLM-R baselines on both datasets.
