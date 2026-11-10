---
title: Wordle in the terminal
date: 2026-03
category: practice
repository: wordle-tui
private: true
skills: [cli-tui, testing, python]

summary: >-
  A terminal word-guessing game with coloured feedback, an on-screen keyboard, three difficulty
  levels and the answer's definition after each game.
status: Complete
---

## What it is

A terminal version of the five-letter word-guessing game: six guesses, with each letter marked correct, present in the wrong place, or absent.

## How it works

- **Game logic** with no input or output code, so it is easy to test. The trickiest part, scoring a guess when a letter appears more than once in the guess or the answer, is covered by unit tests.
- **Display** with Rich: the coloured guess grid and an on-screen keyboard that tracks used letters.
- **Validation** of every guess against a list of accepted five-letter words.
- **Difficulty levels** with separate answer pools, rebuilt by a script.
- **Definitions** of the answer after each game, from the free Dictionary API.
