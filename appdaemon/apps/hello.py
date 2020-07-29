import appdaemon.plugins.hass.hassapi as hass

#
# Hellow World App
#
# Args:

class HelloWorld(hass.Hass):

  def initialize(self):
     self.log("Hello from AppDaemon2")
     self.log("You are now ready to run Apps!")
