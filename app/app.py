#SPDX-FileCopyrightText: 2025 Topias Silfverhuth
#SPDX-License-Identifier: MIT

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO
import sqlite3
import pandas as pd
import logging

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

log = logging.getLogger("ruuvi-dash")
logging.basicConfig(level=logging.DEBUG)

dbconn = sqlite3.connect("ruuvidata.db")
cur = dbconn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS data(id int, temperature float, humidity float, pressure float, date timestamptz)")
dbconn.commit()

updata_counter: int = 0

RTags = {}

def update_database():
    try:
        for i, tag in enumerate(RTags.values()):
            log.debug(f" i: {i}, tag: {tag}")
            cur.execute(f"INSERT INTO data(id, temperature, humidity, pressure, date) VALUES ('{i}', {tag.get('temperature')}, {tag.get('humidity')}, {tag.get('pressure', 0)}, datetime('now'));")
        cur.execute("DELETE FROM data WHERE date < datetime('now', '-1 years');")
        dbconn.commit()
        log.info(" Inserted data into db")
    except Exception as e:
        log.error(" Data collection failed: %s" % e)



def update_data(data):
    global RTags
    global updata_counter
    
    if len(data) != len(RTags):
         RTags = {} 

    for tag in data:
        RTags[tag] = ({
            "temperature": data[tag].get('temperature', 0),
            "humidity": data[tag].get('humidity', 0),
            "pressure": (data[tag].get('pressure', 0)/1000) })
    packets = {tag:val for (tag, val) in enumerate(RTags.values())}

    updata_counter += 1
    if updata_counter > 25:
        update_database()
        updata_counter = 0
    socketio.emit('data_update', packets)
    return packets

"""ROUTES"""

@app.route("/graph/<item>")
def graph(item):
    weeks = request.args.get('weeks', 1, type=int)
    data = {}
    df = pd.read_sql(f"SELECT * FROM data where date > datetime('now', '-{weeks*7} days');", dbconn, index_col=None).groupby('id')
    for id, group in df:
        date = pd.to_datetime(group.date, errors='coerce').dt.strftime("%H:%M").to_list()
        log.debug(date)
        if item == "humidity":
            data[str(id)] = {"date": date, "humidity": group.humidity.tolist()}
        elif item == "pressure":
            data[str(id)] = {"date": date, "pressure": group.pressure.tolist()}
        else:
            data[str(id)] = {"date": date, "temperature": group.temperature.tolist()}
        #print(group.temperature.tolist())
    log.debug(data)

    if not len(data):
        return render_template("graph.html")
    elif not item or (item != "humidity" and item != "pressure" and item != "temperature"):
        return render_template("graph.html", labels=data['0']['date'], values=data['0']["temperature"], values_1=data['1']["temperature"])
    return render_template("graph.html", labels=data['0']['date'], values=data['0'][str(item)], values_1=data['1'][str(item)])

@app.route("/graph")
@app.route("/graph/")
def graph_redirect():
    return graph("temperature")

@app.route("/supersecretadmin")
def admin():
    passwd: str = request.args.get("pass", type=str)
    weeks: int = request.args.get("weeks", type=int)
    if passwd == "javasdk8" and weeks >= 0:
        try:
            cur.execute(f"DELETE FROM data WHERE date < datetime('now', '-{weeks*7} days');")
            dbconn.commit()
            log.info("successfully deleted data older than", weeks, "weeks")
        except Exception as e:
            log.error(e)
            return jsonify({"status": "error", "message": str(e)}), 500
    return render_template("admin.html")


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
        log.info(request.get_json())
        tags = request.get_json()["data"]["tags"]
        packets = update_data(tags)
        

        return jsonify({"status": "success", "data": packets}), 200
    except Exception as e:
        log.error(e)
        return jsonify({"status": "error", "message": str(e)}), 400
        

if __name__ == "__main__":
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)

# command for gunicorn(for docker place in dockerfile CMD[]):
# gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --workers 1 --bind 0.0.0.0:5000 app.app:app
