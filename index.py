import sqlite3
from flask import Flask, request, redirect, url_for, Response, send_from_directory, jsonify
import pandas as pd
import os
import csv
from flask_cors import CORS
from datetime import datetime
from twilio.rest import Client
import time

app = Flask(__name__, static_folder='../client/build', static_url_path='/')
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
# account_sid = os.environ["TWILIO_ACCOUNT_SID"]
# auth_token = os.environ["TWILIO_AUTH_TOKEN"]
AUDIO_FOLDER = 'audio'
CLIENT_PHONE_MAPPING_FILE = 'clients_list.csv'  # New mapping file

# Ensure the audio folder and uploads folder exist
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']


TWILIO_PHONE_NUMBER = '+12513206365'


def init_db():
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id TEXT PRIMARY KEY,
            client_id TEXT,
            client_name TEXT,
            phone_number TEXT,
            date TEXT,
            time TEXT,
            recording_url TEXT,
            call_status TEXT,
            speech_text TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unsuccessful_calls (
            id TEXT PRIMARY KEY,
            client_id TEXT,
            client_name TEXT,
            phone_number TEXT,
            speech_text TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Function to save call recording details to SQLite database
def save_call_recording(call_sid, client_id, client_name, phone_number, speech_text):
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    cursor.execute('''
        INSERT INTO calls (id, client_id, client_name, phone_number, date, time, recording_url, call_status, speech_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (call_sid, client_id, client_name, phone_number, current_date, current_time, "", "", speech_text))
    conn.commit()
    conn.close()


# Function to generate speech text from trade details
def generate_trade_text(trade):
    instrument = trade['Instrument Type']
    action = 'Bought' if float(trade['Net Qty']) > 0 else 'Sold'
    net_quantity = abs(float(trade['Net Qty']))
    net_price = float(trade['Net Price'])
    scrip = trade['Symbol']
    
    if instrument == 'Equities':
        return f"{action} {net_quantity} shares of {scrip} at {net_price}"
    elif instrument == 'Options':
        option_type = 'call' if trade['Option Type'] == 'CE' else 'put'
        strike_price = trade['Strike Price']
        expiry = trade['Ser/Exp']
        return f"{action} {net_quantity} {option_type} contracts at {net_price} of {strike_price} strike price expiring on {expiry}"
    elif instrument == 'Futures':
        expiry = trade['Ser/Exp']
        return f"{action} {net_quantity} future contracts at {net_price} expiring on {expiry}"
    else:
        return ""

# Function to simulate placing a call and return a dummy recording URL
def place_call(client_id, client_name, to_number, speech_text):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    recording_status_callback_url = url_for('handle_recording_status', _external=True)
    status_callback_url = url_for('handle_callback', _external=True)
    response_xml = f"""
    <Response>
        <Say language="en-IN" voice="Alice">{speech_text}</Say>
        <Pause length="5"/>
    </Response>
    """
    call = client.calls.create(
        record=True,
        from_=TWILIO_PHONE_NUMBER,
        to="+91" + str(to_number),
        twiml=response_xml,
        recording_status_callback=recording_status_callback_url,
        status_callback=status_callback_url
    )
    print(call.sid)
    print(call.status)
    save_call_recording(call.sid, client_id, client_name, to_number, speech_text)

# Route to upload file and process
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        process_file(file_path)
        return 'Processing started. Check logs for details.'

# Route to fetch calls with optional filters
@app.route('/calls', methods=['GET'])
def get_calls():
    date = request.args.get('date')
    client = request.args.get('client')
    successful = request.args.get('successful')

    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()

    query = 'SELECT * FROM calls WHERE 1'
    params = []

    if date:
        query += ' AND date = ?'
        params.append(date)
    if client:
        query += ' AND client_name LIKE ?'
        params.append(f'%{client}%')
    if successful:
        query += ' AND call_status = ?'
        params.append(successful)

    cursor.execute(query, params)
    calls = cursor.fetchall()

    conn.close()

    return jsonify({'calls': calls})

# Function to trim CSV in place
def trim_csv_in_place(file_path):
    temp_file = file_path + '.tmp'
    with open(file_path, 'r', newline='') as infile, open(temp_file, 'w', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        for row in reader:
            trimmed_row = [cell.strip() if isinstance(cell, str) else cell for cell in row]
            writer.writerow(trimmed_row)
    
    os.replace(temp_file, file_path)

@app.route('/handle_recording_status', methods=['POST'])
def handle_recording_status():
    recording_url = request.form.get('RecordingUrl')
    recording_status = request.form.get('RecordingStatus')
    call_sid = request.form.get('CallSid')

    # Fetch call details from the database using the CallSid
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    cursor.execute('SELECT client_id, client_name, phone_number FROM calls WHERE id = ?', (call_sid,))
    call_details = cursor.fetchone()
    
    if call_details:
        client_id, client_name, phone_number = call_details
        cursor.execute('UPDATE calls SET recording_url = ? WHERE id = ?', (recording_url, call_sid))
        conn.commit()
    conn.close()

    return '', 200  # Return a 200 OK response to Twilio

@app.route('/handle_callback', methods=['GET', 'POST'])
def handle_callback():
    call_status = request.form.get('CallStatus')
    call_sid = request.form.get('CallSid')

    # Fetch call details from the database using the CallSid
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    cursor.execute('SELECT client_id, client_name, phone_number, speech_text FROM calls WHERE id = ?', (call_sid,))
    call_details = cursor.fetchone()
    
    if call_details:
        client_id, client_name, phone_number, speech_text = call_details
        cursor.execute('UPDATE calls SET call_status = ? WHERE id = ?', (call_status, call_sid))
        conn.commit()

        if call_status != 'completed':
            cursor.execute('''
                INSERT INTO unsuccessful_calls (id, client_id, client_name, phone_number, speech_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (call_sid, client_id, client_name, phone_number, speech_text))
            conn.commit()
    conn.close()
    return '', 200  # Return a 200 OK response to Twilio


# Route to retry unsuccessful calls
@app.route('/retry', methods=['POST'])
def retry_unsuccessful_calls():
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM unsuccessful_calls')
    unsuccessful_calls = cursor.fetchall()

    for call in unsuccessful_calls:
        call_sid, client_id, client_name, phone_number, speech_text = call
        place_call(client_id, client_name, phone_number, speech_text)

        # Remove from unsuccessful_calls table
        cursor.execute('DELETE FROM unsuccessful_calls WHERE id = ?', (call_sid,))
        conn.commit()

    conn.close()

    return 'Retry process completed.'

@app.route('/unsuccessful', methods=['GET'])
def get_clients():
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    cursor.execute('SELECT client_id, client_name, phone_number FROM unsuccessful_calls')
    clients = cursor.fetchall()
    conn.close()

    client_list = [
        {"client_id": client[0], "client_name": client[1], "phone_number": client[2]}
        for client in clients
    ]
    return jsonify({'clients': client_list})

import time

def process_file(file_path):
    trim_csv_in_place(file_path)

    data = pd.read_csv(file_path)
    client_phone_mapping = pd.read_csv(CLIENT_PHONE_MAPPING_FILE)

    client_phone_dict = client_phone_mapping.set_index('CODE')['MOBILE'].to_dict()
    phone_to_clients = {}

    for client_id, client_data in data.groupby('Client'):
        client_name = client_data.iloc[0]['Client Name']  # Assuming 'Client Name' is in the CSV
        client_phone = client_phone_dict.get(client_id, None)

        if client_phone:
            if client_phone not in phone_to_clients:
                phone_to_clients[client_phone] = []
            phone_to_clients[client_phone].append((client_id, client_name, client_data))

    for phone_number, client_list in phone_to_clients.items():
        for client_id, client_name, client_data in client_list:
            trade_texts = [generate_trade_text(trade) for index, trade in client_data.iterrows()]
            speech_text = f"This is a call from Om Capital for Client ID {client_id}. I will announce your day's trades and once I am done, please confirm by saying Yes. Your trades for the day are: " + ". ".join(trade_texts)
            place_call(client_id, client_name, phone_number, speech_text)
            print(f"Recording saved for Client ID: {client_id}, Phone Number: {phone_number}")
            # time.sleep(120)  # Sleep for 5 seconds between calls


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500)
