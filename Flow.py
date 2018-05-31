import numpy as np

from Points import Point2D
from Raster import Raster

class FlowNode(Point2D):
    
    def __init__(self,x,y, value):
        Point2D.__init__(self,x,y)
        self._downnode=None
        self._upnodes=[]
        self._pitflag=True
        self._value=value
        self._flow=None
        self._rainfall=1
        self._lakeDepth = 0
        self._lakeFlag = False
        
    def setDownnode(self, newDownNode):
        self._pitflag=(newDownNode==None)
        
        if (self._downnode!=None):
            self._downnode._removedUpnode(self)
            
        if (newDownNode!=None):
            newDownNode._addUpnode(self)
            
        self._downnode=newDownNode 
        
    def getDownnode(self):
        return self._downnode 
        
    def getUpnodes(self):
        return self._upnodes
    
    def _removedUpnode(self, nodeToRemove):
        self._upnodes.remove(nodeToRemove)
    
    def _addUpnode(self, nodeToAdd):
        self._upnodes.append(nodeToAdd)

    def numUpnodes(self):
        return len(self._upnodes)
        
    def getPitFlag(self):
        return self._pitflag 
    
    def setRainfall(self, rainvalue=1):
        '''assigns rainfall value from raster to the flow node. 
        Also resets flow for analysis using new rainfall values.'''
        self._rainfall = rainvalue
        self._flow = None
        
    def getRainfall(self):
        return self._rainfall
    
    def getLakeDepth(self):
        return self._lakeDepth
    
    def getElevation(self):
        return self._value

#    def getFlow(self):
#        '''Version 1.
#        Recursively counts all connected upnodes, 
#        returns total water volume for flow node'''        
#        if self._flow==None:
#            #returns 1 if no further upnodes to add
#            if self.numUpnodes()==0:
#                self._flow = 1
#                return self._flow
#            else:
#                flow=0
#                #for each upnode, call getFlow again
#                for node in self.getUpnodes():                            
#                    flow += node.getFlow()                
#                #adds last cell's rainfall to the total
#                self._flow=flow + 1
#                return self._flow
#        else:
#            return self._flow
   
    def getFlow(self):
        '''Version 2.
        Recursively counts all connected upnodes, 
        returns total water volume for flow node'''        
        if self._flow==None:
            #returns node's rainfall if no further upnodes to add
            if self.numUpnodes()==0:
                self._flow = self._rainfall
                return self._flow
            else:
                flow=0
                #add rainfall from upnodes, call getFlow again
                for node in self.getUpnodes():                            
                    flow += node.getFlow()                
                #adds last cell's rainfall to the total
                self._flow=flow + self._rainfall
                return self._flow
        else:
            return self._flow                    
  
    def __str__(self):
        return "Flownode x={}, y={}".format(self.get_x(), self.get_y())
    
