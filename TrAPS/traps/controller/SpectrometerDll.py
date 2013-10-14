from ctypes import *
specDll = windll.UsbSpectrometer
IN_ARG = 1
OUT_ARG = 2

prototype = CFUNCTYPE(c_double, c_int32)
paramflags = (IN_ARG, "in", c_int32(10)),
Test = prototype(("Test", specDll), paramflags)

prototype = CFUNCTYPE(c_voidp, c_double * 4000, c_int32)
paramflags = (OUT_ARG, "spectrum"), (IN_ARG, "length", 4000)
GetSpectrum = prototype(("GetSpectrum", specDll), paramflags)

prototype = CFUNCTYPE(c_voidp, c_double * 4000, c_int32)
paramflags = (OUT_ARG, "wavelengths"), (IN_ARG, "length")
GetWavelengths = prototype(("GetWavelengths", specDll), paramflags)

prototype = CFUNCTYPE(c_voidp, c_int32)
paramflags = (IN_ARG, "time"),
SetIntTime = prototype(("SetIntTime", specDll), paramflags)

prototype = CFUNCTYPE(c_voidp, c_int32)
paramflags = (IN_ARG, "trigger_type", 0),
SetTrigger = prototype(("SetTrigger", specDll), paramflags)

prototype = CFUNCTYPE(c_int32)
paramflags = ()
Init = prototype(("Init", specDll), paramflags)

prototype = CFUNCTYPE(c_voidp)
paramflags = ()
Close = prototype(("Close", specDll), paramflags)

#@singleton
class SpectrometerDevice:
    def __init__(self):
        self.array_length = Init()
        self.wavelengths = GetWavelengths(self.array_length)[:self.array_length]
        
    def getSpectrum(self):
        return GetSpectrum()[:self.array_length]
        
    def setTrigger(self, trigger_type):
        SetTrigger(c_int32(trigger_type))
        
    def setIntTime(self, time):
        if time < 3800:
            raise Exception('Integration time too small')
        SetIntTime(c_int32(time))
        
    def close(self):
        Close()
        
if __name__ == 'main':
    s=Spectrometer()
    