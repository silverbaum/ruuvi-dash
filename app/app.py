from gevent import monkey
monkey.patch_all()
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_socketio import SocketIO, emit
from os import getenv, path

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
objs = [] # list which contains the ruuvitag objects


""" SQLITE """
import sqlite3
dbpath = path.join("app", "data", "ruuvidata.db")
cx = sqlite3.connect(dbpath)
cursor = cx.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS ruuvi(Name varchar(20), Temperature float, Humidity float, Pressure float, Date date)') 

def datacollector(packets):
    try:
        for tag in packets:
            vals = packets[tag]
            cursor.execute(f"INSERT INTO ruuvi(name, temperature, humidity, pressure, date) values ('{tag}', {vals.get('temperature')}, {vals.get('humidity')}, {vals.get('pressure')}, datetime('now', 'localtime'));")
            cx.commit()
    except:
        print("data collection failed")
    return



""" RuuviTag object class """
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

def objectifier(ntag): #function to create the RuuviTag objects
    global objs # I wish it wasn't global, currently required by both dashboard and request_data functions
    if ntag == 0:
        objs.clear()
        objs = []

    for i in range(ntag):
        i = RuuviTag()
        objs.append(i)
    return objs



""" Flask app routes """
@app.route('/') #redirect to dash
def redirecter():
    return  redirect(url_for('dashboard'), code=308)

@app.route('/dashboard')
def dashboard():
    data = {}
    for i, obj in enumerate(objs): 
        data[f"Tag_{i}"] = obj.data 
    
    return render_template('dashboard.html', data=data)

@app.route('/request', methods=['POST'])
def request_data():
    try:
        cleandata = {}
        data = request.get_json()
        tags = data['data']['tags']
        num_of_tags = len(tags) 
        tag_macs = tags.keys() #keys from the tags dictionary


        #creating the ruuvitag objects
        if num_of_tags != len(objs): #clear the objects if the amount of tags changes
            objectifier(0)
        if objs == []: #if the list is empty, create new objects
            objectifier(num_of_tags) # create tag objects

        
        #iterate through the data using the mac addresses and place it in the cleandata dict
        for index, tag in enumerate(tag_macs):
            cleandata[index] = data['data']['tags'][tag]
          
        
        
        #update the generated objects with the received data
        for i in range(num_of_tags):
            objs[i].updata(cleandata[i])

        # Create packets with tag names
        packets = {}
        for i in range(len(objs)):
            packets[f"Tag_{i}"] = objs[i].data
    


        
        datacollector(packets)
        
        #print("Emitting data update:", packets)  # Debug print
        socketio.emit('data_update', packets)

        return jsonify({"status": "success", "data": packets}), 200
    except Exception as e:
        print("Error in request_data:", str(e))  # Debug print
        return jsonify({"status": "error", "message": str(e)}), 400


#command for gunicorn:
#gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:5000 app.app:app

if __name__ == '__main__':
    if getenv('FLASK_ENV') == 'development':
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    else:
        socketio.run(app, debug=False, host='0.0.0.0', port=5003)