import cv2
import pickle
import numpy as np
from facenet_pytorch import MTCNN
import torch
from scipy.spatial.distance import cosine

# Setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
mtcnn = MTCNN(keep_all=True, device=device)

# Load the saved encoding from the encodefile.p
with open(r'../capture/encodefile.p', 'rb') as f:
    saved_encoding = pickle.load(f)

# Load the face_capture.png image
face_image = cv2.imread(r'../capture/img.png')
face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

# Detect the face in the image and get encoding
boxes, _ = mtcnn.detect(face_rgb)
if boxes is not None and len(boxes) > 0:
    # Crop the detected face
    cropped_face = face_rgb[int(boxes[0][1]):int(boxes[0][3]), int(boxes[0][0]):int(boxes[0][2])]

    # Get the face encoding
    encoding = mtcnn(cropped_face)[0].cpu().detach().numpy()

    # Compare the two encodings using cosine similarity
    similarity = 1 - cosine(saved_encoding.flatten(), encoding.flatten())

    print(f"Cosine Similarity between saved encoding and captured face: {similarity:.4f}")
else:
    print("No face detected in the captured image.")
