import sys
import os
import csv

from PyQt4 import QtCore, QtGui
import xlwt

from ..model import View, DB
from helpers import SmartTabWidget
import graph_ui

            
class GraphTabWidget(SmartTabWidget):
    def __init__(self, parent=None):
        SmartTabWidget.__init__(self, parent)
        self.defaultTabName = 'Graph'

    @QtCore.pyqtSlot()
    def addTab(self, tabObject=None, Name=None):
        newTab = GraphTab()
        SmartTabWidget.addTab(self, newTab)
        self.currentChanged.connect(self.drawCurrentGraph)
        
    @QtCore.pyqtSlot(int)
    def drawCurrentGraph(self, index):
        currentGraphTab = self.widget(index)
        #currentGraphTab.ui.mplWidget.refreshBackground()
        currentGraphTab.ui.mplWidget.drawCoords()
        
        
class GraphTab(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        hLayout = QtGui.QHBoxLayout(self)
        NewGraphWidget = QtGui.QWidget()
        self.ui = graph_ui.Ui_Form()
        self.ui.setupUi(NewGraphWidget)
        #self.ui.splitter.setStretchFactor(0,0)
        #self.ui.splitter.setStretchFactor(1,1)
        hLayout.addWidget(NewGraphWidget)
        
        self.viewCount = 0
        self.ui.addViewButton.clicked.connect(self.addView)
        self.ui.removeViewButton.clicked.connect(self.removeView)
        self.ui.treeWidget.headerItem()
        self.ui.treeWidget.setColumnWidth(0, 200)
        self.ui.treeWidget.setColumnWidth(1, 250)
        
        self.ui.treeWidget.itemActivated.connect(self.editItemSelectively)
        self.ui.treeWidget.itemChanged.connect(self.updateView)
        
        self.ui.x_unit_type_box.currentIndexChanged.connect(self.changeAxesUnit)
        self.ui.wavelength_units.currentIndexChanged.connect(self.changeAxesUnit)
        self.ui.wavenumber_units.currentIndexChanged.connect(self.changeAxesUnit)
        self.ui.energy_units.currentIndexChanged.connect(self.changeAxesUnit)
        
        self.ui.lowerY.valueChanged[float].connect(self.setLowerYLimit)
        self.ui.upperY.valueChanged[float].connect(self.setUpperYLimit)
        
        self.ui.exportSelected.clicked.connect(self.export)
        self.homedir = os.path.expanduser('~')
        
        
    @QtCore.pyqtSlot()
    def addView(self):
        self.viewCount += 1
        self.ui.treeWidget.itemChanged.disconnect(self.updateView)
        newView = View(self.ui.treeWidget, DB.View[self.ui.mplWidget])
        newView.item.setText(0, "view%d" %self.viewCount)
        self.ui.treeWidget.itemChanged.connect(self.updateView)
        DB.View[self.ui.mplWidget].updateTextDict()
    
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, int)
    def editItemSelectively(self, viewItem, column):
        if column < 2:
            self.ui.treeWidget.editItem(viewItem, column)
        elif column == 2:
            viewItem.changeColour()
            self.ui.mplWidget.drawCoords()
            
    def safelyRenameViewItem(self, viewItem):
        viewItem.setText(0, "%s_" %viewItem.text(0))
        print 'renaming...eq=%s' %viewItem.text(1)
            
    @QtCore.pyqtSlot(QtGui.QTreeWidgetItem, int)
    def updateView(self, viewItem, column):
        text = str(viewItem.text(0))
        if column < 2:
            #view = DB.View[self.ui.mplWidget].textDict[text]
            if column == 0:
                if text in DB.View[self.ui.mplWidget].textDict:
                    if DB.View[self.ui.mplWidget].textDict[text].item == viewItem:
                        if viewItem.checkState(0) == QtCore.Qt.Checked:
                            disabled = False
                        else:
                            disabled = True
                        DB.View[self.ui.mplWidget].textDict[text].disabled = disabled
                        self.ui.mplWidget.drawCoords()
                        return
                    else:
                        self.safelyRenameViewItem(viewItem)
                        return
                elif text in ['', 'live'] + [var.text() for var in DB.Variable.children()]:
                    self.safelyRenameViewItem(viewItem)
                    return
                DB.View[self.ui.mplWidget].updateTextDict()
                #self.ui.mplWidget.updateDepName(view)
                self.ui.mplWidget.updateDepName()
            elif column == 1:
                #self.ui.mplWidget.updateDepData(view)
                self.ui.mplWidget.updateDepData()
        
    @QtCore.pyqtSlot(int)
    def changeAxesUnit(self, index):
        x_unit_type = self.ui.x_unit_type_box.currentIndex()
        x_unit_type_str = self.ui.x_unit_type_box.currentText()
        if x_unit_type == 0:
            x_units_box = self.ui.wavelength_units
        elif x_unit_type == 1:
            x_units_box = self.ui.wavenumber_units
        elif x_unit_type == 2:
            x_units_box = self.ui.energy_units
        
        self.ui.mplWidget.x_unit_type = x_unit_type
        self.ui.mplWidget.x_units = x_units_box.currentIndex()
        x_units_str = x_units_box.currentText()
        self.ui.mplWidget.xLabel = "%s (%s)" %(x_unit_type_str, x_units_str)
        self.ui.mplWidget.updateXAxis()
        
    @QtCore.pyqtSlot(float)
    def setUpperYLimit(self, limit):
        self.ui.mplWidget.yUpperLimit = limit
        self.ui.mplWidget.updateYAxis()
        
    @QtCore.pyqtSlot(float)
    def setLowerYLimit(self, limit):
        self.ui.mplWidget.yLowerLimit = limit
        self.ui.mplWidget.updateYAxis()
    
    @QtCore.pyqtSlot()
    def removeView(self):
        viewTreeItem = self.ui.treeWidget.selectedItems()[0]
        for view in DB.View[self.ui.mplWidget].children():
            if view.item == viewTreeItem:
                self.ui.mplWidget.removeViews(view)
                view.deleteLater()
                self.ui.mplWidget.updateDeps()
                return
    
    @QtCore.pyqtSlot()
    def export(self):
        if len(self.ui.mplWidget.plot) == 0:
            return
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save Data as...", self.homedir, "Excel Workbook (*.xls);;Comma Separated Values (*.csv)")
        if filename == '':
            return
        self.homedir = os.path.dirname(str(filename))
        """
        if filename[-3:] == 'xls':
            self.exportToExcelFile(filename)
        elif filename[-3:] == 'csv':
            self.exportToCSVFile(filename)
        else:
            print "Couldn't match file %s to a file type" %`filename`
        """
        #self.exportToCSVFile(filename)
        self.exportToExcelFile(filename)
            
    def exportToCSVFile(self, filename):
        x_label = self.ui.mplWidget.canvas.ax.get_xlabel()
        for view, plots in self.ui.mplWidget.plot.iteritems():
            outfile = open("%s_%s.csv" %(filename, view.text()), 'w')
            csvout = csv.writer(outfile)
            
            labels = [x_label, "%s = %s" %(view.text(), view.getData())]
            csvout.writerow(labels)
            
            temps = ['Temperature (K)'] + view.getTemp()
            csvout.writerow(temps)
            csvout.writerow([])
            
            data = [plots[0].get_xdata()] + [ plot.get_ydata() for plot in plots ]
            rows = zip(*data)
            csvout.writerows(rows)
            
            outfile.close()
        
        outfile = open("%s_raw.csv" %filename, 'w')
        csvout = csv.writer(outfile)
        constants_used = set()
        for view in self.ui.mplWidget.plot.keys():
            constants_used.update(view.deps['variable'])
           
        labels = [x_label]
        all_temps = ['Temperature (K)']
        all_data = [plots[0].get_xdata()]
           
        for var_text in constants_used:
            var = DB.Variable.textDict[var_text]
            temps = var.getTemp()
            labels.extend([var.text()] * len(temps))
            all_temps.extend(temps)
            all_data.extend(var.getData())
            
        all_data_transposed = zip(*all_data)
            
        csvout.writerow(labels)
        csvout.writerow(all_temps)
        csvout.writerow([])
        csvout.writerows(all_data_transposed)
        
        outfile.close()
            
    def exportToExcelFile(self, filename):
        x_label = self.ui.mplWidget.canvas.ax.get_xlabel()
        workbook = xlwt.Workbook()
        for view, plots in self.ui.mplWidget.plot.iteritems():
            view_sheet = workbook.add_sheet(view.text())
            xdata = plots[0].get_xdata()
            temps = view.getTemp()
            view_sheet.write(0, 0, x_label)
            for j, xdatum in enumerate(xdata, start=3):
                view_sheet.write(j, 0, xdatum)
            #view_sheet.write(0, 2, "%s (%s)" %(view.text(), view.getData()))
            for i, plot in enumerate(plots, start=1):
                if temps != []:
                    view_sheet.write(1, i, temps[i-1])
                view_sheet.write(0, i, "%s (%s)" %(view.text(), view.getData()))
                view_sheet.write(2, i, "Counts")
                for j, ydatum in enumerate(plot.get_ydata(), start=3):
                    view_sheet.write(j, i, ydatum)
        constants_sheet = workbook.add_sheet('Constants')
        constants_sheet.write(0, 0, x_label)
        constants_sheet.write(1, 1, 'Temp (K) = ')
        for j, xdatum in enumerate(xdata, start=3):
            constants_sheet.write(j, 0, xdatum)
        constants_used = set()
        for view in self.ui.mplWidget.plot.keys():
            constants_used.update(view.deps['variable'])
            
        i=2
        for var_text in constants_used:
            var = DB.Variable.textDict[var_text]
            temps = var.getTemp()
            print 'var %s has temps %s' %(var.text(), `temps`)
            for data_index, data in enumerate(var.getData()):
                constants_sheet.write(0, i, var_text)
                constants_sheet.write(1, i, temps[data_index])
                for j, datum in enumerate(data, start=3):
                    constants_sheet.write(j, i, datum)
                i += 1
                
            
        workbook.save(filename)
        
        
            