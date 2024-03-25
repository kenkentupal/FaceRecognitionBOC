import os
import pickle
import cv2
import numpy as np
import firebase_admin
from firebase_admin import credentials, db, storage
import face_recognition
import cvzone

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
    'storageBucket': "facialrecognition-4bee2.appspot.com"
})
bucket = storage.bucket()

# Initialize Video Capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
cap.set(3, 640)
cap.set(4, 480)

# Load background image
imgBackground = cv2.imread('Resources/background.png')

# Load encoded face data
print("Loading Encoded File...")
with open('scripts/EncodeFile.p', 'rb') as file:
    encodeListKnowsWithIds = pickle.load(file)
encodeListKnown, userIds = encodeListKnowsWithIds
print("Encode File Loaded")

# Import mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]


counter = 0
id = -1
imgUser = []

while True:
    success, img = cap.read()
    if not success:
        continue

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[1]

    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            id = userIds[matchIndex]

            userInfo = db.reference(f'Users/{id}').get()

            # Get Image
            blob = bucket.get_blob(f'Images/{id}.png')
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            imgUser = cv2.imdecode(array, cv2.IMREAD_COLOR)

            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1

            # Draw rectangle
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

            # Add text
            text = f"Name: {userInfo['name']}"
            cv2.putText(imgBackground, text, (bbox[0], bbox[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.putText(imgBackground, str(userInfo['name']), (1022, 126),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(userInfo['idnum']), (1022, 166),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(imgBackground, str(userInfo['last_ent']), (1022, 201),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)

            # Resize imgUser to match the dimensions of the region of interest
            imgUserResized = cv2.resize(imgUser, (135, 135))

            # Assign imgUser to the appropriate region of interest in imgBackground
            imgBackground[109:109 + 135, 845:845 + 135] = imgUserResized


        else:
            userInfo = []
            imgUser = []


    cv2.imshow("Face Attendance", imgBackground)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q'):  # Check if 'q' or 'Q' is pressed
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
