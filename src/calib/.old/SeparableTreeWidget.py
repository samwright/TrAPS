from PyQt4 import QtCore, QtGui

from ..model import RangeItem, DataItem

class SeparableTreeWidget(QtGui.QTreeWidget):
    dataChanged = QtCore.pyqtSignal(list)
    
    def __init__(self, parent=None):
        QtGui.QTreeWidget.__init__(self, parent)
        self.sortItems(0, QtCore.Qt.DescendingOrder)
        self.curveDataColumns = []
        self.comparativeDataColumns = []
        
    @QtCore.pyqtSlot()
    def addRange(self):
        new_range = RangeItem(self, ['Range', ''])
        
    def getDataFromColumns(self, columns=[]):
        leftover_data = []
        output_data = []
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if isinstance(item, RangeItem):
                output_data.extend(item.getData(columns))
                output_data.append([])
            else:
                leftover_data.append(item.getData(columns))
        output_data.extend(leftover_data)
        
        print 'output_data = %s' %`output_data`
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
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item.mapFuncFromTo(self, func, from_column, to_column)
            
    def getRangeInColumn(self, column):
        min_vals = []
        max_vals = []
        for data_range in self.getDataFromColumns([column]):
            try:
                min_vals.append(min(data_range))
                max_vals.append(max(data_range))
            except ValueError:
                pass
        print 'min_vals=%s, max_vals=%s' %(`min_vals`, `max_vals`)
        try:
            min_val = min(min_vals)
            max_val = max(max_vals)
        except ValueError:
            min_val = max_val = float('NaN')
        return (min_val, max_val)
        
    def replaceData(self, calib_data):
        self.clear()
        self.appendData(calib_data)
        
    def appendData(self, calib_data):
        temp_column = self.curveDataColumns[0]
        volt_column = self.curveDataColumns[1]
        
        for data_range in calib_data:
            data_range_item = RangeItem(self)
            for voltage, temp in zip(data_range.voltages, data_range.temps):
                row = [None] * self.columnCount()
                row[volt_column] = voltage
                row[temp_column] = temp
                data_item = DataItem(data_range_item, row)