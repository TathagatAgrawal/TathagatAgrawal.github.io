---
title: AI lead scoring (data preparation)
date: 2025-07
category: ml
repository: ai_lead_scoring_engine
private: true
skills: [data-cleaning, pandas, python]

summary: >-
  The data-cleaning stage of a lead-scoring model for an online education company: preparing
  website-behaviour and lead-source data to predict which leads will convert.
status: Data preparation done; model not built
---

## The problem

An online education company (the "X Education" case study dataset) converts about 30% of its leads into paying customers. Lead scoring would rank new leads by how likely they are to convert, so the sales team can focus on the most promising ones.

## What is done

- A write-up of how AI lead scoring works: data collection, cleaning and feature engineering, modelling, scoring on a 0–100 scale, and continuous learning.
- A documented data dictionary for the dataset's demographic, behavioural and engagement variables (lead source, visits, time on site, last activity and so on).
- A data-cleaning notebook: filling small gaps in numeric columns, dropping columns that are more than 40% empty, merging duplicate categories (such as "Google" and "google"), adding an "Others" lead source for missing values, and dropping columns that carry almost no information.

## Status

The model itself has not been built yet.
