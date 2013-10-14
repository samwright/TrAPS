import compiler
import re
from random import randrange
from collections import defaultdict

from PyQt4 import QtCore, QtGui
import numpy as np
from scipy.constants import h, c, e, pi

from helpers import *

re_all_names = re.compile('Name\(\'(.*?)\'\)')
re_funcs = re.compile('CallFunc\(Name\(\'(.*?)\'\)')

UNDEFINED = 0
ONE_SPECTRUM = 1
MANY_SPECTRA = 2


class SimpleModelObj(QtCore.QObject):
    def __init__(self, simpleDatabase):
        QtCore.QObject.__init__(self, simpleDatabase)
        
    def deleteLater(self):
        del self.parent().textDict[str(self.text())]
        QtCore.QObject.deleteLater(self)
        

class VariableListItem(QtGui.QListWidgetItem):
    def __init__(self, parent):
        QtGui.QListWidgetItem.__init__(self, parent, 0)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        parent.setCurrentItem(self)

        
class Variable(SimpleModelObj):
    SPECTRA = 0
    DATASET = 1
    
    def __init__(self, database, listWidget=None):
        SimpleModelObj.__init__(self, database)
        self.listWidget = listWidget
        if self.listWidget != None:
            self.item = VariableListItem(listWidget)
        self.oldText = ''
        #self.item.setText(text)
        self.variableType = Variable.DATASET
        self.spectra = []
        self.dataSet = []
        self.dataSetSpectra = []
        self.status = UNDEFINED
        self.dependentGraphs = []
        
    def text(self):
        return str(self.item.text())
        
    def getTemp(self):
        if self.variableType == Variable.SPECTRA:
            return DB.Data.getTempFromSpectra(self.spectra)
        elif self.variableType == Variable.DATASET:
            return DB.Data.getTempFromSpectra(self.dataSetSpectra)
        
    def delAndReturnIndex(self):
        self.spectra = []
        self.dataSet = []
        self.updateGraphs()
        if self.listWidget != None:
            row = self.listWidget.row(self.item)
            item = self.listWidget.takeItem(row)
            del item
            return row
        self.deleteLater()
        
    def getData(self):
        if self.variableType == Variable.SPECTRA:
            return DB.Data.getDataFromSpectra(self.spectra)
        elif self.variableType == Variable.DATASET:
            return DB.Data.getDataFromSpectra(self.dataSetSpectra)
        
    def textChanged(self):
        newText = self.text()
        for graph in DB.View.keys():
            new_and_old_texts = [self.oldText, newText]
            graph_needs_updating = bool(len(graph.all_deps.intersection(new_and_old_texts)))
            if graph_needs_updating:
                graph.updateDepName()
        self.oldText = newText
        
    def updateGraphs(self):
        
        if len(self.getData()) > 1:
            newStatus = MANY_SPECTRA
        elif len(self.getData()) == 1:
            newStatus = ONE_SPECTRUM
        else:
            newStatus = UNDEFINED
        """
        if newStatus != self.status:
            before_status_changed_dependentGraphs = self.dependentGraphs
            for graph in before_status_changed_dependentGraphs:
                graph.updateDepStatus()
        """
        self.status = newStatus
        for graph in DB.View.keys():
            graph.updateDepData()
        
    @QtCore.pyqtSlot(int)
    def changeVariableType(self, buttonClickedIndex):
        if buttonClickedIndex == QtCore.Qt.Checked:
            self.variableType = Variable.SPECTRA
        elif buttonClickedIndex == QtCore.Qt.Unchecked:
            self.variableType = Variable.DATASET
        self.updateGraphs()
        
    @QtCore.pyqtSlot(int, bool)
    def setSpectrumInclusion(self, row, included):
        if included:
            self.spectra.append(row)
        elif not included:
            self.spectra.remove(row)
        if self.variableType == Variable.SPECTRA:
            self.updateGraphs()
            
    @QtCore.pyqtSlot(int, bool)
    def setDataSetSpectrumInclusion(self, row, included):
        if included:
            self.dataSetSpectra.append(row)
        elif not included:
            self.dataSetSpectra.append(row)
        if self.variableType == Variable.DATASET:
            self.updateGraphs()
            
    @QtCore.pyqtSlot(list, bool)
    def setDataSetSpectraInclusion(self, rows, included):
        if included:
            self.dataSetSpectra.extend(rows)
        elif not included:
            updated_set = set(self.dataSetSpectra).difference(rows)
            self.dataSetSpectra = list(updated_set)
        if self.variableType == Variable.DATASET:
            self.updateGraphs()
            
    @QtCore.pyqtSlot(int, bool)
    def setDataSetInclusion(self, row, included):
        if included:
            self.dataSet.append(row)
        elif not included:
            self.dataSet.append(row)

            
