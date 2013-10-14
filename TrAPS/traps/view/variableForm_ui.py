# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'src/traps/view/ui/variableForm.ui'
#
# Created: Mon Mar  5 02:46:19 2012
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(832, 295)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.checkBox = QtGui.QCheckBox(Form)
        self.checkBox.setText(QtGui.QApplication.translate("Form", "Select individual spectra", None, QtGui.QApplication.UnicodeUTF8))
        self.checkBox.setObjectName(_fromUtf8("checkBox"))
        self.horizontalLayout.addWidget(self.checkBox)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.exportSelected = QtGui.QPushButton(Form)
        self.exportSelected.setText(QtGui.QApplication.translate("Form", "Export Selected", None, QtGui.QApplication.UnicodeUTF8))
        self.exportSelected.setObjectName(_fromUtf8("exportSelected"))
        self.horizontalLayout.addWidget(self.exportSelected)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.spectraSelector = SpectraSelector(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spectraSelector.sizePolicy().hasHeightForWidth())
        self.spectraSelector.setSizePolicy(sizePolicy)
        self.spectraSelector.setMinimumSize(QtCore.QSize(0, 150))
        self.spectraSelector.setObjectName(_fromUtf8("spectraSelector"))
        self.horizontalLayout_2.addWidget(self.spectraSelector)
        self.dataSetSelector = DatasetSelector(Form)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dataSetSelector.sizePolicy().hasHeightForWidth())
        self.dataSetSelector.setSizePolicy(sizePolicy)
        self.dataSetSelector.setMinimumSize(QtCore.QSize(0, 150))
        self.dataSetSelector.setObjectName(_fromUtf8("dataSetSelector"))
        self.horizontalLayout_2.addWidget(self.dataSetSelector)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.checkBox, QtCore.SIGNAL(_fromUtf8("clicked(bool)")), self.spectraSelector.setVisible)
        QtCore.QObject.connect(self.checkBox, QtCore.SIGNAL(_fromUtf8("clicked(bool)")), self.dataSetSelector.setHidden)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        pass

from DataSelector import DatasetSelector, SpectraSelector
