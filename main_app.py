from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

# Store users in a dictionary with their random user IDs
users = {}

# Generate a random user ID
def generate_user_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    user_id = generate_user_id()
    users[request.sid] = user_id
    emit('user_id', user_id)

@socketio.on('message')
def handle_message(msg):
    user_id = users.get(request.sid, 'Unknown')
    formatted_message = f'User {user_id}: {msg}'
    send(formatted_message, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        del users[request.sid]


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)