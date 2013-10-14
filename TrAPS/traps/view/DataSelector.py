from PyQt4 import QtCore, QtGui

from ..model import AddCheckboxToModel, DB
from helpers import CompactTreeView, SortFilterModel, SortForeignFilterModel, inclusive_range


class SpectraSelector(QtGui.QWidget):
    spectrumSelected = QtCore.pyqtSignal(int, bool)
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        hLayout = QtGui.QHBoxLayout(self)
        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Horizontal)
        splitter.setOpaqueResize(True)
        splitter.setChildrenCollapsible(False)
        hLayout.addWidget(splitter)
        
        self.lView = CompactTreeView(splitter)
        
        self.rView = CompactTreeView(splitter)
        
        splitter.setStretchFactor(0,0)
        splitter.setStretchFactor(1,1)
        
        self.setModels(DB.DataSet, DB.Spectrum)
        self.rProxyModel.setForeignRelation(4, self.lProxyModel, 1)
        self.rProxyModel.filterForForeignKeysSelection()
        self.lView.hideColumn(1)
        self.lView.hideColumn(3)
        self.lView.sortByColumn(3, QtCore.Qt.DescendingOrder)
        self.lView.adjustColumnWidths(0, self.lProxyModel.columnCount())
        
        self.rView.hideColumn(2)
        self.rView.hideColumn(4)
        self.rView.hideColumn(5)
        self.rView.sortByColumn(1, QtCore.Qt.DescendingOrder)
        self.rView.adjustColumnWidths(0, self.lProxyModel.columnCount())
        
    def setModels(self, lModel, rModel):
        self.lModel = AddCheckboxToModel(lModel)
        self.lProxyModel = SortForeignFilterModel(self)
        self.lProxyModel.setSourceModel(self.lModel)
        self.lView.setModel(self.lProxyModel)
        
        self.rModel = AddCheckboxToModel(rModel)
        self.rProxyModel = SortForeignFilterModel(self)
        self.rProxyModel.setSourceModel(self.rModel)
        self.rView.setModel(self.rProxyModel)
        
        self.lView.selectionModel().selectionChanged.connect(self.rProxyModel.filterForForeignKeysSelection)
        self.rModel.dataChanged.connect(self.updateLeftCheckbox)
        self.rModel.dataChanged.connect(self.updateSelectedSpectra)
        self.lModel.dataChanged.connect(self.updateRightCheckboxes)
        
        self.lModel.rowsAboutToBeRemoved.connect(self.disableDataSet)
        
    @QtCore.pyqtSlot(QtCore.QModelIndex, int, int)
    def disableDataSet(self, parent, startRow, endRow):
        #self.lModel.dataChanged.disconnect(self.updateRightCheckboxes)
        self.lModel.item(startRow, 0).setCheckState(QtCore.Qt.Unchecked)
        #self.updateRightCheckboxes()
        #self.lModel.dataChanged.connect(self.updateRightCheckboxes)
        
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def updateLeftCheckbox(self, currentPointer, previousPointer):
        rModel_curentForeignKey = self.rModel.item(currentPointer.row(), self.rProxyModel.foreignKeyColumn).text()
        lModel_currentCheckboxItem = self.lModel.item(int(rModel_curentForeignKey), 0)
        self.lModel.dataChanged.disconnect(self.updateRightCheckboxes)
        
        checkedCounter = 0
        uncheckedCounter = 0
        for row in range(self.rModel.rowCount()):
            row_foreignKey = self.rModel.item(row, self.rProxyModel.foreignKeyColumn).text()
            if row_foreignKey == rModel_curentForeignKey:
                row_firstItem = self.rModel.item(row, 0)
                if row_firstItem.checkState() == QtCore.Qt.Checked:
                    checkedCounter += 1
                else:
                    uncheckedCounter += 1
                if checkedCounter > 0 and uncheckedCounter > 0:
                    lModel_currentCheckboxItem.setCheckState(QtCore.Qt.PartiallyChecked)
                    self.lModel.dataChanged.connect(self.updateRightCheckboxes)
                    return
        if checkedCounter == 0:
            lModel_currentCheckboxItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            lModel_currentCheckboxItem.setCheckState(QtCore.Qt.Checked)
        self.lModel.dataChanged.connect(self.updateRightCheckboxes)
            
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def updateSelectedSpectra(self, currentPointer, previousPointer):
        rModel_item = self.rModel.itemFromIndex(currentPointer)
        if rModel_item.checkState() == QtCore.Qt.Checked:
            self.spectrumSelected.emit(currentPointer.row(), True)
        elif rModel_item.checkState() == QtCore.Qt.Unchecked:
            self.spectrumSelected.emit(currentPointer.row(), False)
            
    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def updateRightCheckboxes(self, currentPointer, previousPointer):
        if currentPointer.column() == 0:
            lModel_checkItem = self.lModel.itemFromIndex(currentPointer)
            new_checkState = lModel_checkItem.checkState()
            
            for row in range(self.rModel.rowCount()):
                rModel_foreignKey = self.rModel.item(row, self.rProxyModel.foreignKeyColumn).text()
                if int(rModel_foreignKey) == lModel_checkItem.row():
                    rModel_checkItem = self.rModel.item(row, 0)
                    rModel_checkItem.setCheckState(new_checkState)
  
       
