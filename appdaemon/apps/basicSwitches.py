import appdaemon.plugins.hass.hassapi as hass

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
            if (self.isItLightOutside() and self.onlyWhenDark):
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
    
    def isItLightOutside(self):
        weather = self.get_state("weather.home")
        if (self.sun_up()):
            if (weather == "sunny"): 
                return True
        
        return False

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