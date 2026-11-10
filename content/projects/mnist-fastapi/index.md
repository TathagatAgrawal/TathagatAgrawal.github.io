---
title: Handwritten digit recognition web app
date: 2025-08
category: ml
repository: mnist_fastapi_classifier
skills: [scikit-learn, fastapi, web-frontend, javascript, python]

summary: >-
  Upload a picture of a handwritten digit and a model trained on MNIST tells you which digit it
  is, served through a FastAPI backend and a small web page.
status: Complete

resume:
  title: MNIST FastAPI Classifier
  tech: FastAPI, scikit-learn, Pillow, Keras, TensorFlow, Uvicorn, HTML5, JavaScript
  bullets:
    - Developed an end-to-end digit classification web app using FastAPI (Python backend) and a minimal HTML/JavaScript frontend.
    - Trained a Random Forest classifier on the MNIST dataset, achieving over 97% test accuracy for handwritten digit recognition.
    - Implemented image preprocessing and resizing with Pillow to ensure compatibility with model input requirements.
    - Integrated RESTful API for real-time image upload, preview, and prediction, leveraging scikit-learn, FastAPI, and Keras for efficient deployment.
  short: FastAPI digit-recognition app with a Random Forest trained on MNIST
---

## What it does

A small end-to-end machine-learning app: upload an image of a handwritten digit in the browser, see a preview, and get the model's prediction back.

## How it works

- **Model:** a scikit-learn Random Forest trained on the 60,000 MNIST training images (loaded through Keras) and scored on the 10,000 test images, then saved to disk.
- **API:** a FastAPI endpoint, `/predict-image/`, accepts an uploaded image, converts it to a 28×28 grayscale array with Pillow, and returns the predicted digit.
- **Front end:** a single HTML page with a little JavaScript for uploading, previewing and showing the result.
- **Sample images** of each digit are included for trying it out.
