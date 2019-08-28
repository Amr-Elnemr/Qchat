import os
from datetime import datetime
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
from flask_session import Session

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(12)
socketio = SocketIO(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = True #False: don't remember me when I close the browser
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Globals:
freshApp = True
chats = {
    # 'Sample_Chat':[
    #     {'person':"Amr",'text':"How are u?", 'time':"02.08.2019, 11:00:26"},
    #     {'person':"Ali",'text':"fine, thanks", 'time':"02.08.2019, 11:00:31"}
    # ]
}

@app.route("/")
def index():
    global freshApp
    if (freshApp):
        session["current_room"] = None
        freshApp = False
    if session.get("username") is None:
        return render_template("Login.html")
    else:
        if (session.get("current_room") is None):
            return render_template("Home.html", username=session["username"], ch_conflict = False)
        return render_template("Chatroom.html", roomName=session.get("current_room"), history=chats[session.get("current_room")],userName=session.get("username"))

@app.route("/Home", methods = ["GET", "POST"])
def home():
    if (request.method == "GET"):
        return render_template("Home.html", username=session["username"], ch_conflict = False)
    session["username"] = request.form.get("disname")
    return render_template("Home.html", username=session["username"], ch_conflict = False)


@app.route("/Chatrooms")
def show_chatrooms():
    if session.get("username") is None:
        return redirect(url_for('index'))
    global chats
    return render_template("Rooms.html", rooms = list(chats.keys()))

@app.route("/Join_chatroom/<string:roomName>")
def join_chatroom(roomName):
    global chats
    if session.get("username") is None:
        return redirect(url_for('index'))
    if (roomName not in list(chats.keys())):
        return ("Sorry this chat room doesn't exist, but you can <a href='http://127.0.0.1:5000/Home'><b>create one</b></a>")
    session["current_room"] = roomName
    return render_template("Chatroom.html", roomName = roomName, history = chats[roomName], userName = session.get("username"))

@app.route("/Create_chatroom", methods=["POST"])
def create_chatroom():
    global chats
    if session.get("username") is None:
        return redirect(url_for('index'))
    roomName = request.form.get('chatname')
    if(roomName in list(chats.keys())):
        return jsonify({"success":False})
    chats[roomName] = []
    session["current_room"] = roomName
    return jsonify({"success": True})


# @app.route("/Chat/<string:roomName>", methods=["POST"])
# def chat(roomName):
#     global chats
#     if session.get("username") is None:
#         return redirect(url_for('index'))
#     chats[roomName].append({
#         'person':session.get("username"),
#         'text':request.form.get('tosend'),
#         'time':datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
#     })
#     return render_template("Chatroom.html", roomName = roomName, history = chats[roomName], userName = session.get("username"))

@socketio.on("send")
def send(data):
    global chats
    chats[data['roomName']].append({
        'person': session.get("username"),
        'text': data['inst_msg'],
        'time': datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
    })
    emit("update_room" + data['roomName'], chats[data['roomName']], broadcast = True)


if __name__ == '__main__':
    app.run(debug=True)