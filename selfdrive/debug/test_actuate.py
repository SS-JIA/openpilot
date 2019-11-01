#!/usr/bin/env python
import struct
from common.numpy_fast import clip
from common.params import Params
from copy import copy
from cereal import car, log
import selfdrive.messaging as messaging
from selfdrive.car.car_helpers import get_car
from selfdrive.boardd.boardd import can_list_to_can_capnp

from selfdrive.car.toyota.values import CAR, DBC
from selfdrive.services import service_list
from selfdrive.car.toyota.interface import CarInterface
from selfdrive.car.toyota.carcontroller import CarController

HwType = log.HealthData.HwType


if __name__ == '__main__':

  logcan = messaging.sub_sock(service_list['can'].port)
  health = messaging.sub_sock(service_list['health'].port)

  carstate = messaging.pub_sock(service_list['carState'].port)
  carcontrol = messaging.pub_sock(service_list['carControl'].port)
  sendcan = messaging.pub_sock(service_list['sendcan'].port)

  button_1_last = 0
  enabled = False

  # wait for health and CAN packets
  hw_type = messaging.recv_one(health).health.hwType
  has_relay = hw_type in [HwType.blackPanda, HwType.uno]
#  print("Waiting for CAN messages...")
#  messaging.get_one_can(logcan)


  CP = CarInterface.get_params(CAR.COROLLA_TSS2)
  CI = CarInterface(CP, CarController)
  Params().put("CarParams", CP.to_bytes())

  CC = car.CarControl.new_message()

  while True:

    can_strs = messaging.drain_sock_raw(logcan, wait_for_one=True)
    CS = CI.update(CC, can_strs)
#
#    # Usually axis run in pairs, up/down for one, and left/right for
#    # the other.
    actuators = car.CarControl.Actuators.new_message()
##
#    if joystick is not None:
#      axis_3 = clip(-joystick.testJoystick.axes[3] * 1.05, -1., 1.)          # -1 to 1
    actuators.steer = 0
    actuators.steerAngle = actuators.steer * 43.   # deg
    print(actuators.steerAngle)
#      axis_1 = clip(-joystick.testJoystick.axes[1] * 1.05, -1., 1.)          # -1 to 1
    actuators.gas = 0
    actuators.brake = 0
#
    pcm_cancel_cmd = False # joystick.testJoystick.buttons[0]
#      button_1 = joystick.testJoystick.buttons[1]
#      if button_1 and not button_1_last:
#        enabled = not enabled
#
#      button_1_last = button_1
#
#      #print "enable", enabled, "steer", actuators.steer, "accel", actuators.gas - actuators.brake
#
    hud_alert = 0
    audible_alert = 0
    enabled = False
#      if joystick.testJoystick.buttons[2]:
#        audible_alert = "beepSingle"
#      if joystick.testJoystick.buttons[3]:
#        audible_alert = "chimeRepeated"
#        hud_alert = "steerRequired"
#
    CC.actuators.gas = actuators.gas
    CC.actuators.brake = actuators.brake
    CC.actuators.steer = actuators.steer
    CC.actuators.steerAngle = actuators.steerAngle
    CC.hudControl.visualAlert = hud_alert
    CC.hudControl.setSpeed = 20
    CC.cruiseControl.cancel = pcm_cancel_cmd
    CC.enabled = enabled
    can_sends = CI.apply(CC)
    sendcan.send(can_list_to_can_capnp(can_sends, msgtype='sendcan'))

    print("Actuating...")
    # broadcast carState
    cs_send = messaging.new_message()
    cs_send.init('carState')
    cs_send.carState = copy(CS)
    carstate.send(cs_send.to_bytes())

    # broadcast carControl
    cc_send = messaging.new_message()
    cc_send.init('carControl')
    cc_send.carControl = copy(CC)
    carcontrol.send(cc_send.to_bytes())

