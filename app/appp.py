from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import os
import gunicorn
import six
import eventlet
eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

data = {}  # Initialize data variable


#dictionaries to hold the ruuvi data variables
kitchen = {
    "temp": 0,
    "humidity": 0,
    "pressure": 0,
    "acceleration_x": 0,
    "acceleration_y": 0,
    "acceleration_z": 0
}

outside = {
    "temp": 0,
    "humidity": 0,
    "pressure": 0,
    "acceleration_x": 0,
    "acceleration_y": 0,
    "acceleration_z": 0
}



@app.route('/')
def dashboard():
    return render_template('dashboard.html', data=data)

@app.route('/request', methods=['POST'])
def request_data():  # renamed function since 'request' conflicts with Flask's request object
    try:
        data = request.get_json()
        tags = data['data']['tags']
        tag_magicmountain = tags['D6:34:9B:BF:40:B2']
        tag_lodge=tags['CC:22:D5:38:CB:97']
        temp=tag_magicmountain['temperature']
        print(tags)
        socketio.emit('data_update', data)  # Emit data to all connected clients
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    if os.getenv('FLASK_ENV') == 'development':
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        from gunicorn.app.base import BaseApplication
        from six import iteritems

        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()

            def load_config(self):
                config = {key: value for key, value in iteritems(self.options)
                          if key in self.cfg.settings and value is not None}
                for key, value in iteritems(config):
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            'bind': '0.0.0.0:5000',
            'workers': 1,
            'worker_class': 'eventlet'
        }
        StandaloneApplication(app, options).run()