class LiveVariable(Variable):
    needMoreData = QtCore.pyqtSignal()
    
    def __init__(self, database):
        Variable.__init__(self, database)
        self.data = None
        self.item = None
        
    def text(self):
        return 'live'
        
    def getData(self):
        if self.data == None:
            self.needMoreData.emit()
            return []
        else:
            return [self.data]
            
    def getTemp(self):
        return [self.temp]
            
    @QtCore.pyqtSlot(list, float)
    def updateLiveData(self, data, temp):
        self.data = data
        self.temp = temp
        self.updateGraphs()
        

class ViewTreeItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent):
        QtGui.QTreeWidgetItem.__init__(self, parent, 0)
        self.setCheckState(0, QtCore.Qt.Checked)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.changeColour()
        
    def changeColour(self):
        rand_color = QtGui.QColor(randrange(256), randrange(256), randrange(256))
        self.setForeground(2, QtGui.QBrush(rand_color))
        self.setBackground(2, QtGui.QBrush(rand_color))
    

class View(SimpleModelObj):
    def __init__(self, treeWidget, database):
        SimpleModelObj.__init__(self, database)
        self.item = ViewTreeItem(treeWidget)
        self.treeWidget = treeWidget
        #self.item.setText(0, text)
        self.status = UNDEFINED
        self.deps = {}
        self.disabled = False
        self.temps = []
        
    def getTemp(self):
        print 'returning self.temps from view as %s.  Am I appropriate? %s' %(`self.temps`, `self.status not in [UNDEFINED, ONE_SPECTRUM]`)
        if self.status in [UNDEFINED, ONE_SPECTRUM]:
            self.temps = []
        return self.temps
        
    def text(self):
        return str(self.item.text(0))
        
    def getData(self):
        return str(self.item.text(1))
        
    def getColour(self):
        return self.item.background(2).color().getRgbF()
        
    def getSigma(self):
        return str(self.item.text(3))
        
    def deleteLater(self):
        row = self.treeWidget.indexOfTopLevelItem(self.item)
        item = self.treeWidget.takeTopLevelItem(row)
        SimpleModelObj.deleteLater(self)
        del item
        self.setParent(None)


class DataSetModel(JoinableModel):
    def __init__(self, parent=None):
        headerLabels = [
                        'id',
                        'Name', 
                        'Notes',
                        'Start Time'
                        ]
        JoinableModel.__init__(self, headerLabels, parent)
        self.last_id = -1
    
    def appendRow(self, name, notes):
        self.last_id += 1
        id = self.last_id
        
        startTime = QtCore.QDateTime.currentDateTime().toString()
        
        JoinableModel.appendRow(self,
                                    [
                                    str(id),
                                    name,
                                    notes,
                                    startTime
                                    ]
                                )
                                
    
                   
    
    
class SpectrumModel(JoinableModel):
    def __init__(self, parent=None):
        headerLabels = [
                        'Temp (K)',
                        'Time', 
                        'Time Delta',
                        'lModelKey',
                        'SpectrumImage'
                        ]
        JoinableModel.__init__(self, headerLabels, parent)
        
    
    @QtCore.pyqtSlot(float, str, int)
    def appendRow(self, temp, pickledSpectrum, dataSet):
        now = QtCore.QDateTime.currentDateTime()
        
        deltaTime = ''
        number_of_spectra = self.rowCount()
        if number_of_spectra > 0:
            previousSpectrum_dataSet = self.item(number_of_spectra-1, 'lModelKey').text().toInt()[0]
            if previousSpectrum_dataSet == dataSet:
                previousSpectrum_time = QtCore.QDateTime().fromString(self.item(number_of_spectra-1, 'Time').text())
                deltaTime = previousSpectrum_time.secsTo(now)
        
        JoinableModel.appendRow(self,
                                    [
                                    str(temp),
                                    now.toString(),
                                    str(deltaTime),
                                    str(dataSet),
                                    pickledSpectrum,
                                    ]
                                )
