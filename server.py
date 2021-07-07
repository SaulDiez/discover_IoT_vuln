from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
from libDiscovery.discoveryDNS_SD import discMDNS
from libDiscovery.discoverySSDP import discSSDP
from libDiscovery.discoveryWSD import discWSD

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

#cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


#@app.route('/api')
#def listeningServer():
#    print("jeje")
#@app.route('/api')
#def create_task():
#    dictAll={}
#    dictAll.update(discSSDP())
#    dictAll.update(discMDNS())
#    dictAll.update(discWSD())
#    return jsonify(dictAll)

@socketio.on('connect')
def handle_connect():
    print("connnnnnnected")

@socketio.on('emit_method')
def handle_sendEmit(val):
    print(val)
    dictAll={}
    dictAll.update(discSSDP())
    dictAll.update(discMDNS())
    #dictAll.update(discWSD())
    emit('customEmit', dictAll)

if __name__ == '__main__':
    socketio.run(app)