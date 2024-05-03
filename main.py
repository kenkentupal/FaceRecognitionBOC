import os
import pickle
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
cap.set(4, 480)

pygame.mixer.init()

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
    'storageBucket': "facialrecognition-4bee2.appspot.com"
})
bucket = storage.bucket()

# Load background image
imgBackground = cv2.imread('Resources/background.png')

modeType = 0

# Load encoded face data
def loadEncodedData():
    print("Loading Encoded File...")
    with open('scripts/EncodeFile.p', 'rb') as file:
        encodeListKnowsWithIds = pickle.load(file)
    encodeListKnown, userIds = encodeListKnowsWithIds
    print("Encode File Loaded")
    return encodeListKnown, userIds

encodeListKnown, userIds = loadEncodedData()

# Import mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Preload user images from Firebase storage
user_images = {}
for user_id in userIds:
    # Try to download images with different extensions
    for extension in ['png', 'jpg', 'jpeg']:
        blob = bucket.get_blob(f'Images/{user_id}.{extension}')
        if blob:
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            img = cv2.imdecode(array, cv2.IMREAD_COLOR)
            user_images[user_id] = img
            break  # If image is found, break the loop

# Multiprocessing: Generate encoded data in a separate process
def generate_encoded_data_process():
    generateEncodedData()

if __name__ == "__main__":
    generate_data_process = multiprocessing.Process(target=generate_encoded_data_process)
    generate_data_process.start()

    # Variable to keep track of time
    start_time = time.time()

    while True:
        success, img = cap.read()

        # Check if seconds have passed
        if time.time() - start_time >= 10:
            encodeListKnown, userIds = loadEncodedData()  # Reload encoded data
            generateEncodedData()
            start_time = time.time()  # Reset the timer

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        imgBackground[162:162 + 480, 55:55 + 640] = img
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if len(faceCurFrame) == 0:  # Check if no face is detected
            modeType = 0
            imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
        else:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    # Get the person's name
                    id = userIds[matchIndex]
                    userInfo = db.reference(f'Users/{id}').get()
                    fname = str(userInfo['fname'])
                    lname = str(userInfo['lname'])
                    email = str(userInfo['email'])
                    userId = str(userInfo['userId'])
                    faceinfo = str(userInfo['faceinfo'])

                    # Draw the corner rectangle
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                    if str(userInfo['type']) == "Employee":
                        modeType = 2
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                        # Resize and assign imgUser to the appropriate region of interest in imgBackground
                        imgUser = user_images.get(id)
                        if imgUser is not None:
                            imgUserResized = cv2.resize(imgUser, (235, 235))
                            imgBackground[125:125 + 235, 895:895 + 235] = imgUserResized

                        cv2.putText(imgBackground, fname +" "+lname, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                    (255, 255, 255), 1)
                        cv2.putText(imgBackground, email, (bbox[0], bbox[1] - 30), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                    (255, 255, 255), 1)

                        (w, h), _ = cv2.getTextSize(userInfo['fname'] + " " + userInfo['lname'], cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, str(userInfo['fname']) + " " + str(userInfo['lname']), (808 + offset, 423),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                        (w, h), _ = cv2.getTextSize(userInfo['email'], cv2.FONT_HERSHEY_COMPLEX, 0.5, 1)
                        offset = (414 - w) // 2
                        cv2.putText(imgBackground, str(userInfo['email']), (808 + offset, 466),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)


                    elif str(userInfo['type']) == "Traveler":
                        modeType = 1
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                        # Resize and assign imgUser to the appropriate region of interest in imgBackground
                        imgUser = user_images.get(id)
                        if imgUser is not None:
                            imgUserResized = cv2.resize(imgUser, (135, 135))
                            imgBackground[109:109 + 135, 845:845 + 135] = imgUserResized

                            imgUserB = None
                            # Fetch the secondary user image (replace 'second_folder' with the actual folder name)
                        for extension in ['png', 'jpg', 'jpeg']:
                            blob = bucket.get_blob(f'Baggage/{"baggage1" + id}.{extension}')
                            if blob:
                                array = np.frombuffer(blob.download_as_string(), np.uint8)
                                imgUserB = cv2.imdecode(array, cv2.IMREAD_COLOR)
                                imgUserResizedB = cv2.resize(imgUserB, (150, 150))
                                imgBackground[290:290 + 150, 845:845 + 150] = imgUserResizedB
                                break  # If image is found, break the loop
                        else:
                            imgUserB = None  # If no image is found, set imgUserB to None

                        if imgUserB is not None:
                            # Fetch the secondary user image (replace 'second_folder' with the actual folder name)
                            for extension in ['png', 'jpg', 'jpeg']:
                                blob = bucket.get_blob(f'Baggage/{"baggage2" + id}.{extension}')
                                if blob:
                                    array = np.frombuffer(blob.download_as_string(), np.uint8)
                                    imgUserB = cv2.imdecode(array, cv2.IMREAD_COLOR)
                                    imgUserResizedB = cv2.resize(imgUserB, (150, 150))
                                    imgBackground[290:290 + 150, 1030:1030 + 150] = imgUserResizedB
                                    break  # If image is found, break the loop
                            else:
                                imgUserB = None  # If no image is found, set imgUserB to None

                        # Add the person's name at the top of the rectangle
                        cv2.putText(imgBackground, fname + " " + lname, (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                    (255, 255, 255), 1)

                        cv2.putText(imgBackground, str(userInfo['fname']) +" "+str(userInfo['lname']), (1022, 126),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(userInfo['email']), (1022, 166),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                        cv2.putText(imgBackground, str(userInfo['type']), (1022, 201),
                                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

                else:

                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

                    # Draw a red rectangle around the face
                    cv2.rectangle(imgBackground, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]),
                                  (0, 0, 255), 2)

                    # Add text indicating face not recognized
                    cv2.putText(imgBackground, "Unknown", (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                (0, 0, 255),
                                1)

        cv2.imshow("Face Attendance", imgBackground)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Check if the ESC key is pressed (27 is the ASCII code for ESC)
            break

        # Check if the window is still open
        if cv2.getWindowProperty("Face Attendance", cv2.WND_PROP_VISIBLE) < 1:
            break

    # Release the camera and close all windows
    cap.release()
    cv2.destroyAllWindows()
