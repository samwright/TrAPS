import numpy as np
from time import sleep

class SpectrometerDevice:
    
    def getSpectrum(self):
        data = list(np.array([2,4,5,4,3,4,5,6,7,2]*20)*np.random.random())
        #sleep(0.5)
        return data
        
    def __init__(self):
        self.wavelengths = range(1, 201)
        
    def close(self):
        pass
        
    