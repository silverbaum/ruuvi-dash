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


#RuuviTag object class
class RuuviTag:
 def __init__(self):
      self.data = {
	  "temperature": 0,
	  "humidity": 0,
	  "pressure": 0
	  }
 def updata(self, data):
      self.data.update({
	  "temperature": data.get('temperature', 0),
	  "humidity": data.get('humidity', 0),
	  "pressure": (data.get('pressure', 0)/1000)}
	  )
      
class objs: #class to manage ruuvitag objects
    def __init__(self):
        self.tags=[]
    def empty(self):
        self.tags = []
    def add(self, ntag):
        for i in range(ntag):
            i = RuuviTag()
            self.tags.append(i)
objectifier = objs() 


#redirect to dash
@app.route('/')
def redirecter():
    return  redirect(url_for('dashboard'), code=308)

#dashboard
@app.route('/dashboard')
def dashboard():
    data = {}
    for i, obj in enumerate(objectifier.tags): # creates indexed list of objs (0, obj[0]), (1, obj[1])
        data[f"Tag {i}"] = obj.data 
    return render_template('dashboard.html', data=data)

#data route
@app.route('/request', methods=['POST'])
def request_data(): #only supports decoded data
    try:
        data = request.get_json()
        tags = data['data']['tags']
        num_of_tags = len(tags) 
        tag_macs = tags.keys() #MAC addresses from the tags dictionary

        #creating the ruuvitag objects
        if num_of_tags != len(objectifier.tags): #clear the objects if the amount of tags changes
            objectifier.empty()
        if objectifier.tags == []: #if the list is empty i.e. no objects, create new objects
            objectifier.add(num_of_tags)
    
        for i, tag in enumerate(tag_macs):
            objectifier.tags[i].updata(data['data']['tags'][tag])

        # Create packets with tag names
        packets = {}
        for i in range(len(objectifier.tags)):
            packets[f"Tag {i}"] = objectifier.tags[i].data 
        
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