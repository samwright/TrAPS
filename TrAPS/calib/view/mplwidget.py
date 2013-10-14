import time

from PyQt4 import QtGui, QtCore
import numpy as np

from ...common.MplCanvas import MplCanvas

class MplDoubleYAxisCanvas(MplCanvas):
    def __init__(self):
        MplCanvas.__init__(self)
        self.leftAxis = self.ax
        self.rightAxis = self.ax.twinx()

class MplWidget(QtGui.QWidget):
    needMoreLiveData = QtCore.pyqtSignal()
    
    def __init__(self, parent = None):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        # set the canvas to the Matplotlib widget
        self.canvas = MplDoubleYAxisCanvas()
        # create a vertical box layout
        self.vbl = QtGui.QVBoxLayout()
        # add mpl widget to the vertical box
        self.vbl.addWidget(self.canvas)
        # set the layout to the vertical box
        self.setLayout(self.vbl)
        
        self.tStart = time.time()
        self.tNum = 0
        
        self.canvas.ax.set_xlabel('Temperature (K)')
        
        self.newVisible = self.calVisible = True
        
        #### self.canvas.ax.autoscale(False)
        self.canvas.draw()
        
        self.x_min = 0
        self.x_max = 330
        self.x_steps = 1000
        
        self.leftLabel = 'Calibrated device: not loaded'
        self.rightLabel = 'New device: not loaded'
        self.leftYMin = self.rightYMin = 0
        self.leftYMax = self.rightYMax = 2
        
        self.newCurve = self.calCurve = None
        self.newData = self.calData = None
        
        self.updateXAxis()
        self.updateYAxes()
    
    @QtCore.pyqtSlot(object, list)
    def drawCalCurve(self, func, volt_range):
        self.leftYMin, self.leftYMax = volt_range
        voltages = np.linspace(self.leftYMin, self.leftYMax, 1000)
        temps = [ func(volt) for volt in voltages ]
        if self.calCurve == None:
            self.calCurve, = self.canvas.leftAxis.plot(temps, voltages, color=(0, 0, 0.5), animated=True, alpha=0.5)
        else:
            self.calCurve.set_data(temps, voltages)
        self.updateYAxes()
        self.drawCoords()
        
    
    @QtCore.pyqtSlot(object, list)
    def drawNewCurve(self, func, volt_range):
        self.rightYMin, self.rightYMax = volt_range
        voltages = np.linspace(self.rightYMin, self.rightYMax, 1000)
        temps = [ func(volt) for volt in voltages ]
        if self.newCurve == None:
            self.newCurve, = self.canvas.rightAxis.plot(temps, voltages, color=(0.5, 0, 0), animated=True, alpha=0.5)
        else:
            self.newCurve.set_data(temps, voltages)
        self.updateYAxes()
        self.drawCoords()
        
        
    @QtCore.pyqtSlot(list)
    def drawCalData(self, curve_data):
        plottable_data = [ point for point in curve_data if point != [] ]
        if plottable_data == []:
            temps, voltages = [], []
        else:
            temps, voltages = zip(*plottable_data)
        if self.calData == None:
            self.calData, = self.canvas.leftAxis.plot(temps, voltages, color=(0, 0, 0.5), animated=True, linestyle='None', marker='+')
        else:
            self.calData.set_data(temps, voltages)
        self.drawCoords()
    
    @QtCore.pyqtSlot(list)
    def drawNewData(self, curve_data):
        plottable_data = [ point for point in curve_data if point != [] ]
        if plottable_data == []:
            temps, voltages = [], []
        else:
            temps, voltages = zip(*plottable_data)
        if self.newData == None:
            self.newData, = self.canvas.rightAxis.plot(temps, voltages, color=(0.5, 0, 0), animated=True, linestyle='None', marker='x')
        else:
            self.newData.set_data(temps, voltages)
        self.drawCoords()   
 
    def drawCoords(self):
        self.canvas.restoreBackground()
        if self.calVisible:
            if self.calCurve != None:
                self.canvas.leftAxis.draw_artist(self.calCurve)
            if self.calData != None:
                self.canvas.leftAxis.draw_artist(self.calData)
        if self.newVisible:
            if self.newCurve != None:
                self.canvas.rightAxis.draw_artist(self.newCurve)
            if self.newData != None:
                self.canvas.rightAxis.draw_artist(self.newData)
                    
        self.canvas.blit(self.canvas.leftAxis.bbox)
        self.canvas.blit(self.canvas.rightAxis.bbox)
        
        #self.needMoreLiveData.emit()
        #print 'asking for more...'
        
        self.tNum += 1
        if self.tNum == 1000:
            tDelta = time.time() - self.tStart
            print 'Took %d to draw 1000 frames.  %f fps' %(tDelta, float(1000/tDelta))
            self.tStart = time.time()
            self.tNum = 0
            
    
    @QtCore.pyqtSlot(float)
    def setMinTemp(self, temp):
        self.x_min = temp
        self.updateXAxis()
        
    @QtCore.pyqtSlot(float)
    def setMaxTemp(self, temp):
        self.x_max = temp
        self.updateXAxis()
        
    @QtCore.pyqtSlot(bool)
    def setCalVisible(self, visible):
        self.calVisible = visible
        self.drawCoords()
        
    @QtCore.pyqtSlot(bool)
    def setNewVisible(self, visible):
        self.newVisible = visible
        self.drawCoords()
            
    def updateXAxis(self):
        self.x = np.linspace(self.x_min, self.x_max, self.x_steps)
        
        self.canvas.ax.set_xlim(self.x[0], self.x[-1])
        
        self.canvas.draw()
        
        if self.canvas.background != None:   
            self.drawCoords()
        
        self.canvas.repaint()
            
        
    def updateYAxes(self):
        self.canvas.leftAxis.set_ylim(self.leftYMin, self.leftYMax)
        self.canvas.leftAxis.set_ylabel(self.leftLabel)
        self.canvas.rightAxis.set_ylim(self.rightYMin, self.rightYMax)
        self.canvas.rightAxis.set_ylabel(self.rightLabel)
        
        self.canvas.draw()
        self.canvas.repaint()
        
        # just added this...
        if self.canvas.background != None:   
            self.drawCoords()
        