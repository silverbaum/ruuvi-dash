#SPDX-FileCopyrightText: 2025 Topias Silfverhuth
#SPDX-License-Identifier: MIT

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

RTags = {}
def update_data(data):
    global RTags
    
    if len(data) != len(RTags):
         RTags = {} 

    for tag in data:
        RTags[tag] = ({
            "temperature": data[tag].get('temperature', 0),
            "humidity": data[tag].get('humidity', 0),
            "pressure": (data[tag].get('pressure', 0)/1000) })
    packets = {tag:val for (tag, val) in enumerate(RTags.values())}
    socketio.emit('data_update', packets)
    return packets

@app.route("/")
@app.route("/dashboard")
def dashboard():
    data = {i:tag for (i, tag) in enumerate(RTags.values())}
    return render_template("dashboard.html", data=data)


@app.route("/request", methods=["POST"])
def request_data():
    """
    Receives gateway data in json and sends processed data to clients through websocket
    """
    try:
        tags = request.get_json()["data"]["tags"]
        packets = update_data(tags)

        return jsonify({"status": "success", "data": packets}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == "__main__":
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)

# command for gunicorn(for docker place in dockerfile CMD[]):
# gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:5000 app.app:app
