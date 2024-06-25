import os
import pickle
import subprocess

import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, db, storage
import face_recognition
import cvzone
import pygame
import multiprocessing
import time
from EncodeGenerator import generateEncodedData

# Enable OpenCL acceleration for OpenCV
cv2.ocl.setUseOpenCL(True)

# Load the Haar cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Initialize Video Capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
cap.set(3, 640)
cap.set(4, 360)

pygame.mixer.init()

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
    'storageBucket': "facialrecognition-4bee2.appspot.com"
})
bucket = storage.bucket()

# Load background image
imgBackground = cv2.imread('Resources/background2.png')

modeType = 0

# Load encoded face data
def loadEncodedData():
    try:
        print("Loading Encoded File...")
        with open('scripts/EncodeFile.p', 'rb') as file:
            encodeListKnowsWithIds = pickle.load(file)
        encodeListKnown, userIds = encodeListKnowsWithIds
        print("Encode File Loaded")
        return encodeListKnown, userIds
    except FileNotFoundError:
        print("Encoded file not found. Ensure EncodeFile.p exists in the scripts directory.")
        return [], []
    except pickle.UnpicklingError:
        print("Error loading encoded data. Check if EncodeFile.p is a valid pickle file.")
        return [], []

encodeListKnown, userIds = loadEncodedData()

# Import mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]

# Preload user images from Firebase storage
user_images = {}
for user_id in userIds:
    image_found = False
    for extension in ['png', 'jpg', 'jpeg']:
        blob = bucket.get_blob(f'Images/{user_id}.{extension}')
        if blob:
            try:
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                img = cv2.imdecode(array, cv2.IMREAD_COLOR)
                user_images[user_id] = img
                image_found = True
                break
            except Exception as e:
                print(f"Error decoding image for user {user_id}: {e}")

    if not image_found:
        print(f"No image found for user {user_id}")
def reload_encoded_data(queue):
    while True:
        time.sleep(10)  # Wait for 10 seconds
        encodeListKnown, userIds = loadEncodedData()
        generateEncodedData()
        queue.put((encodeListKnown, userIds))
        print("Encoded data reloaded")



if __name__ == "__main__":
    # Create a queue to share data between processes
    queue = multiprocessing.Queue()

    # Start the process to reload encoded data periodically
    reload_process = multiprocessing.Process(target=reload_encoded_data, args=(queue,))
    reload_process.daemon = True
    reload_process.start()

    while True:
        success, img = cap.read()

        # Check if there is updated encoded data in the queue
        if not queue.empty():
            encodeListKnown, userIds = queue.get()

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)


        imgBackground[162:162 + 360, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if len(faceCurFrame) == 0:
            modeType = 0
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        else:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                # Ensure a stricter threshold for accuracy
                if matches[matchIndex] and faceDis[matchIndex] < 0.4:  # Lower threshold means stricter match
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    id = userIds[matchIndex]
                    userInfo = db.reference(f'Users/{id}').get()
                    fname = str(userInfo['fname'])
                    lname = str(userInfo['lname'])
                    email = str(userInfo['email'])
                    userId = str(userInfo['userId'])
                    faceinfo = str(userInfo['faceinfo'])

                    (w, h), _ = cv2.getTextSize(userInfo['fname'] + " " + userInfo['lname'], cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(userInfo['fname']) + " " + str(userInfo['lname']), (808 + offset, 423), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                    modeType = 2
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                    imgUser = user_images.get(id)
                    if imgUser is not None:
                        imgUserResized = cv2.resize(imgUser, (235, 235))
                        imgBackground[125:125 + 235, 895:895 + 235] = imgUserResized

                    cv2.putText(imgBackground, fname + " " + lname, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    (w, h), _ = cv2.getTextSize(userInfo['email'], cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(userInfo['email']), (808 + offset, 466), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                    process = subprocess.Popen(['python', 'gate_arduino.py'])
                    time.sleep(1)
                    process.terminate()


                else:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    cv2.rectangle(imgBackground, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 0, 255), 2)
                    cv2.putText(imgBackground, "Unknown", (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)

        cv2.imshow("Face Attendance", imgBackground)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key
            break

        if cv2.getWindowProperty("Face Attendance", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
