## What it does

A small end-to-end machine-learning app: upload an image of a handwritten digit in the browser, see a preview, and get the model's prediction back.

## How it works

- **Model:** a scikit-learn Random Forest trained on the 60,000 MNIST training images (loaded through Keras) and scored on the 10,000 test images, then saved to disk.
- **API:** a FastAPI endpoint, `/predict-image/`, accepts an uploaded image, converts it to a 28×28 grayscale array with Pillow, and returns the predicted digit.
- **Front end:** a single HTML page with a little JavaScript for uploading, previewing and showing the result.
- **Sample images** of each digit are included for trying it out.
