from PyQt4 import QtCore, QtGui
import numpy as np

class DataItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent, entries=[]):
        str_entries = [ str(entry) for entry in entries ]
        QtGui.QTreeWidgetItem.__init__(self, str_entries)
        
        self.setFlags(self.flags() & ~QtCore.Qt.ItemIsDropEnabled & ~QtCore.Qt.ItemIsDragEnabled)
        parent.addTopLevelItem(self)
        
    def getSortValue(self):
        sort_column = self.treeWidget().sortColumn()
        return self.getData(sort_column)
        
    def getData(self, columns):
        if hasattr(columns, '__iter__'):
            return [ float(str(self.text(i))) for i in columns ]
        else:
            return float(self.text(columns))
        
    def mapFuncFromTo(self, func, from_column, to_column):
        from_data = float(self.text(from_column))
        to_data = func(from_data)
        self.setText(to_column, str(to_data))
        
    def __lt__(self, item):
        return self.getSortValue() < item.getSortValue()
        
            
class SeparatorItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent):
        QtGui.QTreeWidgetItem.__init__(self, ['--------'])
        
        self.setFlags(self.flags() & ~QtCore.Qt.ItemIsDropEnabled)
        parent.addTopLevelItem(self)
        
        self.savePosition()
        
    def savePosition(self):
        sort_column = self.treeWidget().sortColumn()
        neighbouring_values = []
        for item in [ self.treeWidget().itemAbove(self), self.treeWidget().itemBelow(self) ]:
            if isinstance(item, DataItem):
                neighbouring_value = item.getData(sort_column)
                neighbouring_values.append(neighbouring_value)
                
        self.sort_value = np.average(neighbouring_values)
        if np.isnan(self.sort_value):
            self.sort_value = 0.0
            
        #self.setText(0, '----%.1f----' %self.sort_value)
        
    def getSortValue(self):
        return self.sort_value
        
    def getData(self, columns):
        return []
        
    def mapFuncFromTo(self, func, from_column, to_column):
        pass

    def __lt__(self, item):
        return self.getSortValue() < item.getSortValue()
        
        