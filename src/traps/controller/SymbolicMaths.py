import numexpr
from PyQt4 import QtGui, QtCore

class MathsWorkerClass(QtCore.QObject):
    calculatedCoords = QtCore.pyqtSignal(list)
    
    @QtCore.pyqtSlot(dict, list, list)
    def calculateCoords(self, var_data, view_data, varying_temps):
        output_view_data = []
        
        for view_datum in view_data:
            try:
                coords = list(numexpr.evaluate(view_datum['equation'], var_data))
                if hasattr(coords[0], '__iter__'):
                    # coords is therefore a list of spectra
                    temps = varying_temps
                else:
                    temps = []
                output_view_data.append(
                                        dict(
                                            coords=coords,
                                            temps=temps,
                                            text=view_datum['text'],
                                            colour=view_datum['colour']
                                            )
                                        )
                var_data[view_datum['text']] = coords
                
            except SyntaxError:
                pass
        self.calculatedCoords.emit(output_view_data)