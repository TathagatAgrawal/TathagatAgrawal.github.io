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
