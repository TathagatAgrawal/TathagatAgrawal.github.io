---
title: Multilingual NER with mBERT
date: 2023-12
category: llm
skills: [ner, fine-tuning, hugging-face, pytorch, nlp, python]
links:
  - label: Paper (ICCCNT 2024)
    url: https://ieeexplore.ieee.org/document/10724051

summary: >-
  Fine-tuned multilingual BERT for Hindi and English named entity recognition, ahead of
  Indic-BERT and XLM-R baselines. Published at ICCCNT 2024.
result: F1 of 0.899 on HiNER (Hindi) and 0.946 on WikiNEuRal (English).
status: Published

resume:
  tech: PyTorch, HuggingFace, Fine-tuning, NLP
  link:
    label: Paper link
    url: https://ieeexplore.ieee.org/document/10724051
  bullets:
    - Fine-tuned the bert-base-multilingual-cased model for Named Entity Recognition for Hindi (HiNER) and English (WikiNEuRal).
    - Pre-processed datasets via subword tokenization and aligned entity annotations to token IDs. Conducted hyperparameter-tuning using grid search to obtain optimal performance.
    - Achieved F1 = 0.899 (HiNER) and F1 = 0.946 (WikiNEuRal), outperforming Indic-BERT and XLM-R baselines (see publication \[3\]).
  short: mBERT fine-tuned for Hindi and English NER (F1 0.899 and 0.946)
---

## The problem

Named entity recognition (finding names of people, places, organisations and so on in text) is well served for English, but much less so for Hindi, which has fewer labelled datasets. The question was whether a single multilingual model, fine-tuned per language, could match or beat models built for Indian languages.

## What I did

- Fine-tuned `bert-base-multilingual-cased` separately on HiNER (Hindi) and WikiNEuRal (English).
- Tokenised text into subwords and aligned each word's entity label to its subword tokens, so labels stay correct when a word is split.
- Tuned learning rate, batch size and epochs with a grid search.
- Compared against Indic-BERT and XLM-R baselines.

## Result

| Dataset | Language | F1 |
| --- | --- | ---: |
| HiNER | Hindi | 0.899 |
| WikiNEuRal | English | 0.946 |

mBERT outperformed the Indic-BERT and XLM-R baselines on both. The work was published at ICCCNT 2024 ([paper](https://ieeexplore.ieee.org/document/10724051)).
