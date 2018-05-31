# -*- coding: utf-8 -*-
"""

"""
import numpy as np

class Raster(object):
    
    '''A class to represent 2-D Rasters'''

# Basic constuctor method
    def __init__(self,data,xorg,yorg,cellsize,nodata=-999.999):
        self._data=np.array(data)
        self._orgs=(xorg,yorg)
        self._cellsize=cellsize
        self._nodata=nodata
        
    def getData(self):
        return self._data
        
#return the shape of the data array      
    def getShape(self):
        return self._data.shape    
    
    def getRows(self):
        return self._data.shape[0]
        
    def getCols(self):
        return self._data.shape[1]
        
    def getOrgs(self):
        return self._orgs
        
    def getCellsize(self):
        return self._cellsize
    
    def getNoData(self):
        return self._nodata
        
#returns a new Raster with cell size larger by a factor (must be integer)
    def createWithIncreasedCellsize(self, factor):
       if factor== 1:
           return self
       else:
           #calculate number of rows and columns in new raster
           newRowNum = self.getRows() // factor
           newColNum = self.getCols() // factor
           #create empty raster
           newdata = np.zeros([newRowNum, newColNum])
           #iterate through cells in new aggregated raster
           for i in range(newRowNum):
               for j in range(newColNum):
                   sumCellValue = 0.0
                   #calculate sum of all cells to aggregate into one cell 
                   for k in range(factor):
                       for l in range(factor):
                           sumCellValue += self._data[i*factor + k, j*factor + l]
                   newdata[i,j] = sumCellValue / factor / factor + 100
                   
           return Raster(newdata, self._orgs[0], self._orgs[1], 1)
    