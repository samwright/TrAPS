from PyQt4 import QtCore, QtGui


class JoinableModel(QtGui.QStandardItemModel):
    """
    Using this class, you first create a base model then an extension model.
    The base model is where the shared data goes (eg. pickledSpectrum), and it
    is what rows are appended to.  The extension model contains private data (eg.
    the checkboxes in Analysis tab) and shouldn't be appended directly.  Instead,
    it adds its extra cells only when the base model has new data (which is
    automatically added to this model).
    """
    rowAppendedToModel = QtCore.pyqtSignal(list, object)
    
    def __init__(self, headerLabels, parent):
        QtGui.QStandardItemModel.__init__(self,parent)
        self.setHorizontalHeaderLabels(headerLabels)
        self.headerLabels = headerLabels
        self.joinedModelIndex = None
        self.joinedModel = None
        
    def appendRow(self, items):
        row = [CenteredStandardItem(item) for item in items]
        QtGui.QStandardItemModel.appendRow(self, row)
        self.rowAppendedToModel.emit(row, self)
        
    def item(self, row, column):
        if type(column) == int:
            column_id = column
        else:
            column_id = self.headerLabels.index(column)
        return QtGui.QStandardItemModel.item(self, row, column_id)
    
    def join(self, model):
        if not isinstance(model, JoinableModel):
            raise Exception('To join models, subclass both from JoinableModel')
        self.joinedModelIndex = len(self.headerLabels)
        self.headerLabels.extend(model.headerLabels)
        self.setHorizontalHeaderLabels(self.headerLabels)
        for row in range(model.rowCount()):
            items = [model.item(row, column) for column in range(model.columnCount())]
            self.appendRow(self.defaultItems() + items)
        model.rowAppendedToModel.connect(self.appendRowToJoinedModel)
        model.itemChanged.connect(self.updateJoinedModelItem)
        model.rowsRemoved.connect(self.removeRowFromJoinedModelItem)
        self.joinedModel = model
        
    @QtCore.pyqtSlot(QtGui.QStandardItem, int, int)
    def removeRowFromJoinedModelItem(self, joinedModelIndex, start, end):
        print 'removed from index %d,%d from start=%d to end=%d' %(joinedModelIndex.row(), joinedModelIndex.column(), start, end)
        self.removeRow(start)
        
    @QtCore.pyqtSlot(QtGui.QStandardItem)
    def updateJoinedModelItem(self, joinedModelItem):
        index = self.joinedModel.indexFromItem(joinedModelItem)
        item = self.item(index.row(), index.column() + self.joinedModelIndex)
        item.setText(joinedModelItem.text())
        
    @QtCore.pyqtSlot(list, object)
    def appendRowToJoinedModel(self, items, model):
        startColumn = self.headerLabels.index(model.headerLabels[0])
        row = self.defaultItems() + items 
        self.appendRow(row)
        
    def defaultItems(self):
        """
        Override defaultItems and return a list of itemsto add to the model.
        """
        pass
        
    def hideColumn(self, column):
        if type(column) == int:
            column_id = column
        else:
            column_id = self.headerLabels.index(column)
        QtGui.QStandardItemModel.hideColumn(self, row, column_id)

    
class CenteredStandardItem(QtGui.QStandardItem):
    def __init__(self, contents):
        QtGui.QStandardItem.__init__(self)
        self.setTextAlignment(QtCore.Qt.AlignHCenter)
        self.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsEnabled)
        if isinstance(contents, QtGui.QStandardItem):
            self.copyFrom(contents)
        elif type(contents) in [str, unicode, QtCore.QString]:
            self.setText(contents)
        else:
            raise Exception("""
                Wasn't expecting %s type.  Needed either a QStandardItem or a
                string, unicode or QString.
                """)
        
    def copyFrom(self, original):
        self.setText(original.text())
        if original.isCheckable():
            self.setCheckable(True)
            self.setCheckState(original.checkState())
            self.setTristate(original.isTristate())


class AddCheckboxToModel(JoinableModel):
    def __init__(self, modelToJoin, parent=None):
        JoinableModel.__init__(self, ['Use'], parent)
        self.join(modelToJoin)
    
    def defaultItems(self):
        checkbox = CenteredStandardItem('')
        checkbox.setCheckable(True)
        checkbox.setCheckState(False)
        return [checkbox]
        

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance
