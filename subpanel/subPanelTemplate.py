'''
Created on Nov 19, 2012

@author: Ted Carancho
'''
import time
from PyQt4 import QtCore

class subpanel(object):
    '''This is a class that contains the methods required to add new subpanels to the Configurator
    You can override any of these functions by making new ones in the subpanel they will be used.
    Look at commMonitor.py for an example of how to add this subclass to your subpanel.
    '''

    def __init__(self):
        self.connected = False
        self.timer = None
        self.xml = None
        self.xmlSubPanel = None
        self.comm = None
        self.mainUi = None
        self.boardConfiguration = {}
               
    def initialize(self, commTransport, xml, mainWindow):
        '''This initializes your class with required external arguments'''
        self.comm = commTransport
        self.xml = xml
        self.mainUi = mainWindow
                
    def sendCommand(self, command):
        '''Send a serial command'''
        self.comm.write(command)
        time.sleep(0.150)
        
    def readData(self):
        '''This method reads a single response from the AeroQuad'''
        response = self.comm.read()
        return response
    
    def start(self, xmlSubPanel, boardConfiguration):
        '''This method starts a timer used for any long running loops in a subpanel'''
        self.xmlSubPanel = xmlSubPanel
        self.boardConfiguration = boardConfiguration
        if self.comm.isConnected() == True:
            telemetry = self.xml.find(xmlSubPanel + "/Telemetry").text
            if telemetry != None:
                self.comm.write(telemetry)
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.readContinuousData)
            self.timer.start(10)

    def readContinuousData(self):
        '''This method continually reads telemetry from the AeroQuad'''
        if self.comm.isConnected() == True: 
            if self.comm.dataAvailable():           
                rawData = self.comm.read()
                data = rawData.split(",")
                for i in data:
                    print(i) # Replace this with desired functionality

    def stop(self):
        '''This method enables a flag which closes the continuous serial read thread'''
        if self.comm.isConnected() == True:
            if self.timer != None:
                self.comm.write(self.xml.find("./Settings/StopTelemetry").text)
                self.comm.flushResponse()
                self.timer.timeout.disconnect(self.readContinuousData)
                self.timer.stop()
        
    def timeStamp(self):
        '''Records a timestamp for AeroQuad communication'''
        now = time.time()
        localtime = time.localtime(now)
        milliseconds = '%03d' % int((now - int(now)) * 1000)
        return time.strftime('%H:%M:%S.', localtime) + milliseconds

    def status(self, message):
        self.mainUi.status.setText(message)
    
    def checkRequirementsMatch(self, xmlRequirementPath):
        # Read requirements for the specified subpanel form the XML config file
        subPanelRequirements = self.xml.findall(xmlRequirementPath)
        panelRequirements = {}
        booleanOperation = {}      
        for requirements in subPanelRequirements:
            requirement = requirements.text.split(':')
            if requirement[0] == "All": # Need element 1 populated if "All" detected
                requirement.append("All")
            panelRequirements[requirement[0]] = requirement[1].strip()
            booleanOperation[requirement[0]] = requirements.get("type")

        # Go through each subpanel requirement and check against board configuration
        # If no boolean type defined, assume AND
        requirementType = panelRequirements.keys()
        # If no Requirement found, assume ALL
        try:
            if (requirementType[0] == "All"):
                check = True
            else:
                check = any(panelRequirements[requirementType[0]] in s for s in self.boardConfiguration.values())
                for testRequirement in requirementType[1:]:
                    if (booleanOperation[testRequirement] == "or") or (booleanOperation[testRequirement] == "OR"):
                        check = check or any(panelRequirements[testRequirement] in s for s in self.boardConfiguration.values())
                    else:
                        check = check and any(panelRequirements[testRequirement] in s for s in self.boardConfiguration.values())
        except:
            check = True
        return check