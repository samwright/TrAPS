from PyQt4 import QtCore, QtGui


class SelectionPopup(QtGui.QMenu):
    setSelectionCheckState = QtCore.pyqtSignal(QtCore.Qt.CheckState)
    checkOnlySelected = QtCore.pyqtSignal()
    
    def __init__(self, parent):
        QtGui.QMenu.__init__(self, parent)
        self.addAction("Check Selected", self.checkSelection)
        self.addAction("Uncheck Selected", self.uncheckSelection)
        self.addAction("Check Only Selected", self.checkOnlySelected)
        
    @QtCore.pyqtSlot()
    def checkSelection(self):
        self.setSelectionCheckState.emit(QtCore.Qt.Checked)
        
    @QtCore.pyqtSlot()    
    def uncheckSelection(self):
        self.setSelectionCheckState.emit(QtCore.Qt.Unchecked)        
        
        
class CompactTreeView(QtGui.QTreeView):
    def __init__(self, *args, **kwargs):
        QtGui.QTreeView.__init__(self, *args, **kwargs)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)
        
        self.setMinimumSize(QtCore.QSize(0, 100))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(sizePolicy)
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.menu = SelectionPopup(self)
        self.menu.setSelectionCheckState.connect(self.setSelectionCheckState)
        self.menu.checkOnlySelected.connect(self.checkOnlySelected)
        self.customContextMenuRequested.connect(self.showSelectionPopup)
    
    @QtCore.pyqtSlot(QtCore.Qt.CheckState)
    def setSelectionCheckState(self, checkState):
        proxyModel_Selectedrows = self.selectionModel().selectedRows()
        for proxyModel_row in proxyModel_Selectedrows:
            model_row = self.model().mapToSource(proxyModel_row).row()
            item = self.model().sourceModel().item(model_row, 0)
            item.setCheckState(checkState)
            
    @QtCore.pyqtSlot()
    def checkOnlySelected(self):
        proxyModel_Selectedrows = self.selectionModel().selectedRows()
        rowsToUncheck = range(self.model().rowCount())
        for proxyModel_row in proxyModel_Selectedrows:
            model_row = self.model().mapToSource(proxyModel_row).row()
            item = self.model().sourceModel().item(model_row, 0)
            item.setCheckState(QtCore.Qt.Checked)
            rowsToUncheck.remove(model_row)
        for row in rowsToUncheck:
            item = self.model().sourceModel().item(row, 0)
            item.setCheckState(QtCore.Qt.Unchecked)
            
    @QtCore.pyqtSlot(QtCore.QPoint)
    def showSelectionPopup(self, pos):
        if len(self.selectionModel().selectedRows()) > 0:
            globalPos = self.mapToGlobal(pos)
            self.menu.exec_(globalPos)
    
    def setSourceModel(self, model):
        QtGui.QSortFilterProxyModel.setSourceModel(self, model)
        self.adjustColumnWidths(0, model.columnCount())
    
    @QtCore.pyqtSlot(int, int)
    def columnCountChanged(oldCount, newCount):
        self.adjustColumnWidths(oldCount, newCount)
        
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def dataChanged(self, topLeft=None, bottomRight=None):
        self.adjustColumnWidths(topLeft.column(), bottomRight.column())
        QtGui.QTreeView.dataChanged(self, topLeft, bottomRight)
           
    def adjustColumnWidths(self, leftColumn, rightColumn):
        for column in inclusive_range(leftColumn, rightColumn):
            self.resizeColumnToContents(column)
       
        
