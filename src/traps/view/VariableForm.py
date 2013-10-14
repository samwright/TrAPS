from PyQt4 import QtCore, QtGui

from ..model import Variable

import variableForm_ui
variable_form = variableForm_ui.Ui_Form()


class VariableForm(QtGui.QStackedWidget):
    def __init__(self, parent):
        QtGui.QStackedWidget.__init__(self, parent)
        self.ui = variableForm_ui.Ui_Form()
        
    def addWidget(self, variable):
        if not isinstance(variable, Variable):
            return
            #raise Exception("""
            #                This stacked widget requires a Variable object,
            #                from which it makes its own page widget.
            #                """)
        newPage = QtGui.QWidget()
        self.ui.setupUi(newPage)
        
        self.ui.spectraSelector.spectrumSelected.connect(variable.setSpectrumInclusion)
        self.ui.dataSetSelector.spectrumSelected.connect(variable.setDataSetSpectrumInclusion)
        self.ui.dataSetSelector.spectraSelected.connect(variable.setDataSetSpectraInclusion)
        self.ui.dataSetSelector.dataSetSelected.connect(variable.setDataSetInclusion)
        self.ui.checkBox.stateChanged.connect(variable.changeVariableType)
        
        self.ui.checkBox.clicked.emit(False)
        
        return QtGui.QStackedWidget.addWidget(self, newPage)