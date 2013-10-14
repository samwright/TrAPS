import sys
import csv
from time import time

from PyQt4 import QtCore, QtGui
from bisect import bisect
from numpy import arange, average, fft
import numpy as np

REAL = False

if REAL:
    from nidaqmx import AnalogInputTask

INPUT_CHANNEL = 'Dev1/ai3'
MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 3.0

POLL_RATE = 10000
SAMPLE_RATE = 60



class TemperatureDevice(QtCore.QObject):
    trigger = QtCore.pyqtSignal()
    viewChanged = QtCore.pyqtSignal(dict)
    aquireComplete = QtCore.pyqtSignal(bool)
    loadCalibrationSuccess = QtCore.pyqtSignal(bool)
    
    def __init__(self, parent=None, minV=MIN_VOLTAGE, maxV=MAX_VOLTAGE):
        QtCore.QObject.__init__(self, parent)
        self.minV = minV
        self.maxV = maxV
        
        self.temp_oneDP = 0
        self.triggerTemps = []
        self.triggeredTemps = set()
        self.emitOnTempChangingBy = 0.1
        
        self.device = None
        self.closeDevice()
        self.fit_function = lambda x : float('NaN')
        
        self.trigMax = 280
        self.trigMin = 10
        self.trigSteps = 10
        self.trigDelta = None
        self.updateTriggerTemps()
        
        self.calib_data = []
        
        self.spec = [0] * 200
        self.startTime = time()
    
    @QtCore.pyqtSlot(str)
    def loadCalibrationCSV(self, filename):
        
        try:
            ifile = open(filename, 'r')
        except IOError:
            print "Couldn't load calibration data"
            self.loadCalibrationSuccess.emit(False)
            return
        
        reader = csv.reader(ifile)
        self.loadCalibrationData(reader)
        
    @QtCore.pyqtSlot(object)
    def loadCalibrationData(self, iterable_data):
        old_calib_data = self.calib_data
        self.calib_data = []
        
        calib_range = CalibrationRange()
        self.calib_data.append(calib_range)
        for row in iterable_data:
            try:
                assert len(row) == 2
                temp = float(row[0])
                voltage = float(row[1])
                calib_range.addData(temp, voltage)
            except (TypeError, IndexError, ValueError, AssertionError):
                if len(row) == 2 and self.headers == []:
                    self.headers = row
                calib_range = CalibrationRange()
                self.calib_data.append(calib_range)
                try:
                    calib_range.addFinalData(temp, voltage)
                except UnboundLocalError:
                    pass
                
        empty_ranges = [ data_range for data_range in self.calib_data if data_range.isEmpty() ]
        for empty_range in empty_ranges:
            self.calib_data.remove(empty_range)
                
        if len(self.calib_data) == 0:
            print "No useful data found in supplied data"
            self.loadCalibrationSuccess.emit(False)
            self.calib_data = old_calib_data
            return
            
        for calib_range in self.calib_data:
            calib_range.evaluate()
            
        self.fit_function = FitFunction(self.calib_data)
            
        self.loadCalibrationSuccess.emit(True)
        if hasattr(iterable_data, 'close'):
            iterable_data.close()
                
    @QtCore.pyqtSlot(str)
    def connectDAQ(self, channel):
        print 'connecting daq from channel %s' %channel
        self.closeDevice()
            
        if channel == '':
            return
            
        if REAL == True:
            self.device = AnalogInputTask()
            assert self.device.create_voltage_channel(
                            str(channel),
                            terminal = 'diff',
                            min_val=self.minV, 
                            max_val=self.maxV
                            ) == True
        else:
            self.device = TempDummy()
            
        self.measure()
        #self.device.configure_timing_sample_clock(rate = POLL_RATE)
        #self.device.start()
        
    def close(self):
        self.closeDevice()
        
    def getTempSampleSpectrum(self):
        return self.spec
        
    @QtCore.pyqtSlot(int)
    def setMaxTrigger(self, maxTrigger):
        self.trigMax = maxTrigger
        self.updateTriggerTemps()
        
    @QtCore.pyqtSlot(int)
    def setMinTrigger(self, minTrigger):
        self.trigMin = minTrigger
        self.updateTriggerTemps()
        
    @QtCore.pyqtSlot(float)
    def setTriggerDelta(self, trigDelta):
        self.triggerTemps = list(arange(self.trigMin, self.trigMax, trigDelta))
        self.trigSteps = len(self.triggerTemps)
        if self.trigSteps == (self.trigMax - self.trigMin)//trigDelta:
            # If last value was missed off by arange, but should be included
            self.triggerTemps.append(self.trigMax)
            self.trigSteps += 1
        self.trigDelta = trigDelta
        #print 'my triggers are %s' %`self.triggerTemps`

        self.updateView()
        
    @QtCore.pyqtSlot(int)
    def setTriggerSteps(self, trigSteps):
        self.trigSteps = trigSteps
        self.updateTriggerTemps()
        
    def updateTriggerTemps(self):
        self.triggerTemps = list(np.linspace(self.trigMin, self.trigMax, self.trigSteps))
        if self.trigSteps > 1:
            self.trigDelta = self.triggerTemps[1] - self.triggerTemps[0]
        self.bisection = bisect(self.triggerTemps, self.temp)
        #print 'updated: my triggers are %s' %`self.triggerTemps`
        self.updateView()

    def updateView(self):
        self.viewChanged.emit(
                                dict(
                                        trigSteps = self.trigSteps,
                                        trigDelta = self.trigDelta,
                                        trigMax = self.trigMax,
                                        trigMin = self.trigMin,
                                        temp_oneDP = self.temp_oneDP
                                    )
                                )
    
    @QtCore.pyqtSlot(list)
    def updateFromView(self, data):
        self.setTriggerDelta(data['trigDelta'])
        self.setTriggerSteps(data['trigSteps'])
        self.setTriggerMax(data['trigMax'])
        self.setTriggerMin(data['trigMin'])
        
    
        
    def convertVoltToTemp(self, volt):
        return self.fit_function(volt)
        
        
    @QtCore.pyqtSlot()
    def measure(self):
        if self.device == None:
            return
        #vValues = self.device.read(int(POLL_RATE/SAMPLE_RATE))
        vValues = self.device.read(1024)
        #vValues = self.device.read()
        
        #fourier = np.fft.fftshift(np.fft.fft(vValues).flatten())
        #fourier = np.fft.fft(vValues).flatten()
        #self.spec = [np.abs(val) for val in fourier]
        #print 'spec is %s' %`self.spec`
        #central_ft = np.fft.ifft(self.spec[0])
        #self.temp = central_ft * 100
        #print 'Reading temp values of length %d ' %len(vValues)
        #vValues = bandFilter(vValues)
        vAverage = np.average(vValues)
        previousAverages = [ val for val in self.spec[-1:] if val != 0 ]
        vAverage = np.average([vAverage] + previousAverages)
        del self.spec[0]
        self.spec.append(vAverage)
        
        # Approximate!!! (ie. negative temperatures...)
        self.volt = vAverage
        self.temp = self.convertVoltToTemp(vAverage)
        
        #print 'measuring T=%f' %self.temp
        #self.temp = 240
        #self.temp -= .5
        #self.temp = vAverage*100
        temp_oneDP = round(self.temp, 1)
        if self.temp_oneDP != temp_oneDP and not np.isnan(temp_oneDP):
            self.temp_oneDP = temp_oneDP
            if time() - self.startTime > 0.05:
                self.updateView()
                self.startTime = time()
        else:
            #print 'temp is %f, one_dp is %f' %(self.temp, temp_oneDP)
            pass
        
        new_bisection = bisect(self.triggerTemps, self.temp)
        if self.bisection != new_bisection and self.aquiring:
            upper_index = max(self.bisection, new_bisection)
            lower_index = min(self.bisection, new_bisection)
            #indices_to_remove = range(upper_index, lower_index, -1)
            #indices_covered = range(lower_index, upper_index)
            #print 'triggering because i moved from %f to %f' %(self.triggerTemps[self.bisection], self.triggerTemps[new_bisection])
            #for index in indices_to_remove:
            #    del self.triggerTemps[index]
            number_of_triggered_temps = len(self.triggeredTemps)
            self.triggeredTemps.update( self.triggerTemps[lower_index:upper_index] )
            if len(self.triggeredTemps) != number_of_triggered_temps:
                self.trigger.emit()
            if len(self.triggeredTemps) == len(self.triggerTemps):
                self.reset()
                
        self.bisection = new_bisection
        
        QtCore.QTimer.singleShot(0, self.measure)
                
    def reset(self):
        self.aquiring = False
        self.triggeredTemps = set()
        self.aquireComplete.emit(True)
        self.updateTriggerTemps()
        self.updateView()
        
    def closeDevice(self):
        if self.device != None:
            del self.device
            self.device = None
        self.temp = float('NaN')
        self.volt = float('NaN')
        
        self.aquiring = False
        self.bisection = None
        self.triggeredTemps = set()
        self.headers = []


