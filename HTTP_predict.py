import io
import json
import redis
import torch
from torchvision import models, transforms
from PIL import Image
import requests
from torchvision.models import inception_v3, Inception_V3_Weights

# Initialize a Redis connection.
r = redis.Redis()

# Load the pre-trained Inception V3 model with the updated method.
model = inception_v3(weights=Inception_V3_Weights.IMAGENET1K_V1)
model.eval()

# Define the transformation to preprocess the input image.
preprocess = transforms.Compose([
    transforms.Resize(299),
    transforms.CenterCrop(299),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def load_imagenet_labels():
    labels_url = 'https://storage.googleapis.com/download.tensorflow.org/data/ImageNetLabels.txt'
    response = requests.get(labels_url)
    if response.status_code != 200:
        print("Failed to download ImageNet labels.")
    labels = [line.strip() for line in response.text.split('\n') if line][1:]
    return labels

# Load the ImageNet labels.
imagenet_labels = load_imagenet_labels()

def preprocess_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        preprocessed_image = preprocess(image)
        return preprocessed_image.unsqueeze(0)  # Add a batch dimension.
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def generate_predictions(image):
    with torch.no_grad():
        output = model(image)
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top5_prob, top5_catid = torch.topk(probabilities, 5)
        top5_labels = [imagenet_labels[catid] for catid in top5_catid.tolist()]
        return top5_prob.tolist(), top5_labels

def continuously_receive_messages():
    while True:
        try:
            print("Waiting for image URL...")
            _, message = r.brpop("download")
            data = json.loads(message)
            print(f"Received message for processing: {data}")

            url = data["url"]
            task_id = data["task_id"]
            timestamp = data["timestamp"]
            print(f"Processing image from URL: {url}")

            # Fetch the image from the URL to process
            response = requests.get(url)
            if response.status_code == 200:
                image_bytes = response.content
                preprocessed_image = preprocess_image(image_bytes)
                if preprocessed_image is not None:
                    top5_prob, top5_labels = generate_predictions(preprocessed_image)
                    predictions = [{"label": label, "probability": prob} for label, prob in zip(top5_labels, top5_prob)]
                    result_message = {
                        "task_id": task_id,
                        "timestamp": timestamp,
                        "url": url,
                        "predictions": predictions
                    }
                    print(f"Generated result_message: {result_message}")
                    r.lpush("prediction", json.dumps(result_message))
                else:
                    print("Failed to preprocess image.")
            else:
                print(f"Failed to download image at URL: {url} with status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred during message processing: {e}")

if __name__ == "__main__":
    continuously_receive_messages()
