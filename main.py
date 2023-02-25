import uvicorn
from fastapi import FastAPI, Request, UploadFile
from fastapi import Form, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import face_recognition
import numpy as np
import sqlite3

savefile = "temp.jpg"

con = sqlite3.connect("user.db", check_same_thread=False)
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users(email PRIMARY KEY, name, face_map)")
con.commit()

class Register(BaseModel):
    name: str = Form()
    email: str = Form()
    image: UploadFile = File()

templates = Jinja2Templates(directory="templates")

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    users = cur.execute(f"SELECT name,email FROM users;")
    context = users.fetchall()
    return templates.TemplateResponse("index.html", {"request": request,"context":context})

@app.post("/register")
def register_user(name: str = Form(), email: str = Form(), image: UploadFile = File()):
    with open(savefile, "wb+") as file_object:
        file_object.write(image.file.read())
    picture = face_recognition.load_image_file(savefile)
    face_encoding = face_recognition.face_encodings(picture)[0]

    cur.execute("INSERT OR REPLACE into users (email, name, face_map) values (?,?,?)", (email,name,face_encoding.tobytes(),))
    con.commit()
    return {"name":name,"email":email,"image":image}

@app.post("/recognise")
def read_item(email: str = Form(), image: UploadFile = File()):
    with open(savefile, "wb+") as file_object:
        file_object.write(image.file.read())
    picture = face_recognition.load_image_file(savefile)
    new_encoding = face_recognition.face_encodings(picture)[0]

    encoding = cur.execute(f"SELECT face_map,name FROM users WHERE email='{email}';")
    data = encoding.fetchone()
    registered_encoding = np.frombuffer(data[0])

    results = face_recognition.compare_faces([registered_encoding], new_encoding)
    message = ""
    if results[0] == True:
        message = "This is your picture"
    else:
        message = "This is not your picture"
    
    return {"email":email,"name":data[1],"message":message}

@app.post("/del/{email}")
def delete_user(email):
    cur.execute(f"DELETE FROM users WHERE email='{email}';")
    con.commit()
    return {"message":"User Deleted"}

if __name__ == "__main__":
   uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)