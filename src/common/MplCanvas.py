from PyQt4 import QtGui, QtCore
# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# Matplotlib Figure object
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""
    def __init__(self):
        # setup Matplotlib Figure and Axis
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)
        
        self.background = None
        self.old_dimensions = self.ax.bbox.width, self.ax.bbox.width
    
    def setBackground(self):
        self.draw()
        self.background = self.copy_from_bbox(self.ax.bbox)
        
    def restoreBackground(self):
        current_dimensions = self.ax.bbox.width, self.ax.bbox.width
        if self.background == None or current_dimensions != self.old_dimensions:
            self.setBackground()
            self.old_dimensions = current_dimensions
        self.restore_region(self.background, self.ax.bbox)
        
    def resizeEvent(self, ev):
        FigureCanvas.resizeEvent(self, ev)
        #self.restoreBackground()
        #self.setBackground()
        #self.background == None