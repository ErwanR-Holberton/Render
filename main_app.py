from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import random
import string, os
import mysql.connector
from datetime import date

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('MYSQLHOST'),
        user=os.getenv('MYSQLUSER'),
        password=os.getenv('MYSQLPASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )
    return conn

def add_message(username, content):
    message_date = date.today()  # Use current date
    
    # Insert the message into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO messages (username, content, date)
    VALUES (%s, %s, %s)
    """
    values = (username, content, message_date)
    
    try:
        cursor.execute(query, values)
        conn.commit()
        return jsonify({'message': 'Message added successfully!'}), 201
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({'error': 'Failed to add message'}), 500
    finally:
        cursor.close()
        conn.close()

# Store users in a dictionary with their random user IDs
users = {}

# Generate a random user ID
def generate_user_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

@app.route('/')
def index():
    print("test")
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    user_id = generate_user_id()
    print("someone connected", user_id)
    users[request.sid] = user_id
    emit('user_id', user_id)

@socketio.on('message')
def handle_message(msg):
    user_id = users.get(request.sid, 'Unknown')
    formatted_message = f'User {user_id}: {msg}'
    add_message(user_id, msg)
    print(f'Message received: {formatted_message}')  # Debugging log
    send(formatted_message, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print("someone connected", request.sid)
    if request.sid in users:
        del users[request.sid]

@app.route('/messages')
def show_messages():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all messages
    query = "SELECT * FROM messages ORDER BY date DESC"
    cursor.execute(query)
    messages = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Render the template and pass the messages to it
    return render_template('messages.html', messages=messages)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True, allow_unsafe_werkzeug=True)