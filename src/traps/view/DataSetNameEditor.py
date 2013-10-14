from PyQt4 import QtCore, QtGui

from model import DB

class DataSetNameEditor(QtGui.QLineEdit):
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        completer = QtGui.QCompleter()
        completer.setModel(DB.DataSet)
        completer.setCompletionColumn(1)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompleter(completer)