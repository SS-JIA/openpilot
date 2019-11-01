import os
import unittest
import time
import zmq

import requests

import selfdrive.messaging as messaging
from selfdrive.car.toyota.carstate import CarState, get_can_parser
from selfdrive.car.toyota.interface import CarInterface
from selfdrive.car.toyota.values import CAR, DBC
from selfdrive.services import service_list

if __name__ == "__main__":
    CP = CarInterface.get_params(CAR.COROLLA_TSS2)
    
    addr="127.0.0.1"
	
    can_poller = zmq.Poller()

    can_sock = messaging.sub_sock(service_list['can'].port)
    can_poller.register(can_sock)


    state = CarState(CP)
    parser = get_can_parser(CP)

    while True:
        can_strings = messaging.drain_sock_raw_poller(can_poller, can_sock, wait_for_one=True)

        parser.update_strings(can_strings)
        state.update(parser)
        print("Steering Angle: " + str(state.angle_steers))
        time.sleep(1)
        

