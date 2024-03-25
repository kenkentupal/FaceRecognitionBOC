import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : "https://facialrecognition-4bee2-default-rtdb.firebaseio.com/"
})

ref = db.reference('Users')


data = {
    "123124":
        {
            "name": "Elon Musk",
            "idnum": "123124",
            "last_ent": "2022-03-25 00:54:34"
        },
    "123456":
        {
            "name": "Ken Tupal",
            "idnum": "123456",
            "last_ent": "2022-03-25 00:54:34"
        }

}

for key,value in data.items():
    ref.child(key).set(value)

