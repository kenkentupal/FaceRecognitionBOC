import os
import sys
import cv2
import torch
import pickle
import firebase_admin
import numpy as np
from firebase_admin import credentials, storage
from tqdm import tqdm
from facenet_pytorch import InceptionResnetV1

# Set a higher recursion limit
sys.setrecursionlimit(4000)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
facenet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

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
    if os.path.exists("../data/EncodeFile.p"):
        try:
            with open("../data/EncodeFile.p", 'rb') as file:
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
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_rgb_tensor = torch.tensor(img_rgb).permute(2, 0, 1).unsqueeze(0).float().to(device)
            encodes = facenet(img_rgb_tensor).detach().cpu().numpy().flatten()
            if encodes is not None:
                encodeList.append(encodes)
            else:
                print("No face found in the image")
        except Exception as e:
            print(f"Error encoding face: {e}")
    return encodeList

def delete_images_with_underscore_and_dash():
    try:
        bucket = storage.bucket()
        blobs = bucket.list_blobs()
        for blob in blobs:
            if '_' in blob.name or '-' in blob.name:
                try:
                    blob.delete()
                    # Print only if the image is successfully deleted
                    print(f"Successfully deleted: {blob.name}")
                except Exception as e:
                    print(f"Error deleting image {blob.name}: {e}")
    except Exception as e:
        print(f"An error occurred while deleting images: {e}")

def generateEncodedData():
    try:
        #print("Initializing Firebase...")
        initialize_firebase()
        bucket = storage.bucket()

        # Delete images with underscores or dashes
        delete_images_with_underscore_and_dash()

        # Ensure the 'data' directory exists
        if not os.path.exists("../data"):
            os.makedirs("../data")

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
            with open("../data/EncodeFile.p", 'wb') as file:
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
        with open("../data/EncodeFile.p", 'wb') as file:
            pickle.dump([encodeListKnown, userIds], file)
        print("Encoded data saved to file.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generateEncodedData()
