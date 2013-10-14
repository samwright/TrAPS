import sys

from PyQt4 import QtCore, QtGui

from model import singleton
        
@singleton
class StatusBarSingleton(QtGui.QStatusBar):
    pass

StatusBar = StatusBarSingleton()