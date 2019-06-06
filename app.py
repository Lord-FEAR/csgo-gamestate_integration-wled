from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import time
import json
from threading import Timer
import requests

class MyServer(HTTPServer):
    def __init__(self, server_address, RequestHandler):

        super(MyServer, self).__init__(server_address, RequestHandler)

        self.wled_stat = self.get_wled()
        self.round_phase = None
        self.bomb_state = None
        self.timer30 = None#Timer(30.0, self.wled)
        self.timer35 = None#Timer(35.0, self.wled2)
    
    def get_wled(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
            self.ip = config['ip']
            #print(config['ip'])
        try:
            r = requests.get(url='http://%s/json/state' % self.ip, timeout=5)
            #print(r.json())
            return r.json()
        except requests.exceptions.ConnectTimeout:
            print(time.asctime(), '[CS:GO WLED]', 'WELD not found!')
            sys.exit(0)

    def start_timer30(self):
        #print('start_timer30')
        self.timer30 = Timer(30.0, self.wled)
        self.timer30.start()
    
    def start_timer35(self):
        #print('start_timer35')
        self.timer35 = Timer(35.0, self.wled2)
        self.timer35.start()

    def stop_timer30(self):
        #print('stop_timer30')
        if self.timer30 is not None:
            self.timer30.cancel()
            self.timer30 = None

    def stop_timer35(self):
        #print('stop_timer35')
        if self.timer35 is not None:
            self.timer35.cancel()
            self.timer35 = None

    def wled(self):
        self.send_to_wled(color = [[255, 223, 0],[0,0,0],[0,0,0]])
    def wled2(self):
        self.send_to_wled(color = [[255, 0, 0],[0,0,0],[0,0,0]])

    def send_to_wled(self, color=[[255,255,255],[0,0,0],[0,0,0]], effects=0, data=None):
        #sx=self.wled_stat.state.seg.sx
        #print(self.wled_stat['seg'][0]['sx'])
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain', 'Content-Encoding': 'utf-8'}
        if data is None:
            data = {"seg":[{"col":color, "fx": effects}]}
        requests.post(url='http://%s/json/state' % self.ip, data=json.dumps(data), headers=headers)


class MyRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode('utf-8')

        self.parse_payload(json.loads(body))

        self.send_header('Content-type', 'text/html')
        self.send_response(200)
        self.end_headers()

    def parse_payload(self, payload):
        #print(payload)

        round_phase = self.get_round_phase(payload)
        bomb_state = self.get_bomb_state(payload)

        if round_phase != self.server.round_phase:
            self.server.round_phase = round_phase
            print(time.asctime(), '[CS:GO WLED]', 'New round phase: %s' % round_phase)
            if round_phase == 'over':
                self.server.stop_timer30()
                self.server.stop_timer35()
                self.server.send_to_wled(data = self.server.wled_stat)
        
        if bomb_state != self.server.bomb_state:
            self.server.bomb_state = bomb_state
            if bomb_state is not None:
                print(time.asctime(), '[CS:GO WLED]', 'New bomb state: %s' % bomb_state)
                if bomb_state == 'planted':
                    self.server.start_timer30()
                    self.server.start_timer35()
                    self.server.send_to_wled(color = [[0, 255, 0],[0,0,0],[0,0,0]])

    def get_round_phase(self, payload):
        if 'round' in payload and 'phase' in payload['round']:
            return payload['round']['phase']
        else:
            return None

    def get_bomb_state(self, payload):
        if 'round' in payload and 'bomb' in payload['round']:
            return payload['round']['bomb']
        else:
            return None

    def log_message(self, format, *args):
        """
        Prevents requests from printing into the console
        """
        return

server = MyServer(('127.0.0.1', 32092), MyRequestHandler)

print(time.asctime(), '[CS:GO WLED]', 'Server start')

try:
    server.serve_forever()
except (KeyboardInterrupt, SystemExit):
    pass

server.server_close()
print(time.asctime(), '[CS:GO WLED]', 'Server stop')