"""                                
    def getSpectrum(self, row):
        temp = self.item(row, 0)
        time = self.item(row, 1)
        deltaTime = self.item(row, 2)
        dataSet = self.item(row, 3)
        pickledSpectrum = self.item(row, 4)
        return Spectrum(temp, time, deltaTime, dataSet, pickledSpectrum)
        
        
class Spectrum:
    def __init__(self, temp, time, deltaTime, dataSet, pickledSpectrum):
        self.temp = temp
        self.time = time
        self.deltaTime = deltaTime
        self.dataSet = dataSet
        self.pickledSpectrum = pickledSpectrum

"""



class SimpleModel(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.textDict = {}
        
    def updateTextDict(self):
        self.textDict = dict( (str(obj.text()), obj) for obj in self.children() )

class DataClass:
    def __init__(self):
        self.data = {}
        self.temp = {}
        self.currentKey = -1
        self.xData = None
    
    def addData(self, yData, temp):
        self.currentKey += 1
        #self.data[self.currentKey] = dict(zip(self.xData, yData))
        self.data[self.currentKey] = [ float(y) for y in yData ]
        self.temp[self.currentKey] = temp
        return str(self.currentKey)
        
    def getDatumFromSpectrum(self, row):
        key = int(DB.Spectrum.item(row, 4).text())
        return self.data[key]
        
    def getDataFromSpectra(self, rows):
        data = [self.getDatumFromSpectrum(row) for row in rows]
        return data
        
    def getTempFromSpectrum(self, row):
        key = int(DB.Spectrum.item(row, 4).text())
        return self.temp[key]
        
    def getTempFromSpectra(self, rows):
        temps = [self.getTempFromSpectrum(row) for row in rows]
        return temps
            

@singleton
class DBClass(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.Spectrum = SpectrumModel()
        self.DataSet = DataSetModel()
        self.Variable = SimpleModel()
        self.View = defaultdict(SimpleModel)
        self.Data = DataClass()
          
        live = LiveVariable(self.Variable)
        self.Variable.updateTextDict()
        """
        self.DataSet.appendRow('Data1', 'notes1')
        self.Spectrum.appendRow(50, self.Data.addData([0,2,4,5,5,4,3,2,1,0], 50), self.DataSet.last_id)
        self.Spectrum.appendRow(40, self.Data.addData([0,1,1,1,1,2,1,1,1,0], 40), self.DataSet.last_id)

        self.DataSet.appendRow('Data2', 'notes2')
        self.Spectrum.appendRow(80, self.Data.addData([0,1,1,1,1,2,1,1,1,0], 80), self.DataSet.last_id)
        self.Spectrum.appendRow(60, self.Data.addData([4,3,2,1,0,2,4,2,1,0], 60), self.DataSet.last_id)
        """
        self.currentDataSet = self.DataSet.last_id
        
    @QtCore.pyqtSlot(list)
    def updateWavelengths(self, wavelengths):
        wavelengths = np.array(wavelengths)
        
        wavelength = np.array([
                            wavelengths,
                            wavelengths * 10**(-9),
                            wavelengths / 10.0,
                            wavelengths * 10**(-9) / 201.168
                            ])
        
        wavenumber = 2*pi / wavelength
        energy = np.array([
                            h*c/(e*wavelengths*10**-9),
                            h*c/(wavelengths*10**-9),
                        ])
            
        self.Data.xData = [
                            wavelength,
                            wavenumber,
                            energy
                        ]
        
    @QtCore.pyqtSlot(list, float)
    def newData(self, data, temp):
        self.Spectrum.appendRow(temp, self.Data.addData(data, temp), self.currentDataSet)

DB = DBClass()
