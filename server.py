# -*- coding: UTF-8 -*-

import gevent
from gevent import socket
import logging
import signal
import time
import json

_options = None
_sock_control = None
_sock_data = None
_clients = {}

'''
Data Packet(Json):
    {
        "ssrc": 12345678,
        "seq": 101
    }

Control Packet(Json):
handshake,client -> server
    {
        "ssrc": 12345678,
        "shake": {
            "expect_period": 0.2,
            "expect_size": 114
        }
    }
handshake,server -> client
    {
        "ssrc": 87654321,
        "shake": {
            "ip": "1.2.3.4",
            "port": 10000
        }
    }

report:
    {
        "ssrc": 1233333,
        #sender report
        "sr": {
            "ssrc": 12345678,       # data source being reported,not
            "ntp": 12346.001323,
            "psent": 100,           # packets sent
            "osent": 1234,          # octets sent
        }
        #receiver report
        "rr": {
            "ssrc": 12345678,
            "lost-fraction": 0.03,           # fraction lost since last report
            "lost": 12,                     # number packets lost( maybe negative )
            "last_seq": 123,                # extended last seq number received
            "jitter": 0.3,                  # interarrival jitter
            "lsr": 23445.2344               # last SR packet from this source
            "dlsr": 34.33                   # delay since last SR packet
        }
    }
'''

def time_now():
    return time.time()

class Remote:
    def __init__(self,addr,**kwargs):
        self.ssrc = kwargs['ssrc']
        self.period = kwargs['expect_period']
        self.packet_size = kwargs['expect_size']
        self.control_address = addr
        self.data_address = None
        self.tv_recv = time_now()
        self.lsr = 0.0

    def onPeriod(self):
        pass

    def update(self,downstream):
        pass

    def onSenderReport(self,report):
        pass

    def onReceiverReport(self,report):
        pass

    def onPacket(self,packet):
        pass

def PollControl():
    while True:
        data,addr = _sock_control.recv(1024)
        if data is None or addr is None:
            continue
        packet = json.loads(data)
        if packet is None:
            continue
        ssrc = packet.get('ssrc')
        if ssrc is None:
            continue
        component = packet.get('shake')
        if component is not None:
            if client is None:
                client = Remote(ssrc,component)
                _clients[ssrc] = client
            else:
                client.update(component)
            continue

        client = _clients.get(ssrc)
        if client is None:
            continue

        component = packet.get('sr')
        if component is not None:
            client.onSenderReport(component)
        component = packet.get('rr')
        if component is not None:
            client.onReceiverReport(component)

def PollData():
    logging.info('Bind data socket on: %s' % str(_options.get('frontend-address')))

    while True:
        data,addr = _sock_data.recv(1024)
        if data is None or addr is None:
            continue 
        packet = json.loads(data)


def TimerLoop(self):
    tn = time_now() + 0.02
    while True:
        gevent.sleep(tn - time_now())
        for client in _clients.values():
            client.onPeriod()
        tn += 0.02


def run(options):
    global _options
    global _sock_data
    global _sock_control
    _options = options

    _sock_data = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    _sock_data.bind(_options.get('data-address'))

    _sock_control = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    _sock_data.bind(_options.get('control-address'))

    tasks = []
    tasks.append( gevent.spawn(pollReply,options) )
    tasks.append( gevent.spawn(pollRequest,options) )
    gevent.signal(signal.SIGINT,gevent.killall,tasks)
    gevent.signal(signal.SIGTERM,gevent.killall,tasks)
    gevent.joinall(tasks)

