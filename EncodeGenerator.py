import os
import cv2
import face_recognition
import pickle
import face_recognition
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/",
    'storageBucket': "facialrecognition-4bee2.appspot.com"
})


# Importing images

folderPath = 'Images'
pathList = os.listdir(folderPath)
imgList = []
userIds = []
for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath,path)))
    userIds.append(os.path.splitext(path)[0])

    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)


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
