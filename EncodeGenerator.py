import os
import cv2
import face_recognition
import pickle
import firebase_admin
import numpy as np
from firebase_admin import credentials
from firebase_admin import storage
from tqdm import tqdm  # Import tqdm for the loading screen


def generateEncodedData():
    # Initialize Firebase
    cred = credentials.Certificate("serviceAccountKey.json")

    bucket = storage.bucket()

    # Get the last modified time of the 'Images' folder
    blobs = list(bucket.list_blobs(prefix='Images/'))
    last_modified_time = max(blob.updated for blob in blobs)

    # Check if the encoded data file exists
    if os.path.exists("scripts/EncodeFile.p"):
        # If the file exists, check if it's older than the last modified time of the images
        encode_file_time = os.path.getmtime("scripts/EncodeFile.p")
        if encode_file_time >= last_modified_time.timestamp():
            # If the encoded data file is up to date, load the data from the file
            print("Encoded data file is up to date. Loading...")
            with open("scripts/EncodeFile.p", 'rb') as file:
                encodeListKnownWithIds = pickle.load(file)
                encodeListKnown, userIds = encodeListKnownWithIds
            return

    # If the encoded data file doesn't exist or is outdated, process images
    print("New account found. Encoding images...")
    # Retrieve a list of all files in the 'Images' folder in Firebase Storage
    imgList = []
    userIds = []
    for blob in tqdm(blobs, desc="Downloading images", unit=" image"):
        # Get the file name (e.g., 'Images/user1.png')
        filename = blob.name
        # Extract the user ID from the file name (e.g., 'user1')
        user_id = filename.split('/')[-1].split('.')[0]
        # Download the image data from Firebase Storage
        img_data = blob.download_as_string()
        # Decode the image data into an OpenCV image
        img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
        # Append the image and user ID to their respective lists
        imgList.append(img)
        userIds.append(user_id)

    # Define a function to encode faces
    def findEncodings(imagesList):
        encodeList = []
        for img in tqdm(imagesList, desc="Encoding faces", unit=" face"):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList

    # Encode faces
    print("Encoding Started...")
    encodeListKnown = findEncodings(imgList)
    print("Encoding Finished")

    # Print all newly encoded files
    print("Newly encoded files:")
    for idx, user_id in enumerate(userIds):
        print(f"{user_id}")

    # Save encoded faces to a pickle file
    encodeListKnownWithIds = [encodeListKnown, userIds]
    with open("scripts/EncodeFile.p", 'wb') as file:
        pickle.dump(encodeListKnownWithIds, file)
    print("Encoded data saved to file.")



# Call the function to generate encoded data when the script is run directly
if __name__ == "__main__":
    generateEncodedData()
