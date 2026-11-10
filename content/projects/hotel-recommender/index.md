---
title: Hotel recommendation system
date: 2022-01
category: ml
repository: hotel_recommendation_system
skills: [nlp, pandas, data-cleaning, python]

summary: >-
  Describe your trip in plain words and get the ten European hotels whose guest reviews best
  match it, using 515,000 reviews of 1,493 hotels.
status: Complete

resume:
  title: Hotel Recommendation System
  tech: Python, pandas, NLTK
  bullets:
    - Built a content-based hotel recommender over 515,000 reviews of 1,493 European hotels that matches a natural-language trip description to hotels' aggregated review tags.
    - Used NLTK preprocessing (tokenization, stop-word removal, lemmatization) and a transparent set-intersection similarity for fast, explainable recommendations.
  short: content-based hotel recommender over 515,000 reviews
---

## What it does

You pick a country and describe the trip you're planning in plain words. The recommender returns the ten hotels whose guests' review tags best match your description.

## How it works

- **Data:** 515,000 reviews of 1,493 hotels across six European countries, from a public Kaggle dataset. Each review carries tags such as "Business trip" or "Family with young children".
- **Preprocessing:** countries are extracted from hotel addresses, review tags are gathered per hotel, and text is lower-cased, tokenised, stripped of stop words and lemmatised with NLTK.
- **Matching:** the description goes through the same preprocessing, and hotels in the chosen country are ranked by how many words their tags share with it (a simple set intersection).

The method is deliberately simple: it is fast, needs no training, and every recommendation can be explained by the tags it matched.
