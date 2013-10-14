import sys
import os
import Queue
from time import sleep, time

from PyQt4 import QtCore, QtGui

from ..model import DB
from ..controller import SpectrometerWorkerClass
import hardware_ui
         
         
class HardwareWidget(QtGui.QWidget):
    needMoreData = QtCore.pyqtSignal()
    liveUpdated = QtCore.pyqtSignal(list, float)
    aquire = QtCore.pyqtSignal()
    loadTempCalibration = QtCore.pyqtSignal(str)
    loadDAQDevice = QtCore.pyqtSignal(str)
    initialiseSpectrometer = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = hardware_ui.Ui_Form()
        self.ui.setupUi(self)
        
        self.spectrometerWorker = SpectrometerWorkerClass()
        self.spectrometerWorker.newWavelengths.connect(DB.updateWavelengths)
        self.spectrometerWorker.getWavelengths()
        
        self.spectrometerThread = QtCore.QThread(self)
        self.spectrometerWorker.moveToThread(self.spectrometerThread)
        self.spectrometerThread.start()
        
        self.initialiseSpectrometer.connect(self.spectrometerWorker.initialise)
        self.initialiseSpectrometer.emit()
        
        while not hasattr(self.spectrometerWorker, 'temperatureDevice'):
            pass
        
        #self.tempTimer = QtCore.QTimer(self)
        #self.tempTimer.timeout.connect(self.spectrometerWorker.temperatureDevice.measure)
        #self.tempTimer.start(int(1000/60))
        
        self.ui.integrationTime.valueChanged[int].connect(self.spectrometerWorker.setIntegrationTime)
        
        self.ui.tempTriggerCheckBox.stateChanged.connect(self.spectrometerWorker.tempTriggerChecked)
        
        self.ui.livePoll.clicked.emit(True)
        
        self.liveQueue = Queue.Queue()
        self.maxQueueLen = 1
        
        self.needMoreData.connect(self.spectrometerWorker.updateLive)
        
        self.liveVariable = DB.Variable.textDict['live']
        self.liveVariable.needMoreData.connect(self.getMoreLiveDataASAP)
        self.liveUpdated.connect(self.liveVariable.updateLiveData)
        
        self.spectrometerWorker.liveUpdated.connect(self.addMoreLiveData)
        
        self.askedForData = 0
        self.sendNextData = False
        
        self.ui.livePoll.stateChanged.connect(self.setAutoLiveUpdate)
        self.ui.livePollRate.valueChanged[int].connect(self.spectrometerWorker.setLivePollRate)
        self.ui.livePollButton.clicked.connect(self.getMoreLiveDataASAP)
        
        self.ui.aquireButton.clicked.connect(self.startAquiring)
        self.aquire.connect(self.spectrometerWorker.startAquiring)
        self.spectrometerWorker.aquireComplete.connect(self.endAquiring)
        
        self.spectrometerWorker.newSpectrum.connect(DB.newData)
        self.ui.trigMax.valueChanged[int].connect(self.spectrometerWorker.temperatureDevice.setMaxTrigger)
        self.ui.trigMin.valueChanged[int].connect(self.spectrometerWorker.temperatureDevice.setMinTrigger)
        self.ui.trigSteps.valueChanged[int].connect(self.spectrometerWorker.temperatureDevice.setTriggerSteps)
        self.ui.trigDelta.valueChanged[float].connect(self.spectrometerWorker.temperatureDevice.setTriggerDelta)
        self.spectrometerWorker.temperatureDevice.viewChanged.connect(self.updateViewFromTemp)
        #self.spectrometerWorker.temperatureDevice.measure()
        
        self.loadDAQDevice.connect(self.spectrometerWorker.temperatureDevice.connectDAQ)
        self.loadDAQDevice.emit('Dev1/ai2')
        
        self.ui.loadCalibButton.clicked.connect(self.popupCalibrationDialog)
        self.loadTempCalibration.connect(self.spectrometerWorker.temperatureDevice.loadCalibrationCSV)
        self.spectrometerWorker.temperatureDevice.loadCalibrationSuccess.connect(self.updateCalibView)
        self.homedir = os.path.expanduser('~')
        
        self.ui.dataSetComboBox.setModel(DB.DataSet)
        self.ui.dataSetComboBox.setModelColumn(1)
        self.ui.dataSetComboBox.setInsertPolicy(QtGui.QComboBox.InsertAtCurrent)
        self.ui.addDataSet.clicked.connect(self.addDataSet)
        self.ui.deleteDataSet.clicked.connect(self.deleteDataSet)
        self.ui.notesEditor.textChanged.connect(self.changeDataSetNotes)
        self.addDataSet()
        
        self.ui.dataSetComboBox.currentIndexChanged.connect(self.activateDataSet)
        
        
    @QtCore.pyqtSlot()
    def startAquiring(self):
        self.ui.tempControlWidget.setDisabled(True)
        self.ui.tempTriggerCheckBox.setDisabled(True)
        self.ui.aquireButton.setText('Stop Aquiring')
        self.ui.aquireButton.clicked.disconnect(self.startAquiring)
        self.ui.aquireButton.clicked.connect(self.spectrometerWorker.temperatureDevice.reset)
        self.aquire.emit()
        
    @QtCore.pyqtSlot()
    def endAquiring(self):
        self.ui.tempTriggerCheckBox.setDisabled(False)
        if self.ui.tempTriggerCheckBox.checkState() == QtCore.Qt.Checked:
            self.ui.tempControlWidget.setDisabled(False)
        self.ui.aquireButton.setText('Aquire!')
        self.ui.aquireButton.clicked.disconnect(self.spectrometerWorker.temperatureDevice.reset)
        self.ui.aquireButton.clicked.connect(self.startAquiring)
        
    @QtCore.pyqtSlot(dict)
    def updateViewFromTemp(self, data):
        self.ui.trigMax.valueChanged[int].disconnect(self.spectrometerWorker.temperatureDevice.setMaxTrigger)
        self.ui.trigMin.valueChanged[int].disconnect(self.spectrometerWorker.temperatureDevice.setMinTrigger)
        self.ui.trigSteps.valueChanged[int].disconnect(self.spectrometerWorker.temperatureDevice.setTriggerSteps)
        self.ui.trigDelta.valueChanged[float].disconnect(self.spectrometerWorker.temperatureDevice.setTriggerDelta)
        
        self.ui.trigMax.setValue(data['trigMax'])
        self.ui.currentTempSlider.setMaximum(data['trigMax'])
        self.ui.trigMin.setValue(data['trigMin'])
        self.ui.currentTempSlider.setMinimum(data['trigMin'])
        self.ui.trigSteps.setValue(data['trigSteps'])
        self.ui.trigDelta.setValue(data['trigDelta'])
        self.ui.currentTempSlider.setTickInterval(data['trigDelta'])
        self.ui.currentTempText.setText("%.1f K" %data['temp_oneDP'])
        self.ui.currentTempSlider.setValue(int(data['temp_oneDP']))
        
        self.ui.trigMax.valueChanged[int].connect(self.spectrometerWorker.temperatureDevice.setMaxTrigger)
        self.ui.trigMin.valueChanged[int].connect(self.spectrometerWorker.temperatureDevice.setMinTrigger)
        self.ui.trigSteps.valueChanged[int].connect(self.spectrometerWorker.temperatureDevice.setTriggerSteps)
        self.ui.trigDelta.valueChanged[float].connect(self.spectrometerWorker.temperatureDevice.setTriggerDelta)
        
    def setAutoLiveUpdate(self, state):
        if state == QtCore.Qt.Checked:
            self.liveVariable.needMoreData.connect(self.getMoreLiveDataASAP)
            self.ui.livePollRate.valueChanged[int].emit(self.ui.livePollRate.value())
            self.getMoreLiveDataASAP()
        else:
            self.liveVariable.needMoreData.disconnect(self.getMoreLiveDataASAP)
            self.ui.livePollRate.valueChanged[int].emit(0)
        
    @QtCore.pyqtSlot()
    def getMoreLiveDataASAP(self):
        if self.liveQueue.empty():
            self.sendNextData = True
        else:
            self.liveUpdated.emit(*self.liveQueue.get())
        
        for i in range(self.liveQueue.qsize(), self.maxQueueLen - self.askedForData):
            self.getMoreLiveDataQueued()
            
    def getMoreLiveDataQueued(self):
        self.needMoreData.emit()
        self.askedForData += 1
        
    @QtCore.pyqtSlot(list, float)
    def addMoreLiveData(self, data, temp):
        self.askedForData -= 1
        if self.sendNextData:
            self.getting = False
            self.sendNextData = False
            self.liveUpdated.emit(data, temp)
        else:
            self.liveQueue.put([data, temp])
        
    @QtCore.pyqtSlot()
    def addDataSet(self):
        name = 'New DataSet'
        notes = 'Notes'
        DB.DataSet.appendRow(name, notes)
        row = self.ui.dataSetComboBox.count()-1
        self.ui.dataSetComboBox.setCurrentIndex(row)
        DB.currentDataSet = row
        
    @QtCore.pyqtSlot(int)
    def activateDataSet(self, row):
        if row == -1:
            self.addDataSet()
            return
        dataSet_index = int(DB.DataSet.item(row, 0).text())
        DB.currentDataSet = row
        
        notes_item = DB.DataSet.item(row, 2)
        self.ui.notesEditor.textChanged.disconnect(self.changeDataSetNotes)
        self.ui.notesEditor.setText(notes_item.text())
        self.ui.notesEditor.textChanged.connect(self.changeDataSetNotes)
        
    @QtCore.pyqtSlot()
    def changeDataSetNotes(self):
        row = self.ui.dataSetComboBox.currentIndex()
        
        notes_item = DB.DataSet.item(row, 2)
        notes = self.ui.notesEditor.toPlainText()
        notes_item.setText(notes)
    
    @QtCore.pyqtSlot()
    def deleteDataSet(self):
        current_index = self.ui.dataSetComboBox.currentIndex()
        self.ui.dataSetComboBox.removeItem(current_index)
        
    @QtCore.pyqtSlot()
    def popupCalibrationDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Load temperature calibration curve", self.homedir, "Comma Separated Values (*.csv)")
        filename = str(filename)
        if not filename == '':
            self.loadTempCalibrationFile(filename)
       
    @QtCore.pyqtSlot()
    def loadTempCalibrationFile(self, filename):
        self.calibFileName = os.path.basename(filename)
        self.homedir = os.path.dirname(str(filename))
        self.loadTempCalibration.emit(filename)
        
    @QtCore.pyqtSlot(bool)
    def updateCalibView(self, success):
        if success:
            self.ui.calibLabel.setText(self.calibFileName)
        else:
            QtGui.QMessageBox(QtGui.QMessageBox.Warning, "Calibration curve invalid", "The calibration curve '%s' is invalid.  Check the example curve files to see how it should be formatted.", QtGui.QMessageBox.Ok)