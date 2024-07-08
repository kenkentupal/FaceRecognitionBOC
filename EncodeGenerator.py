import os
import sys
import cv2
import face_recognition
import pickle
import firebase_admin
import numpy as np
from firebase_admin import credentials, storage
from tqdm import tqdm

# Set a higher recursion limit
sys.setrecursionlimit(4000)

def initialize_firebase():
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
                'storageBucket': "facialrecognition-4bee2.appspot.com"
            })
    except Exception as e:
        print(f"Error initializing Firebase: {e}")

def load_existing_encodings():
    if os.path.exists("scripts/EncodeFile.p"):
        try:
            with open("scripts/EncodeFile.p", 'rb') as file:
                encodeListKnownWithIds = pickle.load(file)
                return encodeListKnownWithIds[0], encodeListKnownWithIds[1]
        except Exception as e:
            print(f"Error loading encodings: {e}")
            return [], []
    return [], []

def download_images(blobs, new_user_ids):
    imgList = []
    for blob in tqdm(blobs, desc="Downloading new images", unit=" image"):
        filename = blob.name
        user_id = filename.split('/')[-1].split('.')[0]
        if user_id in new_user_ids:
            try:
                img_data = blob.download_as_string()
                img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    imgList.append(img)
                else:
                    print(f"Error decoding image for user ID: {user_id}")
            except Exception as e:
                print(f"Error downloading image for user ID: {user_id}, error: {e}")
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
        #print("Initializing Firebase...")
        initialize_firebase()
        bucket = storage.bucket()

        #print("Loading existing encodings...")
        encodeListKnown, userIds = load_existing_encodings()

        #print("Retrieving image list from Firebase Storage...")
        blobs = list(bucket.list_blobs(prefix='Passport/'))

        current_user_ids = [blob.name.split('/')[-1].split('.')[0] for blob in blobs]

        #print("Identifying deleted user IDs...")
        deleted_user_ids = [user_id for user_id in userIds if user_id not in current_user_ids]
        if deleted_user_ids:
            print("Deleted user IDs:")
            for user_id in deleted_user_ids:
                print(user_id)


        valid_indices = [i for i, user_id in enumerate(userIds) if user_id in current_user_ids]
        encodeListKnown = [encodeListKnown[i] for i in valid_indices]
        userIds = [userIds[i] for i in valid_indices]

        new_user_ids = [user_id for user_id in current_user_ids if user_id not in userIds]

        if not new_user_ids:
            #print("No new images to encode.")
            with open("scripts/EncodeFile.p", 'wb') as file:
                pickle.dump([encodeListKnown, userIds], file)
            #print("Updated encoded data saved to file.")
            return

        print("Downloading new images...")
        imgList = download_images(blobs, new_user_ids)

        if not imgList:
            print("No valid images found for encoding.")
            return

        #print("Resizing images...")
        imgList = resize_images(imgList)

        #print("Encoding new images...")
        encodeListKnown.extend(find_encodings(imgList))
        userIds.extend(new_user_ids)
        print("Encoding Finished")

        print("Newly encoded files:")
        for user_id in new_user_ids:
            print(f"{user_id}")

        print("Saving encoded data to file...")
        with open("scripts/EncodeFile.p", 'wb') as file:
            pickle.dump([encodeListKnown, userIds], file)
        print("Encoded data saved to file.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generateEncodedData()
