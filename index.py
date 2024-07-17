
import sqlite3
from flask import Flask, request, redirect, url_for, Response, send_from_directory, jsonify
import pandas as pd
import os
import csv
from flask_cors import CORS
from datetime import datetime
from twilio.rest import Client


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
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]


TWILIO_PHONE_NUMBER = '+12513206365'



@app.route('/generate_twiml', methods=['GET', 'POST'])
def generate_twiml():
    text = request.args.get('text')
    response_xml = f"""
    <Response>
        <Say>{text}</Say>
        <Pause length="5"/>
    </Response>
    """
    return Response(response_xml, mimetype='text/xml')
# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT,
            client_name TEXT,
            phone_number TEXT,
            date TEXT,
            time TEXT,
            recording_url TEXT,
            success TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Function to save call recording details to SQLite database
def save_call_recording(client_id, client_name, phone_number, recording_url):
    conn = sqlite3.connect('calls.db')
    cursor = conn.cursor()
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    cursor.execute('''
        INSERT INTO calls (client_id, client_name, phone_number, date, time, recording_url, success)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (client_id, client_name, phone_number, current_date, current_time, recording_url, ""))
    conn.commit()
    conn.close()

# Function to generate speech text from trade details
def generate_trade_text(trade):
    instrument = trade['Instrument Type']
    action = 'Bought' if float(trade['Net Qty']) > 0 else 'Sold'
    net_quantity = abs(float(trade['Net Qty']))
    net_price = float(trade['Net Price'])
    scrip = trade['Scrip Name']
    
    if instrument == 'Equities':
        return f"{action} {net_quantity} shares of {scrip} at {net_price}"
    elif instrument == 'Options':
        option_type = 'call' if trade['Option Type'] == 'Call' else 'put'
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
    response_url = url_for('generate_twiml', _external=True, text=speech_text)
   

    call = client.calls.create(
        record=True,
        from_=TWILIO_PHONE_NUMBER,
        to="+919836046413",
        url=response_url
    )
    print(call.sid)
    # Simulate placing a call and returning a dummy recording URL
    recording_url = f'http://dummy.recording.url/{client_id}'
    save_call_recording(client_id, client_name, to_number, recording_url)
    return recording_url

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
        # Assuming 'successful' is a boolean indicating if the call was successful
        query += ' AND success = ?'
        params.append(successful)

    cursor.execute(query, params)
    calls = cursor.fetchall()

    conn.close()

    # Convert to JSON and return
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


# @app.route('/callback', methods=['POST'])
# def callback():


# Function to process uploaded CSV
def process_file(file_path):
    trim_csv_in_place(file_path)

    data = pd.read_csv(file_path)
    client_phone_mapping = pd.read_csv(CLIENT_PHONE_MAPPING_FILE)

    client_phone_dict = client_phone_mapping.set_index('CODE')['MOBILE'].to_dict()

    for client_id, client_data in data.groupby('Client'):
        client_name = client_data.iloc[0]['Client Name']  # Assuming 'Client Name' is in the CSV
        client_phone = client_phone_dict.get(client_id, None)
        
        if client_phone:
            trade_texts = [generate_trade_text(trade) for index, trade in client_data.iterrows()]
            speech_text = "Your trades for the day are: " + ". ".join(trade_texts)
            recording_url = place_call(client_id, client_name, client_phone, speech_text)
            print(f"Recording saved for Client ID: {client_id}, Phone Number: {client_phone}, URL: {recording_url}")
        else:
            print(f"No phone number found for Client ID: {client_id}")




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5500)