"""
Copyright (c) 2025 Topias Silfverhuth

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from gevent import monkey
monkey.patch_all()
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_socketio import SocketIO, emit
from os import getenv

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

class Tags:
    """Class to manage ruuvitag data"""
    def __init__(self):
        self.tags={}
    def empty(self):
        self.tags = {}
    def updata(self, data, mac=0):
        macs = data.get('id')
        self.tags[macs] = ({
        "temperature": data.get('temperature', 0),
        "humidity": data.get('humidity', 0),
        "pressure": (data.get('pressure', 0)/1000)}
        )
objs = Tags() 

#redirect to dash
@app.route('/')
def redirecter():
    return  redirect(url_for('dashboard'), code=308)

#dashboard
@app.route('/dashboard')
def dashboard():
    data = {}
    for i, tag in enumerate(objs.tags): # creates indexed list of objs (0, obj[0]), (1, obj[1])
        data[f"{i}"] = objs.tags[tag]
    return render_template('dashboard.html', data=data)

#data route
@app.route('/request', methods=['POST'])
def request_data():
    """Receives gateway data in json and sends processed data to clients with SocketIO
    
    Currently only supports decoded data. (data format 5 in gw json)
    The data is 'saved' in an instance of the Tags class.
    
    """
    try:
        data = request.get_json()
        tags = data['data']['tags']
        num_of_tags = len(tags) 
        tag_macs = tags.keys()

        if num_of_tags != len(objs.tags): 
            objs.empty()

        for tag in tag_macs:
           objs.updata(tags[tag])

        packets = {tag:val for (tag, val) in enumerate(objs.tags.values())}
        socketio.emit('data_update', packets)

        return jsonify({"status": "success", "data": packets}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == '__main__':
    if getenv('FLASK_ENV' == 'development'):
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
        
"""
command for gunicorn(for docker place in dockerfile CMD[]):
gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:5000 app.app:app
"""