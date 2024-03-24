import os
import pickle

import cvzone
import numpy as np
import cv2
import face_recognition

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FPS, 60)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)
cap.set(3, 640)
cap.set(4, 480)


imgBackground = cv2.imread('Resources/background.png')

# Load encoded face data
print("Loading Encoded File...")
file = open('scripts/EncodeFile.p', 'rb')
encodeListKnowsWithIds = pickle.load(file)
file.close()
encodeListKnown, userIds = encodeListKnowsWithIds
print("Encode File Loaded")

# Importing the mode images into a list
folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))
#print(len(imgModeList))


while True:
    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[0]


    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            print(userIds[matchIndex])

            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)


    cv2.imshow("Face Attendance", imgBackground)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q'):  # Check if 'q' or 'Q' is pressed
        break

# Release the camera and close all windows
cap.release()
cv2.destroyAllWindows()