class SortFilterModel(QtGui.QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        QtGui.QSortFilterProxyModel.__init__(self, *args, **kwargs)
        self.setDynamicSortFilter(True)
        
    def lessThan(self, left, right):
        leftValue = left.data()
        rightValue = right.data()
        supported_types = [QtCore.QVariant.Double, QtCore.QVariant.DateTime, QtCore.QVariant.Time]
        for typ in supported_types:
            if leftValue.canConvert(typ) and rightValue.canConvert(typ):
                if leftValue.convert(typ) and rightValue.convert(typ):
                    return leftValue.toPyObject() < rightValue.toPyObject()
                else:
                    leftValue = left.data()
                    rightValue = right.data()
        return QtGui.QSortFilterProxyModel.lessThan(self, left, right)
        
        
class SortForeignFilterModel(SortFilterModel):
    def __init__(self, *args, **kwargs):
        SortFilterModel.__init__(self, *args, **kwargs)
        self.setDynamicSortFilter(True)
        self.selectedForeignKeys = ["-1"]
        
    def setForeignRelation(self, foreignKeyColumn, foreignProxyTable, foreignTableKeyColumn):
        self.foreignKeyColumn = foreignKeyColumn
        self.foreignProxyTable = foreignProxyTable
        self.foreignTableKeyColumn = foreignTableKeyColumn
        self.setFilterKeyColumn(foreignKeyColumn)
    
    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def filterForForeignKeysSelection(
                            self,
                            newProxyModelSelection=QtGui.QItemSelection(), 
                            oldProxyModelSelection=QtGui.QItemSelection()
                            ):
        foreignKeysList = self.selectedForeignKeys
        newProxyModel_SelectedIndices = newProxyModelSelection.indexes()
        for proxyModel_SelectedIndex in newProxyModel_SelectedIndices:
            if proxyModel_SelectedIndex.column() == 0:
                model_row = self.foreignProxyTable.mapToSource(proxyModel_SelectedIndex).row()
                foreignKeysList.append(str(model_row))
        oldProxyModel_SelectedIndices = oldProxyModelSelection.indexes()
        for proxyModel_SelectedIndex in oldProxyModel_SelectedIndices:
            if proxyModel_SelectedIndex.column() == 0:
                model_row = self.foreignProxyTable.mapToSource(proxyModel_SelectedIndex).row()
                foreignKeysList.remove(str(model_row))
        self.filterForForeignKeysList(foreignKeysList)
        
    def filterForForeignKeysList(self, foreignKeysList):
        regex_str = '\\b(%s)\\b' %("|".join(foreignKeysList))
        self.setFilterRegExp(regex_str)
        self.selectedForeignKeys = foreignKeysList
        
    def mapRowToSource(self, row):
        #index_inSourceModel = self.index(row, 0, self.sourceModel())
        index_inProxyModel = self.index(row, 0)
        index_inSourceModel = self.mapToSource(index_inProxyModel)
        #self.index(row, 0, parent)
        return index_inSourceModel.row()
        

def inclusive_range(start, stop, step=1):
    return(range(start, stop+step, step))
        
        
class SmartTabWidget(QtGui.QTabWidget):
    def __init__(self, parent=None):
        QtGui.QTabWidget.__init__(self, parent)
        self.setTabBar(EditableTabBar())
        self.tabsCreated = 0
        self.tabCloseRequested.connect(self.deleteTab)
        newTabButton = QtGui.QToolButton()
        newTabButton.setIcon( QtGui.QIcon.fromTheme("list-add") )
        self.setCornerWidget( newTabButton, QtCore.Qt.TopLeftCorner )
        newTabButton.clicked.connect( self.addTab )
        self.defaultTabName = 'Tab'
    
    @QtCore.pyqtSlot(QtGui.QWidget, str)
    def addTab(self, tabObject=None, Name=None):
        if tabObject == None:
            tabObject = QtGui.QWidget()
        if Name == None:
            Name = "%s %d" %(self.defaultTabName, self.tabsCreated+1)
        self.tabsCreated += 1
        QtGui.QTabWidget.addTab(self, tabObject, Name)
        self.setCurrentWidget(tabObject)
    
    @QtCore.pyqtSlot(QtGui.QWidget)
    def deleteTab(self, tab_index):
        tab = self.widget(tab_index)
        if self.count() == 1:
            self.addTab()
        tab.deleteLater()

          
class EditableTabBar(QtGui.QTabBar):
    def mouseDoubleClickEvent(self, event):
        self.renamingTabIndex = self.tabAt(event.pos())
        self.oldName = self.tabText(self.renamingTabIndex)
        
        self.rename_box = RenameBox(self.oldName, self)
        self.renameTab(self.oldName)
        
        text_rect = self.tabRect(self.renamingTabIndex).adjusted(2,2,-2,-2)
        text_rect.moveTo(self.mapToGlobal(text_rect.topLeft()))
        self.rename_box.setGeometry(text_rect)
        
        self.rename_box.selectAll()
        self.rename_box.textEdited.connect(self.renameTab)
        self.rename_box.cancelEdit.connect(self.restoreName)
        self.rename_box.returnPressed.connect(self.rename_box.deleteLater)
        self.rename_box.show()
        QtGui.QTabBar.mouseDoubleClickEvent(self, event)
        
    @QtCore.pyqtSlot()
    def restoreName(self):
        self.setTabText(self.renamingTabIndex, self.oldName)
        self.rename_box.deleteLater()
        
    @QtCore.pyqtSlot(QtCore.QString)
    def renameTab(self, text):
        self.setTabText(self.renamingTabIndex, text)
        new_width = self.tabRect(self.renamingTabIndex).adjusted(2,2,-2,-2).width()
        self.rename_box.setFixedWidth(new_width)
        
        
class RenameBox(QtGui.QLineEdit):
    cancelEdit = QtCore.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super(QtGui.QLineEdit, self).__init__(*args, **kwargs)
        self.setWindowFlags(QtCore.Qt.Popup)
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.cancelEdit.emit()
        else:
            QtGui.QLineEdit.keyPressEvent(self, event)
            
    def mousePressEvent(self, event):
        QtGui.QLineEdit.mousePressEvent(self, event)            
        if not self.geometry().contains(self.mapToGlobal(event.pos())):
            self.cancelEdit.emit()