import appdaemon.plugins.hass.hassapi as hass
from pysolar.solar import *
import datetime


class circadianLight(hass.Hass):
    def initialize(self):
        
        #get all configuration parameters
        self.lights = self.args["lights"].replace(' ','').split(",")
        
        self.onOffBool = self.args["onOffBool"]
        
        self.zenitTemp = self.configureParameter("zenitTemp", 6000)
        self.duskDawnTemp = self.configureParameter("duskDawnTemp", 2500)
        self.nightTemp = self.configureParameter("nightTemp", 2200)
        self.bedtimeBright = self.configureParameter("bedtimeBright", 1)
        
        self.eveningStart = self.convertToMinutesSinceMidnight(self.configureParameter("eveningStart", "21:00"))
        self.bedtime = self.convertToMinutesSinceMidnight(self.configureParameter("bedtime", "23:00"))
        self.wakeUpStart = self.convertToMinutesSinceMidnight(self.configureParameter("wakeUpStart", "8:30"))
        self.wakeUpEnd = self.convertToMinutesSinceMidnight(self.configureParameter("wakeUpEnd", "9:00"))
        
        self.latitude = 0 # 59.4 #self.config["latitude"]
        self.longitude = 18.0 #self.config["longitude"]
        
        self.eveningLength = self.bedtime - self.eveningStart        
        self.wakeUpLength = self.wakeUpEnd - self.wakeUpStart
        
        self.config = self.get_plugin_config()
        self.run_every(self.updateColor, self.datetime() + datetime.timedelta(seconds=3), 60)
        
        #register callbask for onoffbool so everythign updates when bool turns on
        self.listen_state(self.onOffBoolEvent, self.onOffBool, new = "on")  
        
        #register callbacks for all light so they can be autoupdated when turned  on
        for light in self.lights:
          self.listen_state(self.lightEvent, light, new = "on")        
        
        self.log(f'Initializing at {self.latitude:.2f}(Lat), {self.longitude:.2f}(Long)')

    def configureParameter(self, inputArg, default):
        if inputArg in self.args:
            return inputArg
        else:
            return default
        
            
    def convertToMinutesSinceMidnight(self, inputString):
        tempList = [int(x) for x in inputString.split(":")]
        return tempList[0]*60 + tempList[1]
        
    
    #calculates timedelta in minutes
    def calculateTimeDelta(self, startTime, endTime):
        return (endTime[0] - startTime[0])*60 + endTime[1] - startTime[1]
    
    #recalculate color & brightness
    def updateColor(self, kwargs):
        solarElevation = get_altitude(self.latitude, self.longitude, self.get_now())
        currentTime = self.datetime()
        minutesSinceMidnight = currentTime.hour*60 + currentTime.minute
        
        #calculate color temperature
        if (solarElevation > 0):
            self.brightness = 100
            self.colorTemp = self.duskDawnTemp + 80 * solarElevation
            if (self.colorTemp > self.zenitTemp):
                self.colorTemp = self.zenitTemp
        else:
            self.colorTemp = self.duskDawnTemp + solarElevation * 25
            self.colorTemp = self.nightTemp if (self.colorTemp < self.nightTemp) else self.colorTemp
        
        #calculate brightness
        # if time is night, set low brightness
        if (minutesSinceMidnight < self.wakeUpStart):
          self.brightness = self.bedtimeBright
        # if during wakup phase, fade up lights
        elif (minutesSinceMidnight < self.wakeUpEnd):
          self.brightness = (minutesSinceMidnight - self.wakeUpStart)/self.wakeUpLength*100
        #elif befor evening start
        elif (minutesSinceMidnight < self.eveningStart):
          self.brightness = 100
        #if evening have started
        elif (minutesSinceMidnight < self.bedtime):
          self.brightness = 100 - (minutesSinceMidnight - self.eveningStart)/self.eveningLength*(100 - self.bedtimeBright)
        else:
          self.brightness = self.bedtimeBright
        
        #change light color & brightness for all lights that are on
        if (self.get_state(self.onOffBool) == "on"):
          for light in self.lights:
              if(self.get_state(light) == "on"):
                self.turn_on(light, kelvin = self.colorTemp, brightness_pct = self.brightness)
        
        self.log(f"solar elevation: {solarElevation:.0f}, color temp: {self.colorTemp:.0f}, brightness: {self.brightness:.0f}")
       
        
    def lightEvent(self, entity, attribute, old, new,  kwargs):
      if (self.get_state(self.onOffBool) == "on"):
        self.log(entity + " turned on, color reset")
        self.turn_on(entity, kelvin = self.colorTemp, brightness_pct = self.brightness)
        self.log(entity + " brightness: " + f'{self.get_state(entity, attribute="brightness")}')
        
        
    def onOffBoolEvent(self, entity, attribute, old, new,  kwargs):
      for light in self.lights:
        if(self.get_state(light) == "on"):
          self.turn_on(light, kelvin = self.colorTemp, brightness_pct = self.brightness)
    
#    def setLight(self, light, colorTemp, brightness):
#      self.turn_on(light, kelvin = self.colorTemp)
#      self.turn_on(light, brightness_pct = self.brightness)
      