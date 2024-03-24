import os

import cv2
import face_recognition
import pickle


# Importing images

folderPath = 'Images'
pathList = os.listdir(folderPath)
imgList = []
userIds = []
for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath,path)))
    userIds.append(os.path.splitext(path)[0])
print(userIds)


def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

print("Encoding Started...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown,userIds]
print("Encoding Fininsh...")

file = open("scripts/EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds,file)
file.close()
print("File Saved")