class TempDummy:
    def __init__(self):
        self.volt_range = np.arange(0.293, 2.466, 0.00001)
        self.index = 0
        self.index_delta = +1
    
    def create_voltage_channel(self, *args, **kwargs):
        return True
    
    def read(self, num):
        self.index += self.index_delta
        if self.index == len(self.volt_range):
            self.index = len(self.volt_range) - 1
            self.index_delta = -1
        elif self.index < 0:
            self.index = 0
            self.index_delta = +1
        
        return self.volt_range[self.index]
        #return [500,510,520]
        
    def close(self):
        pass
    
    
def bandFilter(values, exclude_Hz=np.arange(55, 65)):
    fourier = np.fft.fft(values)
    
    scaled_exclude_Hz = Hz_to_remove * float(SAMPLE_TIME) / POLL_RATE
    for freq_to_remove in scaled_exclude_Hz:
        fourier[int(freq_to_remove)] = 0
        fourier[SAMPLE_TIME - int(freq_to_remove)] = 0
    return np.fft.ifft(fourier)
    

class CalibrationRange:
    def __init__(self):
        self.temps = []
        
        self.voltages = []
        self.max_voltage = None
        self.min_voltage = None
        
        self.polyFit = None
        
    def addData(self, temp, voltage):
        if self.isEmpty():
            self.max_voltage = voltage
            self.min_voltage = voltage
        else:
            if self.max_voltage < voltage:
                self.max_voltage = voltage
            if self.min_voltage > voltage:
                self.min_voltage = voltage
            
        self.temps.append(temp)
        self.voltages.append(voltage)
        self.polyFit = None
        self.lowerExtrapFunc = None
        self.higherExtrapFunc = None
        
    def addFinalData(self, temp, voltage):
        self.addData(temp, voltage)
        #self.temps.remove(temp)
        #self.voltages.remove(voltage)
        
    def isValidForVoltage(self, voltage):
        if None not in [ self.max_voltage, self.min_voltage ]:
            if self.min_voltage <= voltage < self.max_voltage:
                return True
        return False
        
    def evaluate(self, voltage=None):
        if self.isEmpty():
            return float('NaN')
            
        if not isinstance(self.polyFit, np.poly1d):
            coefs = np.polyfit(self.voltages, self.temps, 6)
            self.polyFit = np.poly1d(coefs)
            
            end_indices = len(self.voltages) // 4
            voltages_dict = dict(zip(self.voltages, self.temps))
            sorted_voltages = voltages_dict.keys()
            sorted_voltages.sort()
            
            first_voltages = sorted_voltages[:end_indices]
            first_temps = [ voltages_dict[volt] for volt in first_voltages ]
                
            last_voltages = sorted_voltages[-1-end_indices:]
            last_temps = [ voltages_dict[volt] for volt in last_voltages ]
            
            
            coefs = np.polyfit(first_voltages, first_temps, 1)
            self.lowerExtrapFunc = np.poly1d(coefs)
            
            coefs = np.polyfit(last_voltages, last_temps, 1)
            self.higherExtrapFunc = np.poly1d(coefs)
            
        if voltage != None:
            temp = float('NaN')
            if self.min_voltage < voltage < self.max_voltage:
                temp = self.polyFit(voltage)
            elif voltage < self.min_voltage:
                temp = self.lowerExtrapFunc(voltage)
            elif voltage > self.max_voltage:
                temp = self.higherExtrapFunc(voltage)
            #print 'min %f : volt %f : max %f => temp %f' %(self.min_voltage, voltage, self.max_voltage, temp)
            return temp
        
    def isEmpty(self):
        return self.temps == []
        
        
class FitFunction:
    def __init__(self, calib_data):
        self.calib_data = calib_data
        
    def __call__(self, volt):
        valid_calib_range = None
        for calib_range in self.calib_data:
            if calib_range.isValidForVoltage(volt):
                valid_calib_range = calib_range
                break
                
        if valid_calib_range == None:
            # Find closes min or max value
            deltaV_from_range = dict( (
                                min(
                                    abs(data_range.max_voltage-volt), 
                                    abs(data_range.min_voltage-volt)
                                    ), data_range)
                            for data_range in self.calib_data )
                                
            smallest_deltaV = min(deltaV_from_range.keys())
            valid_calib_range = deltaV_from_range[smallest_deltaV]
            
            
            #return float('Nan')
            #return volt
        
        return valid_calib_range.evaluate(volt)