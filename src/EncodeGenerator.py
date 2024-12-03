import os
import sys
import cv2
import face_recognition
import pickle
import numpy as np
from tqdm import tqdm

# Set a higher recursion limit
sys.setrecursionlimit(4000)

def load_existing_encodings():
    if os.path.exists("../data/EncodeFile.p"):
        try:
            with open("../data/EncodeFile.p", 'rb') as file:
                encodeListKnownWithIds = pickle.load(file)
                return encodeListKnownWithIds[0], encodeListKnownWithIds[1]
        except Exception as e:
            print(f"Error loading encodings: {e}")
            return [], []
    return [], []

def load_local_images(image_path):
    imgList = []
    try:
        img = cv2.imread(image_path)
        if img is not None:
            imgList.append(img)
        else:
            print(f"Error reading image from {image_path}")
    except Exception as e:
        print(f"Error loading image from {image_path}: {e}")
    return imgList

def resize_images(imagesList, width=800):
    resized_images = []
    for img in imagesList:
        try:
            height = int((width / img.shape[1]) * img.shape[0])
            resized_img = cv2.resize(img, (width, height))
            resized_images.append(resized_img)
        except Exception as e:
            print(f"Error resizing image: {e}")
    return resized_images

def find_encodings(imagesList):
    encodeList = []
    for img in tqdm(imagesList, desc="Encoding faces", unit=" face"):
        try:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodes = face_recognition.face_encodings(img)
            if encodes:
                encodeList.append(encodes[0])
            else:
                print("No face found in the image")
        except Exception as e:
            print(f"Error encoding face: {e}")
    return encodeList

def generateEncodedData():
    try:
        # Ensure the 'data' directory exists
        if not os.path.exists("../data"):
            os.makedirs("../data")

        # Load existing encodings
        encodeListKnown, userIds = load_existing_encodings()

        # Define the path to the local image
        image_path = "../capture/face_capture.png"

        # Load the local image
        imgList = load_local_images(image_path)

        if not imgList:
            print("No valid images found for encoding.")
            return

        # Resize the images
        imgList = resize_images(imgList)

        # Encode the new image
        encodeListKnown.extend(find_encodings(imgList))
        userIds.extend(["new_user"])  # Here, you might want to generate a unique user ID or use a known one

        print("Encoding Finished")

        # Save the newly encoded data
        print("Saving encoded data to file...")
        with open("../data/EncodeFile.p", 'wb') as file:
            pickle.dump([encodeListKnown, userIds], file)
        print("Encoded data saved to file.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generateEncodedData()
