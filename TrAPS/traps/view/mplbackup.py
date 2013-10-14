#!/usr/bin/env python
"""
import sys
import os.path
parent_dir = os.path.abspath('..')
sys.path.append(parent_dir)
"""

from collections import defaultdict
from copy import copy

# Python Qt4 bindings for GUI objects
from PyQt4 import QtGui, QtCore

# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_agg import FigureCanvasAgg
import pylab
import numexpr

# Matplotlib Figure object
from matplotlib.figure import Figure

from matplotlib.lines import Line2D

from sympy import var, sympify
from sympy.utilities.lambdify import lambdify

from ..model import DB

class MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""
    def __init__(self):
        # setup Matplotlib Figure and Axis
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0,10)

        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)
        
        #self.hidden = HiddenFigureCanvas()
        
        #self.background = self.copy_from_bbox(self.ax.bbox)
        
        #self.ax.plot([0,1],[0,1],color='red')
        #self.draw()
        
class HiddenFigureCanvas(FigureCanvasAgg):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0,10)
        self.ax.set_autoscale_on(False)
        FigureCanvasAgg.__init__(self, self.fig)
        self.background = self.copy_from_bbox(self.ax.bbox)
        
    def getImage(self, x, y, color):
        self.restore_region(self.background)
        self.ax.plot(x, y, color=color)
        image = self.copy_from_bbox(self.ax.bbox)
        return image


class MplWidget(QtGui.QWidget):
    """Widget defined in Qt Designer"""
    def __init__(self, parent = None):
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        # set the canvas to the Matplotlib widget
        self.canvas = MplCanvas()
        # create a vertical box layout
        self.vbl = QtGui.QVBoxLayout()
        # add mpl widget to the vertical box
        self.vbl.addWidget(self.canvas)
        # set the layout to the vertical box
        self.setLayout(self.vbl)
        
        self.graphs = defaultdict(list)
        self.equations = {}
        self.coords = defaultdict(list)
        self.persistent = False
    
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem)
    def redrawView(self, view):
        variables = tuple(var(copy(variable)) for variable in view.variables_used)
        #self.equations[view] = lambdify(variables, view.equation)
        self.equations[view] = view.equation
        self.coords[view] = []
        variable_values = self.getStaticDatumForUsedVariables(view)
        self.redrawGraph()
        
        if view.variable_with_many_spectra != None:
            for changing_spectrum in view.data[view.variable_with_many_spectra.text()]:
                variable_values[view.variable_with_many_spectra.text()] = changing_spectrum
                coords_dict = self.evaluateSpectra(self.equations[view], variable_values)
                self.coords[view].append(coords_dict)
                self.drawCoord(coords_dict, view.item.background(2).color().getRgbF())
        else:
            coords_dict = self.evaluateSpectra(self.equations[view], variable_values)
            self.coords[view].append(coords_dict)
            self.drawCoord(coords_dict, view.item.background(2).color().getRgbF())
        self.canvas.draw()
            
    def evaluateSpectra(self, equation, variable_values):
        coords = dict(x=DB.Data.xData, y=numexpr.evaluate(equation, variable_values))
        return dict(variables=variable_values, coords=coords)
        
    def oldEvaluateSpectra(self, equation, variable_values):
        var_dict = {}
        coords = dict(x=DB.Data.xData, y=[])
        for x in DB.Data.xData:
            var_dict = dict((variable, values[x]) for variable, values in variable_values.iteritems())
            try:
                y = equation(**var_dict)
                print 'y = %f' %y
            except ZeroDivisionError:
                print 'divided by zero!'
                y=0
            except NameError:
                print "Couldn't understand equation.  Are functions spelt correctly?"
            #coords['x'].append(x)
            coords['y'].append(y)
        
        #self.images[view].append( dict(variables=variable_values, image=self.createImage(view.item.background(2).color(), coords)) )
        #return self.createImage(view.item.background(2).color(), coords)
        return dict(variables=variable_values, coords=coords)
    
    """
    def createImage(self, colour, coords):
        # make an image objectdrawCoord
        #imageObj = object()
        #image = pylab.plot(coords['x'], coords['y'], color="blue")#colour.getRgbF())
        #print 'drawing now... %s' %`zip(coords['x'],coords['y'])`
        image = self.canvas.ax.plot(coords['x'], coords['y'], color=colour.getRgbF())
        #image = Line2D(coords['x'], coords['y'], color=colour.getRgbF())
        #self.canvas.ax.draw_artist(image)
        #image = self.canvas.hidden.getImage(coords['x'], coords['y'], color=colour.getRgbF())
        #print 'got image: %s' %`image`
        #self.canvas.ax.figure.canvas.blit(image)
        #self.canvas.blit(self.canvas.ax.bbox)
        self.canvas.draw()
        return image
    """
        
    def getStaticDatumForUsedVariables(self, view, exceptView=None):
        return dict((variable, view.data[variable][0]) for variable in view.variables_used if not variable == view.variable_with_many_spectra)
        
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem)
    def removeView(self, view):
        if view in self.coords:
            del self.coords[view]
            self.redrawGraph()
            self.canvas.draw()
       
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, list, bool)
    def includeDatumFromView(self, view, datum, include):
        if include:
            variable_values = self.getStaticDatumForUsedVariables(view)
            variable_values[view.variable_with_many_spectra.text()] = datum
            coords_dict = self.evaluateSpectra(self.equations[view], variable_values)
            self.coords[view].append(coords_dict)
            self.drawCoord(coords_dict, view.item.background(2).color().getRgbF())
            self.canvas.draw()
        else:
            """
            for coords_dict in self.coords[view]:
                if coords_dict['variables'][view.variable_with_many_spectra] == datum:
                    self.coords[view].remove(coords_dict)
                    self.redrawGraph()
                    self.canvas.draw()
                    return
            """
            self.redrawView(view)
                    
    def redrawGraph(self):
        if self.persistent == False:
            self.canvas.ax.clear()
        for view, coords_dict_list in self.coords.iteritems():
            for coords_dict in coords_dict_list:
                self.drawCoord(coords_dict, view.item.background(2).color().getRgbF())
        """
        for view, image_dicts in self.images.iteritems():
            for image_dict in image_dicts:
                # self.addImageToGraph(image_dict['image'])
                print 'trying to print image %s' %`image_dict['image']`
                #self.canvas.ax.draw_artist(image_dict['image'])
                # self.addLabelToKey(view.text(), view.item.background(2))
        #self.canvas.blit(self.canvas.ax.bbox)
        #self.canvas.draw()
        """
        
    def drawCoord(self, coords_dict, color):
        x = coords_dict['coords']['x']
        y = coords_dict['coords']['y']
        self.canvas.ax.plot(x, y, color=color)

            

        