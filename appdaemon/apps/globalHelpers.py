import appdaemon.plugins.hass.hassapi as hass

class Enviroment(hass.Hass):
  @staticmethod
  def isItLightOutside(self):
    weather = self.get_state("weather.home")
    if (self.sun_up()):
      if (weather == "sunny"): 
        return True
        
    return False

class Helpers(hass.Hass):
  @staticmethod
  def configureParameter(self, inputArg, default):
    if inputArg in self.args:
        return inputArg
    else:
        return default