class FlowRaster(Raster):

    def __init__(self,araster):
        super().__init__(None,araster.getOrgs()[0],araster.getOrgs()[1],
              araster.getCellsize())
        data = araster.getData()
        nodes=[]
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                y=(i)*self.getCellsize()+self.getOrgs()[0]
                x=(j)*self.getCellsize()+self.getOrgs()[1]
                nodes.append(FlowNode(x,y, data[i,j]))

        nodearray=np.array(nodes)
        nodearray.shape=data.shape
        self._data = nodearray

        self.__neighbourIterator=np.array(
                [1,-1,1,0,1,1,0,-1,0,1,-1,-1,-1,0,-1,1] )
        self.__neighbourIterator.shape=(8,2)
        self._pits = []
        self.setDownCells()
        
              
    def getNeighbours(self, r, c):
        neighbours=[]
        for i in range(8):
            rr=r+self.__neighbourIterator[i,0]
            cc=c+self.__neighbourIterator[i,1]
            if (rr>-1 and rr<self.getRows() and 
                cc>-1 and cc<self.getCols()):
                neighbours.append(self._data[rr,cc])
                
        return neighbours
    
    def lowestNeighbour(self,r,c):
        lownode=None
        
        for neighbour in self.getNeighbours(r,c):
            if lownode==None or \
            neighbour.getElevation() < lownode.getElevation():
                lownode=neighbour
        
        return lownode

    def setDownCells(self):
       for r in range(self.getRows()):
           for c in range(self.getCols()):
               lowestN = self.lowestNeighbour(r,c)
               if (lowestN.getElevation() < \
                   self._data[r,c].getElevation()):
                   self._data[r,c].setDownnode(lowestN)
               else:
                   self._data[r,c].setDownnode(None)
                   self._pits.append(self._data[r,c])
    
    def extractValues(self, extractor):
        values=[]
        for i in range(self._data.shape[0]):
            for j in range(self._data.shape[1]):
                values.append(extractor.getValue(self._data[i,j]))
        valuesarray=np.array(values)
        valuesarray.shape=self._data.shape
        return valuesarray
    
    def getMaxFlow(self):
        '''extract the node with greatest flow value'''
        maxFlow = 0
        maxNode = None
        for r in range(self.getRows()):
            for c in range(self.getCols()):
                if self._data[r,c]._flow > maxFlow:
                    maxFlow = self._data[r,c]._flow
                    maxNode = self._data[r,c]
        return maxFlow, maxNode
    
    def addRainfall(self, rainraster):
        '''gets rainfall data for each cell, 
        assigns value to associated flow node'''
        for r in range(self._data.shape[0]):
            for c in range(self._data.shape[1]):
                self._data[r,c].setRainfall(rainraster[r,c])
                
     
    def calculateLakes(self):
        #if a pit has fewer than 8 neighbours, 
        #it is on a raster edge and water can flow out
        for pit in self._pits:
            neighbours = self.getNeighbours(int(pit.get_y()),
                                            int(pit.get_x()))
            if len(neighbours) < 8:
                pass            
            #find the lake extent if the pit is not at an edge
            else:
                self.growLake(pit)            
            
            
    def growLake(self, pit):
        '''finds extent of a topographical depression (lake)
        surrounding a node'''
        #flags pit to be part of a lake
        pit._lakeFlag = True
        #list keeps a record of all nodes added to the current lake
        nodes_in_lake = [pit]
        #flag keeps track of when one lake has been fully completed
        found_outlet = False
        while not found_outlet:
            #find the lowest node on the lake's perimeter
            lowest=None            
            #check neighbours of all lake nodes
            for node in nodes_in_lake:
                neighbours = self.getNeighbours(int(node.get_y()), 
                                                int(node.get_x()))
                for neighbour in neighbours:
                    #lowest node cannot already be in the lake
                    if neighbour not in nodes_in_lake:
                        if lowest==None or \
                        neighbour.getElevation() < lowest.getElevation():   
                            lowest=neighbour
            #sets flag to true if the node drains
            found_outlet = self.node_drains(lowest, nodes_in_lake)
            #add lowest perimeter node to the lake if it doesn't drain
            if not found_outlet:    
                lowest._lakeFlag = True
                nodes_in_lake.append(lowest)
            #if node drains away, set the lake pit's downnode to outlet
            elif found_outlet:
                pit.setDownnode(lowest)
                break               
        #assign depths to all nodes in the completed lake
        self.calcLakeDepth(nodes_in_lake)

    
    def node_drains(self, node, nodes_in_lake):
        '''checks if a node drains away from the current lake'''
        drains = True
        #node cannot be an upnode of any other node in the lake
        for n in nodes_in_lake:
            if node in n.getUpnodes():
                drains = False
        #if node is already part of a lake, can't assume it will drain
        #ensures that any previous lake will be subsumed by current lake
        if node._lakeFlag == True:
            drains = False
        return drains
    
    def calcLakeDepth(self, nodes_in_lake):
        '''assigns lake depths to all nodes in a complete lake'''
        depths = []
        #get elevations for all nodes in the lake
        for node in nodes_in_lake:
            depths.append(node.getElevation())
        #calculate and assign lake depth for each node
        for node in nodes_in_lake:
            node._lakeDepth = max(depths)-node.getElevation()
                           
                
class FlowExtractor():
    def getValue(self, node):
        return node.getFlow()
    
class LakeDepthExtractor():
    def getValue(self, node):
        return node.getLakeDepth()


