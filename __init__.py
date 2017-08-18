
# GPIO Input plugin for Craftbeerpi 
# Version 1 made by nanab
# https://github.com/mrillies/cbpi_GPIO_input
# Some code taken from https://github.com/nanab/Flowmeter


# GPIO Input plugin for Craftbeerpi 
# Version 1 made by mrillies
# https://github.com/mrillies/cbpi_GPIO_input
# Some code taken from https://github.com/nanab/Flowmeter

import time
from modules import cbpi
from modules.core.hardware import SensorActive
import json
from flask import Blueprint, render_template, jsonify, request
from modules.core.props import Property

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except Exception as e:
    print e
    pass

PUD_map = {'Pull Up': GPIO.PUD_UP, 'Pull Down': GPIO.PUD_DOWN, 'Off': GPIO.PUD_OFF}
trig_level = {"Momentary": True,"Latch Rise": True, "Latch Fall" : False }

@cbpi.sensor
class GPIOinput(SensorActive):

    gpio = Property.Select("GPIO", options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27])
    input_type = Property.Select("Input Type", options=["Momentary","Latch Rise", "Latch Fall"], description="Momentary - input high = high val. Latched - pulse on, pulse off")
    pud_type = Property.Select("Pull Up/Down", options=["Pull Up","Pull Down","Off"], description="Pull Up or down ressitor on input")

    on_val = Property.Number("High Value", configurable=True, default_value="0", description="Read value when input is high or Latch True(3.3V)")
    off_val = Property.Number("Low Value", configurable=True, default_value="100", description="Read value when sensor is low or Latch False (0V)")
    out_val = [0,1]

    input_on = False
    latch_val = False
    
    def init(self):
        self.input_on = False
        self.trigger_val = None
        try:                  
            GPIO.setup(int(self.gpio), GPIO.IN , pull_up_down = PUD_map[self.pud_type])
            GPIO.remove_event_detect(int(self.gpio))
            GPIO.add_event_detect(int(self.gpio), GPIO.BOTH, callback=self.IO_trigger, bouncetime=20)
            self.out_val = [self.off_val,self.on_val]
            self.latch_val = trig_level[self.input_type]
            super(GPIOinput,self).init()
            print "Init Complete"
            self.data_received(self.out_val[self.input_on])
        except Exception as e:
            print e

    def get_unit(self):
        unit = "NA"
        return unit
    
    def IO_trigger(self, channel):
        self.sleep(0.0005)
        self.trigger_val = GPIO.input(int(self.gpio))
        if self.input_type[0] == "L":
            if self.trigger_val != self.latch_val:
                self.trigger_val = None

    def execute(self): 
        while self.is_running():
            self.api.socketio.sleep(.1)
            #if GPIO.event_detected(int(self.gpio)):
            if self.trigger_val is not None:
                # if we're here, an edge was recognized
                #self.sleep(0.01) # debounce
                if self.input_type[0] == "M":
                    self.input_on = GPIO.input(int(self.gpio))
                else: #Latch
                    if self.trigger_val == self.latch_val:
                        self.input_on = not self.input_on
               
                self.data_received(self.out_val[self.input_on])
                self.trigger_val = None

    def stop(self):
        self.__running = False
        GPIO.cleanup([int(self.gpio)])
        GPIO.remove_event_detect(int(self.gpio))
