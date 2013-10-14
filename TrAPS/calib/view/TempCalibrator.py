import sys
import os
from bisect import bisect
from time import time
import csv

from PyQt4 import QtCore, QtGui
from numpy import arange, average, fft
import numpy as np
import xlwt

from ...common.Temperature import TemperatureDevice, CalibrationRange
from ..model import DataItem
import calib_ui


import nidaqmx
daqSystem = nidaqmx.System()
daqDevices = daqSystem.devices
daqAnalogueInputsByDevice = [ device.get_analog_input_channels() for device in daqDevices ]
daqAnalogueInputs = ['']
for analogInputs in daqAnalogueInputsByDevice:
    daqAnalogueInputs.extend(analogInputs)

#daqAnalogueInputs = ['Dev1/ai2', 'Dev1/ai3']


#import traps.controller.TemperatureDevice as TemperatureDevice

app = QtGui.QApplication([])


class MainWindow(QtGui.QWidget):
    aquire = QtCore.pyqtSignal()
    setupDevices = QtCore.pyqtSignal()
    closing = QtCore.pyqtSignal()
    calLoadCurve = QtCore.pyqtSignal(str)
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.homedir = os.path.expanduser('~')
        
        self.ui = calib_ui.Ui_Form()
        self.ui.setupUi(self)
        
        self.ui.calDevInput.addItems(daqAnalogueInputs)
        self.ui.calDevInput.setCurrentIndex(0)
        self.ui.newDevInput.addItems(daqAnalogueInputs)
        self.ui.newDevInput.setCurrentIndex(0)
        
        self.ui.calTreeWidget.curveDataColumns = [0, 1]
        self.ui.calTreeWidget.sortByTemp()
        self.ui.newTreeWidget.curveDataColumns = [2, 0]
        self.ui.newTreeWidget.comparativeDataColumns = [1, 0]
        self.ui.newTreeWidget.sortByTemp()
        
        self.ui.loadCalibButton.clicked.connect(self.loadCalib)
        
        self.tempController = TempController()
        self.tempThread = QtCore.QThread(self)
        self.tempController.moveToThread(self.tempThread)
        self.tempThread.start()
        
        self.setupDevices.connect(self.tempController.setupDevices)
        self.setupDevices.emit()
        
        start_time = time()
        while not hasattr(self.tempController, 'cal_device'):
            if time() - start_time > 5000:
                print 'Taking ages!'
        
        self.ui.trigMax.valueChanged[int].connect(self.tempController.cal_device.setMaxTrigger)
        self.ui.trigMin.valueChanged[int].connect(self.tempController.cal_device.setMinTrigger)
        self.ui.trigSteps.valueChanged[int].connect(self.tempController.cal_device.setTriggerSteps)
        self.ui.trigDelta.valueChanged[float].connect(self.tempController.cal_device.setTriggerDelta)
        self.tempController.cal_device.viewChanged.connect(self.updateViewFromTemp)
        
        self.ui.aquireButton.clicked.connect(self.startAquiring)
        self.aquire.connect(self.tempController.startAquiring)
        self.tempController.cal_device.aquireComplete.connect(self.endAquiring)
        
        self.calLoadCurve.connect(self.tempController.cal_device.loadCalibrationCSV)
        
        self.closing.connect(self.tempController.close)
        self.tempController.closed.connect(self.closedNicely)
        
        self.ui.calDevInput.currentIndexChanged[str].connect(self.tempController.cal_device.connectDAQ)
        self.ui.newDevInput.currentIndexChanged[str].connect(self.tempController.new_device.connectDAQ)
        
        self.tempController.newDataPoint.connect(self.addNewCalibData)
        self.ui.mplWidget.needMoreLiveData.connect(self.tempController.sendNewData)
        
        #self.tempController.cal_device.dataChanged.connect(self.ui.calTreeWidget.replaceData)
        
        self.ui.calTreeWidget.dataChanged.connect(self.tempController.cal_device.loadCalibrationData)
        self.ui.calTreeWidget.dataReadyToShow.connect(self.ui.mplWidget.drawCalData)
        self.ui.newTreeWidget.dataChanged.connect(self.tempController.new_device.loadCalibrationData)
        self.ui.newTreeWidget.dataReadyToShow.connect(self.ui.mplWidget.drawNewData)
        
        #self.tempController.cal_device.curveChanged.connect(self.calCurveChanged)
        self.tempController.cal_device.dataAndCurveChanged.connect(self.calChanged)
        #self.tempController.new_device.curveChanged.connect(self.newCurveChanged)
        self.tempController.new_device.dataAndCurveChanged.connect(self.newChanged)
        
        self.ui.loadComparitiveDataButton.clicked.connect(self.importComparativeData_stepOne)
        self.fit_function = lambda x : float('NaN')
        self.tempImporter = CalTempDevice()
        self.tempImporter.dataAndCurveChanged.connect(self.importComparativeData_stepTwo)
        
        self.tempController.cal_device.updateHeaders.connect(self.updateCalHeaders)
        self.tempImporter.updateHeaders.connect(self.updateNewHeaders)
        
    @QtCore.pyqtSlot()
    def startAquiring(self):
        self.ui.tempControlWidget.setDisabled(True)
        self.ui.tempTriggerCheckBox.setDisabled(True)
        self.ui.aquireButton.setText('Stop Aquiring')
        self.ui.aquireButton.clicked.disconnect(self.startAquiring)
        self.ui.aquireButton.clicked.connect(self.tempController.stopAquiring)
        self.aquire.emit()
        
    @QtCore.pyqtSlot()
    def endAquiring(self):
        self.ui.tempTriggerCheckBox.setDisabled(False)
        if self.ui.tempTriggerCheckBox.checkState() == QtCore.Qt.Checked:
            self.ui.tempControlWidget.setDisabled(False)
        self.ui.aquireButton.setText('Aquire!')
        self.ui.aquireButton.clicked.disconnect(self.tempController.stopAquiring)
        self.ui.aquireButton.clicked.connect(self.startAquiring)
    
    @QtCore.pyqtSlot(dict)
    def updateViewFromTemp(self, data):
        self.ui.trigMax.valueChanged[int].disconnect(self.tempController.cal_device.setMaxTrigger)
        self.ui.trigMin.valueChanged[int].disconnect(self.tempController.cal_device.setMinTrigger)
        self.ui.trigSteps.valueChanged[int].disconnect(self.tempController.cal_device.setTriggerSteps)
        self.ui.trigDelta.valueChanged[float].disconnect(self.tempController.cal_device.setTriggerDelta)
        
        self.ui.trigMax.setValue(data['trigMax'])
        self.ui.currentTempSlider.setMaximum(data['trigMax'])
        self.ui.trigMin.setValue(data['trigMin'])
        self.ui.currentTempSlider.setMinimum(data['trigMin'])
        self.ui.trigSteps.setValue(data['trigSteps'])
        self.ui.trigDelta.setValue(data['trigDelta'])
        self.ui.currentTempSlider.setTickInterval(data['trigDelta'])
        self.ui.currentTempText.setText("%.1f K" %data['temp_oneDP'])
        self.ui.currentTempSlider.setValue(int(data['temp_oneDP']))
        
        self.ui.trigMax.valueChanged[int].connect(self.tempController.cal_device.setMaxTrigger)
        self.ui.trigMin.valueChanged[int].connect(self.tempController.cal_device.setMinTrigger)
        self.ui.trigSteps.valueChanged[int].connect(self.tempController.cal_device.setTriggerSteps)
        self.ui.trigDelta.valueChanged[float].connect(self.tempController.cal_device.setTriggerDelta)
    
    @QtCore.pyqtSlot(list, object)
    def calChanged(self, calib_data, fit_function):
        self.fit_function = fit_function
        self.ui.calibLabel.setText(self.calLoadCurve_filename)
        
        # Update cal data in calTreeWidget
        self.ui.calTreeWidget.replaceData(calib_data)
        updated_cal_data = self.ui.calTreeWidget.getCurveData()
        self.ui.calTreeWidget.dataReadyToShow.emit(updated_cal_data)
        
        # Update calculated temperatures in newTreeWidget
        temp_column = self.ui.newTreeWidget.curveDataColumns[0]
        calib_volt_column = self.ui.newTreeWidget.comparativeDataColumns[0]
        self.ui.newTreeWidget.mapFuncFromTo(fit_function, calib_volt_column, temp_column)
        update_new_data = self.ui.newTreeWidget.getCurveData()
        self.ui.newTreeWidget.dataChanged.emit(update_new_data)
        self.ui.newTreeWidget.dataReadyToShow.emit(update_new_data)
        
        # Update cal curve in graph
        volt_column = self.ui.calTreeWidget.curveDataColumns[1]
        volt_range = self.ui.calTreeWidget.getRangeInColumn(volt_column)
        if not containsNaN(volt_range):
            self.ui.mplWidget.drawCalCurve(fit_function, volt_range)
        else:
            print 'had a NaN in MainWindow.calCurveChanged'
        
    @QtCore.pyqtSlot(list, object)
    def newChanged(self, calib_data, fit_function):
        # Update new curve in graph
        volt_column = self.ui.newTreeWidget.curveDataColumns[1]
        volt_range = self.ui.newTreeWidget.getRangeInColumn(volt_column)
        if not containsNaN(volt_range):
            self.ui.mplWidget.drawNewCurve(fit_function, volt_range)
        
    def loadCalib(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Load calibrated device curve...", self.homedir, "Comma Separated Values (*.csv)")
        if filename == '':
            return
        self.calLoadCurve_filename = str(filename)
        self.calLoadCurve.emit(str(filename))
        
    @QtCore.pyqtSlot(float, float, float, bool)
    def processNewData(cal_volt, temp, new_volt, save):
        if save == True:
            self.addNewCalibData(cal_volt, temp, new_volt)
        else:
            self.ui.mplWidget.setLiveData(cal_volt, temp, new_volt)
    
    def addNewCalibData(self, cal_volt, temp, new_volt):
        # Just captured data from new, that can go back into new's calibration data
        new_data = DataItem(self.ui.newTreeWidget, [new_volt, cal_volt, temp])
        updated_data = self.ui.newTreeWidget.getCurveData()
        
        self.ui.newTreeWidget.dataChanged.emit(updated_data)
        self.ui.newTreeWidget.dataReadyToShow.emit(updated_data)

                
    def closeEvent(self, ev):
        self.closing.emit()
            
    def closedNicely(self):
        app.quit()
        
    def importComparativeData_stepOne(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Load comparative data...", self.homedir, "Comma Separated Values (*.csv)")
        if filename == '':
            return
    
        self.tempImporter.loadCalibrationCSV(filename)
        
    def importComparativeData_stepTwo(self, calib_data, rubbish_fit_function):
        self.ui.newTreeWidget.appendComparativeData(calib_data)
        
        cal_volt_column = self.ui.newTreeWidget.comparativeDataColumns[0]
        temp_column = self.ui.newTreeWidget.curveDataColumns[0]
        self.ui.newTreeWidget.mapFuncFromTo(self.fit_function, cal_volt_column, temp_column)
        
        update_new_data = self.ui.newTreeWidget.getCurveData()
        self.ui.newTreeWidget.dataChanged.emit(update_new_data)
        self.ui.newTreeWidget.dataReadyToShow.emit(update_new_data)
        
    def updateCalHeaders(self, headers_patch):
        headers = [ self.ui.calTreeWidget.headerItem().text(i) 
                    for i in range(self.ui.calTreeWidget.columnCount()) ]
        
        volt_column = self.ui.calTreeWidget.curveDataColumns[1]
        headers[volt_column] = headers_patch[1]
        
        self.ui.calTreeWidget.setHeaderLabels(headers)
        self.ui.mplWidget.leftLabel = "Calibrated device: %s" %headers[volt_column]
        self.ui.mplWidget.updateYAxes()
        
        
    def updateNewHeaders(self, headers_patch):
        headers = [ self.ui.newTreeWidget.headerItem().text(i) 
                    for i in range(self.ui.newTreeWidget.columnCount()) ]
        
        cal_column = self.ui.newTreeWidget.comparativeDataColumns[0]
        new_column = self.ui.newTreeWidget.comparativeDataColumns[1]
        headers[cal_column] = headers_patch[0]
        headers[new_column] = headers_patch[1]
        
        self.ui.newTreeWidget.setHeaderLabels(headers)
        self.ui.mplWidget.rightLabel = "New device: %s" %headers[new_column]
        self.ui.mplWidget.updateYAxes()
        

class TempController(QtCore.QObject):
    newDataPoint = QtCore.pyqtSignal(float, float, float, bool)
    closed = QtCore.pyqtSignal()
    
    
    def setupDevices(self):
        self.new_device = CalTempDevice()
        self.cal_device = CalTempDevice()
        self.cal_device.setMaxTrigger(330)
        self.cal_device.setMinTrigger(0)
        self.cal_device.setTriggerDelta(1.0)
        self.cal_device.trigger.connect(self.triggered)
        
        self.new_device.reset()
        self.cal_device.reset()
        
        
    def startAquiring(self):
        self.cal_device.updateTriggerTemps()
        self.cal_device.aquiring = True
            
    def stopAquiring(self):
        self.cal_device.reset()
            
    def triggered(self):
        self.sendNewData(save = True)
            
    def sendNewData(self, save=False):
        cal_volt = self.cal_device.volt
        temp = self.cal_device.temp
        new_volt = self.new_device.volt
        
        if not containsNaN([cal_volt, temp, new_volt]):
            self.newDataPoint.emit(cal_volt, temp, new_volt, save)
        else:
            print 'Failed to save: new_volt=%f, temp=%f' %(new_volt, temp)
            
    def close(self):
        self.cal_device.closeDevice()
        self.new_device.closeDevice()
        self.closed.emit()
		
    	
class CalTempDevice(TemperatureDevice):
    curveChanged = QtCore.pyqtSignal(object)
    dataChanged = QtCore.pyqtSignal(list)
    dataAndCurveChanged = QtCore.pyqtSignal(list, object)
    updateHeaders = QtCore.pyqtSignal(list)
    
    def __init__(self, *args, **kwargs):
        TemperatureDevice.__init__(self, *args, **kwargs)
        self.loadCalibrationSuccess.connect(self.sendNewData)
    
    @QtCore.pyqtSlot(bool)
    def sendNewData(self, success):
        if success:
            self.dataAndCurveChanged.emit(self.calib_data, self.fit_function)
            if len(self.headers) == 2:
                self.updateHeaders.emit(self.headers)
        
def containsNaN(lst):
    NaN_values = [ np.isnan(val) for val in lst ]
    return True in NaN_values
            
def startApp():
    mainWindow = MainWindow()
    mainWindow.show()
    
    sys.exit(app.exec_())
