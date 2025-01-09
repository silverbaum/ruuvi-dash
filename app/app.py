from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)





#@app.route('/')
#def index():
#    return render_template('index.html')



@app.route('/request', methods=['POST'])
def request_data():  # renamed function since 'request' conflicts with Flask's request object
    global data
    try:
        data = request.get_json()
        print(data)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/')
def dashboard():
    return render_template('dashboard.html', data=data)


if __name__ == '__main__':
   # Flask.run(app, debug=True)
   socketio.run(app, debug=True, host='0.0.0.0', port=5000)