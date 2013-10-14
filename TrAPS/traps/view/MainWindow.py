import sys

from PyQt4 import QtCore, QtGui

app = QtGui.QApplication(sys.argv)
#from model.StatusBar import StatusBarClass
import main_ui


class MainWindow(QtGui.QMainWindow):
    closing = QtCore.pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        QtGui.QMainWindow.__init__(self, *args, **kwargs)
        #self.setStatusBar(StatusBarClass())
        self.ui = main_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        
        #self.ui.actionCreate_calibration_data.triggered.connect(self.calibrator.show)
        #self.calibrator.loadFile.connect(self.ui.hardwareWidget.loadTempCalibrationFile)
        #loadTempCalibrationFile
        
        #MainWindow_ui.bigSplitter.setStretchFactor(0,0)
        #MainWindow_ui.bigSplitter.setStretchFactor(1,1)
        #self.ui.rightSplitter.setStretchFactor(0,0)
        #self.ui.rightSplitter.setStretchFactor(1,1)
        #self.ui.checkBox.clicked.emit(True)
        
        self.closing.connect(self.ui.hardwareWidget.spectrometerWorker.close)
        self.ui.hardwareWidget.spectrometerWorker.closed.connect(self.closedNicely)
        
        
    def closeEvent(self, ev):
        self.closing.emit()
    
    @QtCore.pyqtSlot()
    def closedNicely(self):
        app.quit()
        
        
def startApp():
    mainWindow = MainWindow()
    mainWindow.show()
    
    sys.exit(app.exec_())
    #app.exec_()