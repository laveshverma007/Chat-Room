from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_socketio import join_room, leave_room, send, SocketIO
from werkzeug.utils import secure_filename
from flask_socketio import emit
import os
import random
from string import ascii_uppercase
import time
import socket
import pyttsx3
from langdetect import detect
from translate import Translator
import os
import smtplib
from email.message import EmailMessage




app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "./uploads"
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:
            break

    return code


@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name1 = request.form.get("name1")
        name2 = request.form.get("name2")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name1:
            return render_template(
                "home.html",
                error="Please enter first name.",
                code=code if code != None else "",
            )
        if not name2:
            return render_template(
                "home.html",
                error="Please enter second name.",
                code=code if code != None else "",
                name1=name1,
            )
        if join != False and not code:
            return render_template(
                "home.html",
                error="Please enter a room code.",
                code=code if code != None else "",
                name1=name1,
                name2=name2,
            )

        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template(
                "home.html", error="Room does not exist.", code=code, name=name1
            )

        session["room"] = room
        session["name"] = name1 + " " + name2
        return redirect(url_for("room"))

    return render_template("home.html")


language = {"tolang": "en", "flang": "en"}
def get_local_ip_address():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address

ip_address = get_local_ip_address()

@app.route("/room", methods=["POST", "GET"])
def room():
    recipient_list = ["sprshtndn@gmail.com"]
    
    room = session.get("room")
    name = session.get("name")
    if request.method == "POST":
        data = request.get_json()
        # print(data.get("toLang"))
        language["tolang"] = data.get("toLang")
        recipient_list.append(data.get("recipient"))
    email_id = 'llounge649@gmail.com'
    email_pass = 'inpmaibuaaozjuig'

    print(recipient_list)
    print(language["tolang"])


    msg = EmailMessage()
    msg['Subject'] = "Meeting Code"
    msg['From'] = email_id
    msg['To'] = recipient_list
    links = f"http://{get_local_ip_address()}:3000/"
    msg.set_content(f"Join the room with the code {room} \nHere is the link - {links}")


    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_id, email_pass)
        smtp.send_message(msg)
    # print(request.form.get("inputlang"))
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])



@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        room = session.get("room")
        name = session.get("name")
        file = request.files["file"]
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            # emit('file_uploaded', room=room)
            url = f"http://{get_local_ip_address()}:1234/{filename}"
            # url = slugify(url)
            # url = urllib.parse.quote_plus(url)
            content = {
                "name": name,
                "message": url,
            }
            rooms[room]["messages"].append(content)
            return redirect(url_for("room"))
    return "No file selected"


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    lang = detect(data["data"])
    # print(lang)
    translator = Translator(from_lang=lang, to_lang=language["tolang"])
    # output = translator.translate(t_sentence, dest=language)
    output = translator.translate(data["data"])

    content = {"name": session.get("name"), "message": output , }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    # print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    # print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
    if socketio.connected:
        room = session.get("room")
        name = session.get("name")
        leave_room(room)

        if room in rooms:
            rooms[room]["members"] -= 1
            if rooms[room]["members"] <= 0:
                del rooms[room]

        send({"name": name, "message": "has left the room"}, to=room)
        # print(f"{name} has left the room {room}")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=3000, debug=True)
