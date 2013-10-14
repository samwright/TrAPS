from PyQt4 import QtCore, QtGui

class DataItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent=None, entries=[]):
        str_entries = [ str(entry) for entry in entries ]
        QtGui.QTreeWidgetItem.__init__(self, parent, str_entries)
        self.setFlags(self.flags() & ~QtCore.Qt.ItemIsDropEnabled)
        
    def getData(self, columns):
        return [ float(self.text(i)) for i in columns ]
        
    def mapFuncFromTo(self, func, from_column, to_column):
        from_data = float(self.text(from_column))
        to_data = func(from_data)
        self.setText(to_column, to_data)
        
        
class RangeItem(QtGui.QTreeWidgetItem):
    def __init__(self, *args, **kwargs):
        QtGui.QTreeWidgetItem.__init__(self, *args, **kwargs)
        self.setFlags(self.flags() & ~QtCore.Qt.ItemIsDragEnabled)
        
    def getData(self, columns):
        return [ self.child(i).getData(columns) for i in range(self.childCount()) ]
        
    def mapFuncFromTo(self, func, from_column, to_column):
        for i in range(self.childCount()):
            item = self.child(i)
            item.mapFuncFromTo(self, func, from_column, to_column)        
