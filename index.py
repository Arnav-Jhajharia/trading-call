import sqlite3
from flask import Flask, request, redirect, url_for, Response, send_from_directory, jsonify
import pandas as pd
import os
import csv
from flask_cors import CORS
from datetime import datetime, timedelta
from twilio.rest import Client
import queue
import threading
import time

app = Flask(__name__, static_folder='../client/build', static_url_path='/')
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
AUDIO_FOLDER = 'audio'
CLIENT_PHONE_MAPPING_FILE = 'clients_list.csv'

# Ensure the audio folder and uploads folder exist
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_PHONE_NUMBER = '+12513206365'

# Create a queue for calls
call_queue = queue.Queue()

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

def process_call_queue():
    last_call_time = {}
    while True:
        call_info = call_queue.get()
        if call_info is None:
            break  # Exit the loop if None is enqueued

        client_id, client_name, phone_number, speech_text = call_info
        
        # Check if we need to wait before making the call
        current_time = datetime.now()
        if phone_number in last_call_time:
            time_since_last_call = (current_time - last_call_time[phone_number]).total_seconds()
            if time_since_last_call < 90:
                wait_time = 90 - time_since_last_call
                time.sleep(wait_time)
        
        # Make the call
        place_call(client_id, client_name, phone_number, speech_text)
        print(f"Call made for Client ID: {client_id}, Phone Number: {phone_number}")
        
        # Update the last call time for this phone number
        last_call_time[phone_number] = datetime.now()

        call_queue.task_done()

# Start the background thread for processing calls
call_thread = threading.Thread(target=process_call_queue, daemon=True)
call_thread.start()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        result = process_file(file_path)
        return jsonify({"message": result}), 200

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

    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    cursor.execute('SELECT client_id, client_name, phone_number FROM calls WHERE id = ?', (call_sid,))
    call_details = cursor.fetchone()
    
    if call_details:
        client_id, client_name, phone_number = call_details
        cursor.execute('UPDATE calls SET recording_url = ? WHERE id = ?', (recording_url, call_sid))
        conn.commit()
    conn.close()

    return '', 200

@app.route('/handle_callback', methods=['GET', 'POST'])
def handle_callback():
    call_status = request.form.get('CallStatus')
    call_sid = request.form.get('CallSid')

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
    return '', 200

@app.route('/retry', methods=['POST'])
def retry_unsuccessful_calls():
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM unsuccessful_calls')
    unsuccessful_calls = cursor.fetchall()

    for call in unsuccessful_calls:
        call_sid, client_id, client_name, phone_number, speech_text = call
        call_queue.put((client_id, client_name, phone_number, speech_text))

        # Remove from unsuccessful_calls table
        cursor.execute('DELETE FROM unsuccessful_calls WHERE id = ?', (call_sid,))
        conn.commit()

    conn.close()

    return 'Retry process queued.'

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

def process_file(file_path):
    trim_csv_in_place(file_path)

    data = pd.read_csv(file_path)
    client_phone_mapping = pd.read_csv(CLIENT_PHONE_MAPPING_FILE)

    client_phone_dict = client_phone_mapping.set_index('CODE')['MOBILE'].to_dict()

    for _, row in data.iterrows():
        client_id = row['Client']
        client_name = row['Client Name']
        phone_number = client_phone_dict.get(client_id)
        
        if phone_number:
            trade_text = generate_trade_text(row)
            speech_text = f"This is a call from Om Capital for Client ID {client_id}. I will announce your day's trades and once I am done, please confirm by saying Yes. Your trade for the day is: {trade_text}"
            
            # Instead of making the call directly, add it to the queue
            call_queue.put((client_id, client_name, phone_number, speech_text))
            print(f"Call queued for Client ID: {client_id}, Phone Number: {phone_number}")
        else:
            print(f"No phone number found for Client ID: {client_id}")

    return f"Processed {len(data)} rows. Calls have been queued."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500)