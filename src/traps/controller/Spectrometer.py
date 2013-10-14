from time import time, sleep

from PyQt4 import QtCore, QtGui

REAL = False

if REAL:
    from SpectrometerDll import SpectrometerDevice
else:
    from SpecDummy import SpectrometerDevice
from ...common.Temperature import TemperatureDevice
SpectrometerWorkerClass = 0

from ..model import singleton, Variable, DB


class SpectrometerWorkerClass(QtCore.QObject):
    newSpectrum = QtCore.pyqtSignal(list, float)
    deviceConnected = QtCore.pyqtSignal()
    deviceDisconnected = QtCore.pyqtSignal()
    liveUpdated = QtCore.pyqtSignal(list, float)
    newWavelengths = QtCore.pyqtSignal(list)
    closed = QtCore.pyqtSignal()
    aquireComplete = QtCore.pyqtSignal(bool)
    
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.device = SpectrometerDevice()
    
    def initialise(self):
        self.temperatureDevice = TemperatureDevice(self)
        self.temperatureDevice.trigger.connect(self.aquire)
        self.temperatureDevice.aquireComplete.connect(self.aquireComplete)
        self.tempTrigger = False
        self.startTime = 0
        self.refresh_interval = 500
        self.getWavelengths()
        #self.liveVariable = DB.Variable.textDict['live']
        #self.liveUpdated.connect(self.liveVariable.updateLiveData)
        
        #self.temperatureDevice.measure()
        
    @QtCore.pyqtSlot()
    def connectSpectrometer(self):
        try:
            self.device = SpectrometerDevice()
        except:
            self.deviceDisconnected.emit()
            return
        self.deviceConnected.emit()
     
    @QtCore.pyqtSlot()
    def close(self):
        self.device.close()
        self.temperatureDevice.close()
        self.closed.emit()
     
    def getWavelengths(self):
        print 'getting wavelengths...'
        self.newWavelengths.emit(self.device.wavelengths)
     
    @QtCore.pyqtSlot()
    def disconnectSpectrometer(self):
        if self.device is not None:
            self.device.close()
        self.device = None
    
    @QtCore.pyqtSlot(int)
    def setIntegrationTime(self, time):
        if self.device is None:
            return
        self.device.setIntTime(time*1000)
        
    @QtCore.pyqtSlot(int)
    def setTrigger(self, triggerType):
        if self.device is None:
            return
        self.device.setTrigger(triggerType)
        
    @QtCore.pyqtSlot()
    def getSpectrum(self):
        if self.device is None:
            return
        return self.device.getSpectrum()
        """
        spec = list(self.temperatureDevice.getTempSampleSpectrum())
        spec.extend( [0.0] * (len(self.device.wavelengths) - len(spec)) )
        if len(spec) > len(self.device.wavelengths):
            spec = spec[:len(self.device.wavelengths)]
        #print 'spec contains: %s' %`spec[:10]`
        #print 'len(x)=%d , len(y)=%d' %(len(self.device.wavelengths), len(spec))
        if len(spec) == len(self.device.wavelengths):
            return spec
        else:
            return self.device.getSpectrum()
        """
            
        
    
    @QtCore.pyqtSlot()
    def startAquiring(self):
        if self.tempTrigger:
            self.temperatureDevice.aquiring = True
        else:
            self.aquire()
            self.aquireComplete.emit(True)
        
    @QtCore.pyqtSlot()
    def aquire(self):
        self.newSpectrum.emit(self.device.getSpectrum(), self.temperatureDevice.temp)
        
    @QtCore.pyqtSlot(int)
    def tempTriggerChecked(self, state):
        if state == QtCore.Qt.Checked:
            self.tempTrigger = True
        else:
            self.tempTrigger = False
        
    @QtCore.pyqtSlot()
    def updateLive(self):
        delta_time = time() - self.startTime
        wait_correction = self.refresh_interval - delta_time*1000
        """
        if wait_correction > 0:
            QtCore.QTimer.singleShot(wait_correction, self.updateLiveNow)
        else:
            self.updateLiveNow()
        """
        self.updateLiveNow()
        
    def updateLiveNow(self):
        data = self.getSpectrum()
        self.liveUpdated.emit(data, self.temperatureDevice.temp)
        self.startTime = time()

    @QtCore.pyqtSlot(int)
    def setLivePollRate(self, refresh_interval):
        self.refresh_interval = refresh_interval