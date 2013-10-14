import time
from collections import defaultdict
import compiler
import re

from PyQt4 import QtGui, QtCore
import numexpr
import numpy as np

from ...common.MplCanvas import MplCanvas
from ..model import DB, Variable, UNDEFINED, ONE_SPECTRUM, MANY_SPECTRA
from ..controller import MathsWorkerClass

re_all_names = re.compile('Name\(\'(.*?)\'\)')
re_funcs = re.compile('CallFunc\(Name\(\'(.*?)\'\)')

app = QtGui.QApplication.instance()


class MplWidget(QtGui.QWidget):
    """Widget defined in Qt Designer"""
    coordsNeedCalculating = QtCore.pyqtSignal(dict, list, list)
    
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
        
        self.coords = defaultdict(list)
        self.persistent = False
        self.worker = MathsWorkerClass()
        worker = self.worker
        workerThread = QtCore.QThread(app)
        worker.moveToThread(workerThread)
        
        self.coordsNeedCalculating.connect(worker.calculateCoords)
        
        worker.calculatedCoords.connect(self.drawCoords)
        
        workerThread.start()
        
        self.plot = defaultdict(list)
        
        self.tStart = time.time()
        self.tNum = 0
        self.parsable_views = set()
        self.x_unit_type = 0
        self.x_units = 0
        self.xLabel = "Wavelength (Nanometres)"
        self.yLowerLimit = 0
        self.yUpperLimit = 10
        
        #self.canvas.ax.get_xaxis().set_animated(True) 
        #self.canvas.ax.grid()
        self.canvas.ax.autoscale(False)
        self.canvas.draw()
        
        self.updateXAxis()
        self.updateYAxis()
        self.all_deps = set()
        #self.canvas.setBackground()
        #QtCore.QTimer.singleShot(0, self.canvas.setBackground)
        
    def updateDepName(self):
        self.updateDeps()
    def updateDepStatus(self):
        self.updateDeps()
    def updateDepData(self):
        self.updateDeps()
    
    def updateDeps(self):
        # Check that equations can be parsed, and variables/views referenced in equations do exist.
        self.all_deps = set()
        self.parsable_views = set()
        all_defined_symbols = set(sym.text() for sym in DB.Variable.children() + DB.View[self].children())
        #all_defined_symbols_with_sigmas = all_defined_symbols.update('sigma_%s' %view.text() 
        #                                    for view in DB.View[self].children() if view.getSigma() != '')
        all_variables_text = [var.text() for var in DB.Variable.children()]
        for view in DB.View[self].children():
            try:
                parsed_equation = str(compiler.parse(view.getData()))
                functions_used = set(re_funcs.findall(parsed_equation))
                all_names = set(re_all_names.findall(parsed_equation))
                deps = all_names.difference(functions_used)
                self.all_deps.update(deps)
                #print 'deps is %s, and all_variables_text is %s' %(`deps`, `all_variables_text`)
                view.deps['view'] = deps.difference(all_variables_text)
                #print "view %s has deps: %s" %(view.text(), `view.deps`)
                view.deps['variable'] = deps.difference(view.deps['view'])
                if not deps.issubset(all_defined_symbols):
                    raise SyntaxError
                self.parsable_views.add(view)
            except SyntaxError:
                self.removeViews(view)
                #print "Equation %s could not be parsed" %view.getData()
                
        self.drawViewsInOrder()
                
    def drawViewsInOrder_afterVariableChange(self, variables=set()):
        views_dependent_on_variables = set(view for view in DB.View[self] \
                                        if not view.deps['variable'].isdisjoint(variables))
        self.drawViewsInOrder(self, views_dependent_on_variables)
        
    def drawViewsInOrder(self, fromViews=set()):
        
        if fromViews != set():
            order = set(view.text() for view in fromViews)
            minimum_number_of_view_deps = 1
        else:
            order = [ view.text() for view in self.parsable_views \
                    if len(view.deps['view']) == 0 ]
            minimum_number_of_view_deps = 0
                
        #print 'order is %s' %`order`
        while True:
            remaining_views = set(view for view in self.parsable_views if view.text() not in order)
            next_in_order = [ view.text() for view in remaining_views \
                            if view.deps['view'].issubset(order) \
                            and len(view.deps['view']) >= minimum_number_of_view_deps ]
            if next_in_order == []:
                if len(remaining_views) == 0:
                    pass
                else:
                    self.removeViews(remaining_views)
                break
            order.extend( next_in_order )
        views_text_in_order = order
        variable_deps = set()
        undefined_views = set()
        view_data = []
        var_data = {}
        varying_temps = []
        for view_text in views_text_in_order:
            view = DB.View[self].textDict[view_text]
            multi_spectrum_variables = 0
            view.status = ONE_SPECTRUM
            for dep_variable_text in view.deps['variable']:
                try:
                    dep_var = DB.Variable.textDict[dep_variable_text]
                    if dep_var.status == MANY_SPECTRA:
                        multi_spectrum_variables += 1
                    elif dep_var.status == UNDEFINED:
                        view.status = UNDEFINED
                except KeyError:
                    #print '1'
                    view.status = UNDEFINED
            for dep_view_text in view.deps['view']:
                dep_view = DB.View[self].textDict[dep_view_text]
                if dep_view.status == MANY_SPECTRA:
                    multi_spectrum_variables += 1
                elif dep_view.status == UNDEFINED:
                    view.status = UNDEFINED
            if multi_spectrum_variables > 1:
                view.status = UNDEFINED
            elif multi_spectrum_variables == 1 and view.status is not UNDEFINED:
                view.status = MANY_SPECTRA
            if view.status is UNDEFINED:
                self.removeViews(view)
            else:
                view_data.append( 
                                dict(
                                    text = view_text,
                                    equation = view.getData(),
                                    colour = view.getColour()
                                    )
                                )
                variable_deps.update(view.deps['variable'])
            
        for variable_text in variable_deps:
            var = DB.Variable.textDict[variable_text]
            var_data[variable_text] = var.getData()
            if multi_spectrum_variables == 1 and var.status == MANY_SPECTRA:
                varying_temps = var.getTemp()
            
        self.coordsNeedCalculating.emit(var_data, view_data, varying_temps)
        
   
    def removeViews(self, views):
        if not hasattr(views, '__iter__'):
            views = [views]
        for view in views:
            if view in self.plot:
                del self.plot[view]
 
    @QtCore.pyqtSlot(dict)
    def drawCoords(self, view_data=[]):
        
        x = DB.Data.xData[self.x_unit_type][self.x_units]
        for view_datum in view_data:
            coords = view_datum['coords']
            colour = view_datum['colour']
            temps = view_datum['temps']
            view = DB.View[self].textDict[view_datum['text']]
            view.temps = temps
            try:
                first_coord = coords[0][0]
            except IndexError:
                coords = [coords]
            for i in range(len(coords)):
                try:
                    if view not in self.plot:
                        raise IndexError
                    plot = self.plot[view][i]
                    plot.set_ydata(coords[i])
                    plot.set_color(colour)
                except IndexError:
                    plot, = self.canvas.ax.plot(x, coords[i], color=colour, animated=True)
                    self.plot[view].append(plot)
            self.plot[view] = self.plot[view][:i+1]
            
        
        self.canvas.restoreBackground()
        for view, plots in self.plot.iteritems():
            if view.disabled == False:
                for plot in plots:
                    plot.set_color(view.getColour())
                    self.canvas.ax.draw_artist(plot)
                    
        self.canvas.blit(self.canvas.ax.bbox)
        
        #self.canvas.restore_region(self.background)
        
        live = DB.Variable.textDict['live']
        if self.isVisible():
            live.needMoreData.emit()
        
        self.tNum += 1
        if self.tNum == 1000:
            tDelta = time.time() - self.tStart
            print 'Took %d to draw 1000 frames.  %f fps' %(tDelta, float(1000/tDelta))
            self.tStart = time.time()
            self.tNum = 0
            
    def updateXAxis(self):
        #self.canvas.ax.clear() ### Added
        #self.canvas.draw()
        #self.refreshBackground()
        x = DB.Data.xData[self.x_unit_type][self.x_units]
        upper_x = np.max([x[0], x[-1]])
        lower_x = np.min([x[0], x[-1]])
        
        #self.canvas.ax.set_xlim(1e-9, 1e-8)
        self.canvas.ax.set_xlim(lower_x, upper_x)
        self.canvas.ax.set_xlabel(self.xLabel)
        #self.updateYAxis() ### removed
        
        self.canvas.draw()
        for view, plots in self.plot.iteritems():
            for plot in plots:
                plot.set_xdata(x)
                #self.canvas.ax.draw_artist(plot)
        if self.canvas.background != None:   
            self.drawCoords()
        
        self.canvas.repaint() ### Added
        #self.canvas.draw()
        #self.refreshBackground()
        #self.canvas.blit(self.canvas.ax.bbox)
            
        
    def updateYAxis(self):
        self.canvas.ax.set_ylim(self.yLowerLimit, self.yUpperLimit)
        self.canvas.draw()
        self.canvas.repaint()