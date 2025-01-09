from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)



#dictionaries to hold the ruuvi data variables
magicmountain = {
    "temp": 0,
    "humidity": 0,
    "pressure": 0,
    "acceleration_x": 0,
    "acceleration_y": 0,
    "acceleration_z": 0
}

lodge = {
    "temp": 0,
    "humidity": 0,
    "pressure": 0,
    "acceleration_x": 0,
    "acceleration_y": 0,
    "acceleration_z": 0
}



@app.route('/')
def dashboard():
    data = {
        'magicmountain': magicmountain,
        'lodge': lodge
    }
    return render_template('dashboard.html', data=data)

@app.route('/request', methods=['POST'])
def request_data():  # renamed function since 'request' conflicts with Flask's request object
    global data
    try:
        data = request.get_json()
        tags = data['data']['tags']
        #Define tags with MAC addresses
        tag_magicmountain = tags['D6:34:9B:BF:40:B2']
        tag_lodge=tags['CC:22:D5:38:CB:97']
        # Update data variables
        magicmountain.update({
            'temp': tag_magicmountain['temperature'],
            'humidity': tag_magicmountain['humidity'],
            'pressure': tag_magicmountain['pressure'],
            'acceleration_x': tag_magicmountain['acceleration_x'],
            'acceleration_y': tag_magicmountain['acceleration_y'],
            'acceleration_z': tag_magicmountain['acceleration_z']
        })
        lodge.update({
            'temp': tag_lodge['temperature'],
            'humidity': tag_lodge['humidity'],
            'pressure': tag_lodge['pressure'],
            'acceleration_x': tag_lodge['acceleration_x'],
            'acceleration_y': tag_lodge['acceleration_y'],
            'acceleration_z': tag_lodge['acceleration_z']
        })


        print(tags)
        socketio.emit('data_update', data)  # Emit data to all connected clients
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
   socketio.run(app, debug=False, host='0.0.0.0', port=5000)