class DatasetSelector(CompactTreeView):
    spectrumSelected = QtCore.pyqtSignal(int, bool)
    spectraSelected = QtCore.pyqtSignal(list, bool)
    dataSetSelected = QtCore.pyqtSignal(int, bool)
    
    def __init__(self, parent):
        CompactTreeView.__init__(self, parent)
        self.checked = ['-1']
        self.setModel(DB.DataSet)
        self.model.dataChanged.connect(self.updateSelectedDataSets)
        self.hideColumn(1)
        self.hideColumn(3)
        self.sortByColumn(3, QtCore.Qt.DescendingOrder)
        self.adjustColumnWidths(0, self.proxyModel.columnCount())
        
    def setModel(self, model):
        self.model = AddCheckboxToModel(model)
        self.proxyModel = SortForeignFilterModel(self)
        self.proxyModel.setSourceModel(self.model)
        CompactTreeView.setModel(self, self.proxyModel)
        
        self.selectedSpectra = SortForeignFilterModel(self)
        self.selectedSpectra.setSourceModel(DB.Spectrum)
        self.selectedSpectra.setForeignRelation(3, self.proxyModel, 1)
        
        self.selectedSpectra.rowsAboutToBeRemoved.connect(self.removeSpectra)
        self.selectedSpectra.rowsInserted.connect(self.addSpectra)
        self.selectedSpectra.filterForForeignKeysList(self.checked)
        self.selectedSpectra.sort(0)
        
        self.model.rowsAboutToBeRemoved.connect(self.disableDataSet)
        
    @QtCore.pyqtSlot(QtCore.QModelIndex, int, int)
    def disableDataSet(self, parent, startRow, endRow):
        if str(startRow) in self.checked:
            self.dataSetSelected.emit(startRow, False)
            self.checked.remove(str(startRow))
            self.selectedSpectra.filterForForeignKeysList(self.checked)
        
    @QtCore.pyqtSlot(QtCore.QModelIndex, int, int)
    def removeSpectra(self, parent, startRow, endRow):
        rows_inSourceModel = [self.selectedSpectra.mapRowToSource(row) for row in inclusive_range(startRow, endRow)]
        if len(rows_inSourceModel) > 1:
            self.spectraSelected.emit(rows_inSourceModel, False)
        else:
            self.spectrumSelected.emit(rows_inSourceModel[0], False)
    
    @QtCore.pyqtSlot(QtCore.QModelIndex, int, int)
    def addSpectra(self, parent, startRow, endRow):
        rows_inSourceModel = [self.selectedSpectra.mapRowToSource(row) for row in inclusive_range(startRow, endRow)]
        if len(rows_inSourceModel) > 1:
            self.spectraSelected.emit(rows_inSourceModel, True)
        else:
            self.spectrumSelected.emit(rows_inSourceModel[0], True)
        
    def updateSelectedDataSets(self, currentPointer, previousPointer):
        if currentPointer.column() == 0:
            item = self.model.itemFromIndex(currentPointer)
            row = currentPointer.row()
            if item.checkState() == QtCore.Qt.Checked:
                self.dataSetSelected.emit(row, True)
                self.checked.append(str(row))
            elif item.checkState() == QtCore.Qt.Unchecked:
                self.dataSetSelected.emit(row, False)
                self.checked.remove(str(row))
            self.selectedSpectra.filterForForeignKeysList(self.checked)
            
            # Force refilter:
            self.selectedSpectra.sort(0)
        
