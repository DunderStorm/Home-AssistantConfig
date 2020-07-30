import appdaemon.plugins.hass.hassapi as hass
import datetime
from globalHelpers import Enviroment, Helpers

# basic switched out with optional off hysteresis timer and only at night filter
class switchedLight(hass.Hass):
    
    def initialize(self):
        self.timerHandle = None
        self.sensor = self.args["sensor"]
        
        self.actuators = self.args["actuators"].split(",")
        
        if "offTimer" in self.args:
            self.offTimer = self.args["offTimer"]
        else:
            self.offTimer = 0
        
        if "onlyWhenDark" in self.args:
            self.onlyWhenDark = self.args["onlyWhenDark"]
        else:
            self.onlyWhenDark = False
      
        self.listen_state(self.trigger, self.sensor)
        
        self.log(self.sensor)
        self.log(self.actuators)
 
    def trigger(self, entity, attribute, old, new, kwargs):
        if new == "on":
            if (Enviroment.isItLightOutside(self) and self.onlyWhenDark):
                self.log("pressence detected but weather is great and sun still up")
            else:
                if self.timerHandle == None:
                    self.turnOnAll() # turn on all lights
                    self.log("light on")

                else:
                    self.cancel_timer(self.timerHandle)
                    self.log("reset timer")
        
        if new == "off":
            self.timerHandle = self.run_in(self.timeout, self.offTimer)
    

    def timeout(self, kwargs):
        if (self.get_state(self.sensor) == "off"):
            self.turnOffAll()
            self.timerHandle = None
        else:
            self.log("light timed out while sensor is on, this should not happen")
    
    def turnOnAll(self):
        for actuator in self.actuators:
            self.turn_on(actuator)
    
    def turnOffAll(self):
        for actuator in self.actuators:
            self.turn_off(actuator)
            
            
class timerSwitch(hass.Hass):
  
  def initialize(self):
    self.actuators = self.args["actuators"].split(",")
    self.onlyWhenDark = Helpers.configureParameter(self, "onlyWhenDark", False)
    
    self.start = self.convertToMinutesSinceMidnight(Helpers.configureParameter(self, "start", "10:00"))
    self.end = self.convertToMinutesSinceMidnight(Helpers.configureParameter(self, "end", "23:59"))
    
    self.run_every(self.updateSwitch, self.datetime() + datetime.timedelta(seconds=3), 60)

  def convertToMinutesSinceMidnight(self, inputString):
    tempList = [int(x) for x in inputString.split(":")]
    return tempList[0]*60 + tempList[1]
    
  def updateSwitch(self, kwargs):
    currentTime = self.datetime()
    minutesSinceMidnight = currentTime.hour*60 + currentTime.minute
    
    
    if (minutesSinceMidnight < self.start):
      self.log("doNothing")
      
    elif (minutesSinceMidnight < self.end):
      if (Enviroment.isItLightOutside(self) and self.onlyWhenDark):
        self.log("too light for lights")
      else:
        #Turn on all lights
        for actuator in self.actuators:
          self.turn_on(actuator)
    
    else:
      #Turn off all lights
      for actuator in self.actuators:
        self.turn_off(actuator)
    