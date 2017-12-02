from pyqtgraph.graphicsItems.ROI import PolyLineROI
from pyqtgraph.graphicsItems.ROI import ROI

class PolyLineROI_new(PolyLineROI):
    def __init__(self, pos, **kwds):
        PolyLineROI.__init__(self, pos)

    def getArrayRegion(self, data, img, axes=(0,1), **kwds):
        """
        This is the custom getArrayRegion to remove the exception from line 2015 of actual getArrayRegion from ROI of pyqtgraph
        """
        br = self.boundingRect()
        sliced = ROI.getArrayRegion(self, data, img, axes=axes, fromBoundingRect=True, **kwds)
        
        if img.axisOrder == 'col-major':
            mask = self.renderShapeMask(sliced.shape[axes[0]], sliced.shape[axes[1]])
        else:
            mask = self.renderShapeMask(sliced.shape[axes[1]], sliced.shape[axes[0]])
            mask = mask.T
            
        # reshape mask to ensure it is applied to the correct data axes
        shape = [1] * data.ndim
        shape[axes[0]] = sliced.shape[axes[0]]
        shape[axes[1]] = sliced.shape[axes[1]]
        mask = mask.reshape(shape)

        return sliced * mask





