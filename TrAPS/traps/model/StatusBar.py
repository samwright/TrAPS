import sys

from PyQt4 import QtCore, QtGui

from helpers import singleton
        
@singleton
class StatusBarClass(QtGui.QStatusBar):
    pass

#StatusBar = StatusBarSingleton()