from PyQt4 import QtCore, QtGui
from ..model import DB, Variable

import variableWidget_ui



class VariableWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.ui = variableWidget_ui.Ui_Form()
        self.ui.setupUi(self)
        
        self.variableCount = 0
        self.ui.addButton.clicked.connect(self.newVariable)
        self.ui.removeButton.clicked.connect(self.deleteSelectedVariable)
        
        #self.ui.listWidget.itemActivated.connect(self.changeVariableForm)
        self.ui.listWidget.itemSelectionChanged.connect(self.changeVariableForm)
        self.ui.listWidget.itemChanged.connect(self.variableTextChanged)
        
    @QtCore.pyqtSlot()
    def newVariable(self):
        self.variableCount += 1
        self.ui.listWidget.itemChanged.disconnect(self.variableTextChanged)
        variable = Variable(DB.Variable, self.ui.listWidget)
        self.ui.listWidget.itemChanged.connect(self.variableTextChanged)
        variable.item.setText("var%d" %self.variableCount)
        index = self.ui.stackedWidget.addWidget(variable)
        self.ui.stackedWidget.setCurrentIndex(index)
        
    @QtCore.pyqtSlot()
    def deleteSelectedVariable(self):
        variableListItem = self.ui.listWidget.selectedItems()[0]
        for variable in DB.Variable.children():
            if variable.item == variableListItem:
                index = variable.delAndReturnIndex()
                #variable.deleteLater()
                variablePage = self.ui.stackedWidget.widget(index)
                self.ui.stackedWidget.removeWidget(variablePage)
                variablePage.deleteLater()
                return
        
    @QtCore.pyqtSlot()
    def changeVariableForm(self):
        variableListItems = self.ui.listWidget.selectedItems()
        if len(variableListItems) == 1:
            variableItem = variableListItems[0]
            index = self.ui.listWidget.row(variableItem)
            self.ui.stackedWidget.setCurrentIndex(index)
        
    @QtCore.pyqtSlot(QtGui.QListWidgetItem)
    def variableTextChanged(self, variableListItem):
        newText = str(variableListItem.text())
        print 'changing to %s' %newText
        all_views_names = []
        for views in DB.View.values():
            all_views_names.extend([view.text() for view in views.children()])
        if newText in [''] + DB.Variable.textDict.keys() + all_views_names:
            variableListItem.setText("%s_" %newText)
            return
        DB.Variable.updateTextDict()
        variable = DB.Variable.textDict[str(variableListItem.text())]
        variable.textChanged()
    