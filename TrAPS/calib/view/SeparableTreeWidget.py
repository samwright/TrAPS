import os
import csv

from PyQt4 import QtCore, QtGui

from ..model import SeparatorItem, DataItem

class SeparableTreeWidget(QtGui.QTreeWidget):
    dataChanged = QtCore.pyqtSignal(list)
    dataReadyToShow = QtCore.pyqtSignal(list)
    
    def __init__(self, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        
        self.curveDataColumns = []
        self.comparativeDataColumns = []
        
        self.homedir = os.path.expanduser('~')
        
    def sortByTemp(self):
        temp_column = self.curveDataColumns[0]
        self.sortItems(temp_column, QtCore.Qt.DescendingOrder)
        self.setSortingEnabled(True)
        
    def rowsInserted(self, modelIndex, start, end):
        items_around_index = [ self.topLevelItem(i) for i in range(start-1, start+1) ]
        affected_separators = set( item for item in items_around_index if isinstance(item, SeparatorItem) )
        for separator in affected_separators:
            separator.savePosition()
        QtGui.QTreeWidget.rowsInserted(self, modelIndex, start, end)
        
        
    @QtCore.pyqtSlot()
    def addSeparator(self):
        new_seperator = SeparatorItem(self)
        
    def getDataFromColumns(self, columns):
        output_data = [ item.getData(columns) for item in self.items() ]
        
        #print 'output_data = %s' %`output_data`
        return output_data
        
    def getCurveData(self):
        return self.getDataFromColumns(self.curveDataColumns)
        
    def getComparativeData(self):
        return self.getDataFromColumns(self.comparativeDataColumns)
        
    def dropEvent(self, ev):
        QtGui.QTreeWidget.dropEvent(self, ev)
        self.dataChanged.emit(self.getCurveData())
        
    #TODO def deleteEvent: dataChanged.emit(...)
        
    def mapFuncFromTo(self, func, from_column, to_column):
        for item in self.items():
            item.mapFuncFromTo(func, from_column, to_column)
            
    def getRangeInColumn(self, column):
        min_vals = []
        max_vals = []
        for data_range in self.getDataFromColumns([column]):
            try:
                min_vals.append(min(data_range))
                max_vals.append(max(data_range))
            except ValueError:
                pass
        #print 'min_vals=%s, max_vals=%s' %(`min_vals`, `max_vals`)
        try:
            min_val = min(min_vals)
            max_val = max(max_vals)
        except ValueError:
            min_val = max_val = float('NaN')
        return (min_val, max_val)
        
    def items(self):
        return [ self.topLevelItem(i) for i in range(self.topLevelItemCount()) ]
        
    def replaceData(self, calib_data):
        scroll_position = self.verticalScrollBar().value()
        print 'before replace, len(calib_data)=%d, len(self.getCurveData())=%d' %(len(calib_data), len(self.getCurveData()))
        self.clear()
        self.appendData(calib_data)
        print 'after replace, len(self.getCurveData())=%d' %len(self.getCurveData())
        self.verticalScrollBar().setSliderPosition(scroll_position)
        
    def appendComparativeData(self, calib_data):
        cal_volt_column = self.comparativeDataColumns[0]
        new_volt_column = self.comparativeDataColumns[1]
        
        self.appendData(calib_data, cal_volt_column, new_volt_column)
        
    def appendData(self, calib_data, temp_column=None, volt_column=None):
        if temp_column == None:
            temp_column = self.curveDataColumns[0]
        if volt_column == None:
            volt_column = self.curveDataColumns[1]
        
        last_index_in_calib_data = len(calib_data) - 1
        self.setSortingEnabled(False)
        
        for i, data_range in enumerate(calib_data):
            for voltage, temp in zip(data_range.voltages, data_range.temps):
                row = [None] * self.columnCount()
                row[volt_column] = voltage
                row[temp_column] = temp
                data_item = DataItem(self, row)
                
            if i != last_index_in_calib_data:
                separator_item = SeparatorItem(self)
        #self.dataReadyToShow.emit(self.getCurveData())
        self.setSortingEnabled(True)
        
    def deleteSelected(self):
        try:
            item = self.selectedItems()[0]
            self.invisibleRootItem().removeChild(item)
            self.dataChanged.emit(self.getCurveData())
        except IndexError:
            pass
        
    def saveCurveData(self):
        self.save(self.curveDataColumns)
        
    def saveComparativeData(self):
        self.save(self.comparativeDataColumns)
        
    def save(self, columns):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save Curve Data as...", self.homedir, "Comma Separated Values (*.csv)")
        if filename == '':
            return
        ofile = open(filename, 'w')
        writer = csv.writer(ofile)
        
        data = self.getDataFromColumns(columns)
        headers = [ self.headerItem().text(i) for i in columns ]
        
        writer.writerow(headers)
        for datum in data:
            writer.writerow(datum)
            
        ofile.close()
        
            
        
            