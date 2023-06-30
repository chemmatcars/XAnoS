from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from pyqtgraph.dockarea import *
import pyqtgraph as pg
from PolyLineROI_new import PolyLineROI_new
import sys
import fabio as fb
import numpy as np
import os
from Image_Widget import Image_Widget
import copy

class MaskWidget(QWidget):
    def __init__(self,img,parent=None):
        QWidget.__init__(self,parent)
        self.imageData=img.T
        self.tmp_data=copy.copy(self.imageData)
        
        self.mask={}
        self.mask_type={}
        self.mask_val={}
        self.mask_data={}
        self.threshold={}
        self.mask_number=0
        
        self.vblayout=QVBoxLayout(self)
        self.mainDock=DockArea(self,parent)
        self.vblayout.addWidget(self.mainDock)
        self.imageDock=Dock('Image')
        self.maskControlDock=Dock('Mask Control')
        self.mainDock.addDock(self.maskControlDock,'left')
        self.mainDock.addDock(self.imageDock,'right')
        
        self.create_maskControlDock()
        self.create_imageDock()
        self.init_signals()
        
        
    def init_signals(self):
        self.drawShapePushButton.clicked.connect(self.draw_shape)
        self.shape_ListWidget.currentTextChanged.connect(self.shape_changed)
        self.removeShapePushButton.clicked.connect(self.remove_shape)
        self.openShapesPushButton.clicked.connect(self.open_shape_file)
        self.createMaskPushButton.clicked.connect(self.create_all_masks)
        self.saveShapesPushButton.clicked.connect(self.save_shape_file)
        self.saveMaskPushButton.clicked.connect(self.save_mask)
        
        
    def create_imageDock(self):
        self.imageLayout=pg.LayoutWidget()
        row=0
        col=0
        roiPSLabel=QLabel('ROI point-size')
        self.imageLayout.addWidget(roiPSLabel,row=row,col=col)
        col+=1
        self.roiPSLineEdit=QLineEdit('5')
        self.roiPSLineEdit.returnPressed.connect(self.updateROI)
        self.imageLayout.addWidget(self.roiPSLineEdit,row=row,col=col)
        col+=1
        roiLWLabel=QLabel('ROI line-width')
        self.imageLayout.addWidget(roiLWLabel,row=row,col=col)
        col+=1
        self.roiLWLineEdit=QLineEdit('2')
        self.roiLWLineEdit.returnPressed.connect(self.updateROI)
        self.imageLayout.addWidget(self.roiLWLineEdit,row=row,col=col)
        col+=1
        roiColorLabel=QLabel('ROI color')
        self.imageLayout.addWidget(roiColorLabel,row=row,col=col)
        col+=1
        self.roiColorButton=pg.ColorButton()
        self.roiColorButton.sigColorChanging.connect(self.updateROI)
        self.roiColorButton.sigColorChanged.connect(self.updateROI)
        self.imageLayout.addWidget(self.roiColorButton,row=row,col=col)
        
        row+=1
        col=0
        self.imageWidget=Image_Widget(self.imageData)
        self.imageLayout.addWidget(self.imageWidget,row=row,col=col,colspan=6)
        self.pg_axis=self.imageWidget.imageView.getView()
        self.pg_image=self.imageWidget.imageView.getImageItem()
        
        self.imageDock.addWidget(self.imageLayout)
        
    def create_maskControlDock(self):
        self.maskControlLayout=pg.LayoutWidget()
        row=0
        col=0
        self.openShapesPushButton=QPushButton('Open Shape File')
        self.maskControlLayout.addWidget(self.openShapesPushButton,row=row,col=col)
        col=1
        self.saveShapesPushButton=QPushButton('Save Shape File')
        self.maskControlLayout.addWidget(self.saveShapesPushButton,row=row,col=col)
        
        row=1
        col=0
        self.shape_ListWidget=QListWidget()
        self.shape_ListWidget.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.maskControlLayout.addWidget(self.shape_ListWidget,row=row,col=col,colspan=2)
        
        row=2
        col=0
        maskShapeLabel=QLabel('Mask Shape')
        self.maskControlLayout.addWidget(maskShapeLabel,row=row,col=col)
        col=1
        self.maskShapeComboBox=QComboBox()
        self.maskShapeComboBox.addItems(['upper-threshold','lower-threshold','rectangle','inverted-rectangle','ellipse','inverted-ellipse','polyline','inverted-polyline'])
        self.maskControlLayout.addWidget(self.maskShapeComboBox,row=row,col=col)
        row=3
        col=0
        self.drawShapePushButton=QPushButton('Draw Shape')
        self.maskControlLayout.addWidget(self.drawShapePushButton,row=row,col=col)
        col=1
        self.removeShapePushButton=QPushButton('Remove Shape')
        self.maskControlLayout.addWidget(self.removeShapePushButton,row=row,col=col)
        row=4
        col=0
        self.createMaskPushButton=QPushButton('Create/Update Mask')
        self.maskControlLayout.addWidget(self.createMaskPushButton,row=row,col=col)
        col=1
        self.saveMaskPushButton=QPushButton('Save Mask')
        self.maskControlLayout.addWidget(self.saveMaskPushButton,row=row,col=col)      
        self.maskControlDock.addWidget(self.maskControlLayout)       

        
        
    def draw_shape(self):
        """
        Adds a selected ROI shape in the selected image to create mask
        """
        self.masking=1
        if self.shape_ListWidget.count()==0:
            self.mask={}
            self.mask_number=0
            self.mask_val={}
            self.mask_list=[]
        centerx=self.imageData.shape[0]/2#(self.image_xmax+self.image_xmin)/2.0
        centery=self.imageData.shape[1]/2#(self.image_ymax+self.image_ymin)/2.0
        lenx=self.imageData.shape[0]#(self.image_xmax-self.image_xmin)
        leny=self.imageData.shape[1]#(self.image_ymax-self.image_ymin)
        self.roiPS=int(self.roiPSLineEdit.text())
        self.roiLW=int(self.roiLWLineEdit.text())
        self.roiPen=pg.mkPen(color=self.roiColorButton.color(),width=self.roiLW)
        if str(self.maskShapeComboBox.currentText())=='upper-threshold':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            self.mask_val[self.mask_number]=1
            self.threshold[self.mask_number],_=QInputDialog.getDouble(self,'Upper-threshold','Upper-threshld value:',value=1e6)
            txt=str(self.mask_number)+':upper-threshold: val=%.e'%(self.threshold[self.mask_number])
            self.shape_ListWidget.addItem(txt)
            item=self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list.append(txt)
        elif str(self.maskShapeComboBox.currentText())=='lower-threshold':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            self.mask_val[self.mask_number]=1
            self.threshold[self.mask_number],_=QInputDialog.getDouble(self,'Lower-threshold value','Lower-threshld value:',value=0)
            txt=str(self.mask_number)+':lower-threshold: val=%.e'%(self.threshold[self.mask_number])
            self.shape_ListWidget.addItem(txt)
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list.append(txt)
        elif str(self.maskShapeComboBox.currentText())=='rectangle':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            pos=[centerx-0.1*lenx/2.0,centery-0.1*leny/2.0]
            size=[0.1*lenx,0.1*leny]
            self.mask[self.mask_number]=pg.ROI(pos,size,pen=self.roiPen)
            self.mask_val[self.mask_number]=1
            #self.mask[self.mask_number].addRotateFreeHandle((0,0),(0.5,0.5))
            self.mask[self.mask_number].addScaleHandle((1,1),(0.0,0.0))
            txt=str(self.mask_number)+':rectangle: pos='+str(pos)+';size='+str(size)+';val='+str(self.mask_val[self.mask_number])
            self.shape_ListWidget.addItem(txt)
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list.append(txt)
        elif str(self.maskShapeComboBox.currentText())=='inverted-rectangle':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            pos=[centerx-0.1*lenx/2.0,centery-0.1*leny/2.0]
            size=[0.1*lenx,0.1*leny]
            self.mask[self.mask_number]=pg.ROI(pos,size,pen=self.roiPen)
            self.mask_val[self.mask_number]=-1
            #self.mask[self.mask_number].addRotateFreeHandle((0,0),(0.5,0.5))
            self.mask[self.mask_number].addScaleHandle((1,1),(0.0,0.0))
            txt=str(self.mask_number)+':inverted-rectangle: pos='+str(pos)+';size='+str(size)+';val='+str(self.mask_val[self.mask_number])
            self.shape_ListWidget.addItem(txt)
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list.append(txt)
        elif self.maskShapeComboBox.currentText()=='ellipse':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            pos=[centerx,centery]
            size=[0.1*lenx,0.1*leny]
            self.mask[self.mask_number]=pg.EllipseROI(pos,size,pen=self.roiPen)
            self.mask_val[self.mask_number]=1
            txt=str(self.mask_number)+':ellipse: pos='+str(pos)+';size='+str(size)+';val='+str(self.mask_val[self.mask_number])
            self.shape_ListWidget.addItem(txt)
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list.append(txt)
        elif self.maskShapeComboBox.currentText()=='inverted-ellipse':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            pos=[centerx,centery]
            size=[0.1*lenx,0.1*leny]
            self.mask[self.mask_number]=pg.EllipseROI(pos,size,pen=self.roiPen)
            self.mask_val[self.mask_number]=-1
            txt=str(self.mask_number)+':inverted-ellipse: pos='+str(pos)+';size='+str(size)+';val='+str(self.mask_val[self.mask_number])
            self.shape_ListWidget.addItem(txt)
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list.append(txt)
        elif self.maskShapeComboBox.currentText()=='polyline':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            self.pg_axis.scene().sigMouseClicked.connect(self.draw_polyline)
            self.roi_finished=False
            self.new_pos=[]
            self.mask[self.mask_number]=PolyLineROI_new(self.new_pos,closed=False,pen=self.roiPen)
            self.mask[self.mask_number].pen=self.roiPen
            self.tmpLine=PolyLineROI_new(self.new_pos,closed=False,pen=self.roiPen)
            self.tmpLine.pen=self.roiPen
            self.pg_axis.addItem(self.mask[self.mask_number])
            self.pg_axis.addItem(self.tmpLine)
            return
        elif self.maskShapeComboBox.currentText()=='inverted-polyline':
            self.mask_type[self.mask_number]=self.maskShapeComboBox.currentText()
            self.pg_axis.scene().sigMouseClicked.connect(self.draw_polyline)
            self.roi_finished=False
            self.new_pos=[]
            self.mask[self.mask_number]=PolyLineROI_new(self.new_pos,closed=False,pen=self.roiPen)
            self.tmpLine=PolyLineROI_new(self.new_pos,closed=False,pen=self.roiPen)
            self.pg_axis.addItem(self.mask[self.mask_number])
            self.pg_axis.addItem(self.tmpLine)
            return
        if str(self.maskShapeComboBox.currentText())!='lower-threshold' and str(self.maskShapeComboBox.currentText())!='upper-threshold':
            self.pg_axis.addItem(self.mask[self.mask_number])
            self.mask[self.mask_number].sigRegionChangeFinished.connect(self.update_shape)
            self.mask[self.mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
        self.mask_number=self.mask_number+1
        print(self.mask_list)
    def updateROI(self):
        """
        Updates the ROI depending upon the changes made in pointsize, linewidth and color
        """
        self.roiPS=int(self.roiPSLineEdit.text())
        self.roiLW=int(self.roiLWLineEdit.text())
        self.roiPen=pg.mkPen(color=self.roiColorButton.color(),width=self.roiLW)
        for key in self.mask.keys():
            handles=self.mask[key].getHandles()
            for h in handles:
                h.radius=self.roiPS
                h.update()
            self.mask[key].setPen(self.roiPen)
            self.mask[key].update()
        
    def draw_polyline(self,evt):
        if evt.double():
            self.pg_axis.scene().sigMouseMoved.disconnect()
            self.pg_axis.scene().sigMouseMoved.connect(self.imageWidget.image_mouseMoved)
            self.pg_axis.removeItem(self.tmpLine)
            del self.tmpLine
            self.mask[self.mask_number].clearPoints()
            self.mask[self.mask_number].setPoints(self.new_pos[:-2],closed=True)
            self.roi_finished=True
            self.pg_axis.scene().sigMouseClicked.disconnect()
            if self.maskShapeComboBox.currentText()=='polyline':
                self.mask_val[self.mask_number]=1
            else:
                self.mask_val[self.mask_number]=-1
            self.shape_ListWidget.addItem(str(self.mask_number)+':polyline: pos='+str(self.new_pos[:-1])+';val='+str(self.mask_val[self.mask_number]))
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.mask_list[self.mask_number]=item.text()
            self.pg_axis.addItem(self.mask[self.mask_number])
            self.mask[self.mask_number].sigRegionChangeFinished.connect(self.update_shape)
            self.mask[self.mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
            self.mask_number=self.mask_number+1
        else:
            pos=self.pg_image.mapFromScene(evt.scenePos())
            self.pg_axis.scene().sigMouseMoved.connect(self.update_polyline)
            if len(self.new_pos)>1:
                del self.new_pos[-1]
            self.new_pos.append([pos.x(),pos.y()])
            self.mask[self.mask_number].clearPoints()
            self.tmpLine.clearPoints()
            self.mask[self.mask_number].setPoints(self.new_pos,closed=False)
            self.new_pos.append([pos.x(),pos.y()])
            self.tmpLine.setPoints(self.new_pos[-2:])
            
                
            
    def update_polyline(self,evt):
        point=evt
        if self.pg_image.sceneBoundingRect().contains(point):
            pos=self.pg_image.mapFromScene(point)
            self.new_pos[-1]=[pos.x(),pos.y()]
            self.tmpLine.clearPoints()
            self.tmpLine.setPoints(self.new_pos[-2:])
        
            
        
    def remove_shape(self):
        """
        Removes the selected shapes from shape_ListWidget
        """
        for item in self.shape_ListWidget.selectedItems():
            mask_number=int(str(item.text()).split(':')[0])
            if self.mask_type[mask_number]!='upper-threshold' and self.mask_type[mask_number]!='lower-threshold':
                self.pg_axis.removeItem(self.mask[mask_number])
            row=self.shape_ListWidget.row(item)
            self.shape_ListWidget.takeItem(row)
            if mask_number in self.mask_data:
                del self.mask_data[mask_number]
            if mask_number in self.mask_val:
                del self.mask_val[mask_number]
            if mask_number in self.mask:
                del self.mask[mask_number]
            del self.mask_type[mask_number]
            self.mask_list.pop(mask_number)
        if self.shape_ListWidget.count()>0:           
            self.create_all_masks()
        else:
            self.imageWidget.imageLogLinear()
        
        
    def create_mask(self,mask_number):
        """
        Creates the mask as per the ROI drawn
        """
        self.masking=1
        self.mask_data[mask_number]=np.zeros_like(self.imageData)
        if self.mask_type[mask_number]=='upper-threshold':
            self.mask_data[mask_number]=np.where(self.imageData>self.threshold[mask_number],self.mask_val[mask_number],0)
        elif self.mask_type[mask_number]=='lower-threshold':
            self.mask_data[mask_number]=np.where(self.imageData<self.threshold[mask_number],self.mask_val[mask_number],0)
        else:
            cols,rows=self.imageData.shape
            m=np.mgrid[:cols,:rows]
            possx=m[0,:,:]
            possy=m[1,:,:]
            possx.shape=cols,rows
            possy.shape=cols,rows
            mpossx=self.mask[mask_number].getArrayRegion(possx,self.pg_image)
            mpossx=mpossx[np.nonzero(mpossx)].astype('int')
            mpossy=self.mask[mask_number].getArrayRegion(possy,self.pg_image)
            mpossy=mpossy[np.nonzero(mpossy)].astype('int')
            self.mask_data[mask_number][mpossx,mpossy]=self.mask_val[mask_number]
            #print(np.sum(self.mask_data[mask_number]))
            if self.mask_val[mask_number]<0:
                self.mask_data[mask_number]=1+self.mask_data[mask_number]
  
    def create_all_masks(self):
        """
        Creates the maskes for all the shapes
        """
        self.masking=1
        self.full_mask_data=np.zeros_like(self.tmp_data)
        tmp=copy.copy(self.imageData)
        ##Masking the edge of the image##
        if self.shape_ListWidget.count()>0:
            self.full_mask_data[0,:]=1
            self.full_mask_data[-1,:]=1
            self.full_mask_data[:,0]=1
            self.full_mask_data[:,-1]=1
        for key in self.mask_type.keys():
            self.create_mask(key)
            self.full_mask_data=np.logical_or(self.full_mask_data,self.mask_data[key])
        self.full_mask_data=-1*self.full_mask_data
        self.imageData=(self.full_mask_data+1)*self.imageData
        self.imageWidget.imageData=self.imageData
        self.imageWidget.imageLogLinear()
        self.imageData=copy.copy(tmp)

    def shape_changed(self,currentItemText):
        s_line = currentItemText.strip().split(':')
        mask_number = int(s_line[0])
        print(mask_number, self.shape_ListWidget.currentRow())
        if mask_number != self.shape_ListWidget.currentRow():
            QMessageBox.warning(self, 'Change not allowed', 'The change of mask number is not allowed')
            item.setText(self.mask_list[mask_number])
            return
        mask_type = s_line[1]
        print(mask_type, self.mask_list[mask_number])
        if mask_type!=self.mask_list[mask_number].split(':')[1]:
            QMessageBox.warning(self, 'Change not allowed', 'The change of mask type is not allowed')
            item.setText(self.mask_list[mask_number])
            return
        self.mask_type[mask_number] = mask_type
        if mask_type == 'upper-threshold':
            val = eval(s_line[2].split('=')[1])
            self.mask_val[mask_number] = 1
            self.threshold[mask_number] = val
        elif mask_type == 'lower-threshold':
            val = eval(s_line[2].split('=')[1])
            self.mask_val[mask_number] = 1
            self.threshold[mask_number] = val
        elif (mask_type == 'rectangle') or (mask_type == 'inverted-rectangle'):
            size_pos = s_line[2].split(';')
            pos = eval(size_pos[0].split('=')[1])
            size = eval(size_pos[1].split('=')[1])
            val = eval(size_pos[2].split('=')[1])
            self.mask[mask_number].setPos(pos)
            self.mask[mask_number].setSize(size)
            self.mask_val[mask_number] = val
            print(pos, self.mask[mask_number].pos())
            # self.mask[self.mask_number].addRotateFreeHandle((0,0),(0.5,0.5))
            #self.mask[mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
        elif (mask_type == 'ellipse') or (mask_type == 'inverted-ellipse'):
            size_pos = s_line[2].split(';')
            pos = eval(size_pos[0].split('=')[1])
            size = eval(size_pos[1].split('=')[1])
            val = eval(size_pos[2].split('=')[1])
            self.mask[mask_number].setPos(pos)
            self.mask[mask_number].setSize(size)
            self.mask_val[mask_number] = val
            #self.mask[mask_number].sigRegionChangeFinished.connect(self.update_shape)
            #self.mask[mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
        else:
            pos_val = s_line[2].split(';')
            pos = eval(pos_val[0].split('=')[1])
            val = eval(pos_val[1].split('=')[1])
            self.mask[self.mask_number].setPoints(pos)
            self.mask_val[self.mask_number] = val
            # self.mask[self.mask_number].sigRegionChangeFinished.connect(self.update_shape)
            # self.mask[self.mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
            # self.pg_axis.addItem(self.mask[self.mask_number])
        
    def update_shape(self,mask):
        """
        Updates the shape of the mask when the change in the ROI is finished
        """
        self.masking=1
        pos=mask.pos()
        size=mask.size()
        handles=mask.getHandles()
        handles=[[mask.mapToItem(self.pg_image, h.pos()).x(), mask.mapToItem(self.pg_image, h.pos()).y()] for h in handles]
        for key, val in self.mask.items():
            if mask==self.mask[key]:
                mask_number=key
        for i in range(self.shape_ListWidget.count()):
            if int(str(self.shape_ListWidget.item(i).text()).split(':')[0])==mask_number:
                item_number=i
                break
        oldval=str(self.shape_ListWidget.item(item_number).text())
        shape_name=oldval.split(':')[1]
        if (shape_name=='rectangle') or (shape_name=='inverted-rectangle') or (shape_name=='ellipse') or (shape_name=='inverted-ellipse'):
            txt=str(mask_number)+':'+shape_name+': pos='+str([pos.x(),pos.y()])+';size='+str([size.x(),size.y()])+';val='+str(self.mask_val[mask_number])
            self.shape_ListWidget.item(item_number).setText(txt)
            self.mask_list[item_number]=txt
        else:
            txt=str(mask_number)+':'+shape_name+': pos='+str(handles)+';val='+str(self.mask_val[mask_number])
            self.shape_ListWidget.item(item_number).setText(txt)
            self.mask_list[item_number] = txt
        #self.create_all_masks()
        
    def move_shape(self,mask):
        """
        Resets the mask under the shape while start moving the shape
        """
        self.masking=1
        for key, val in self.mask.items():
            if mask==self.mask[key]:
                mask_number=key
        self.full_mask_data=np.zeros_like(self.tmp_data)
        tmp=copy.copy(self.imageData)
        for key in self.mask.keys():
            val=copy.copy(self.mask_val[key])
            if key==mask_number:
                self.mask_val[key]=0
                self.create_mask(key)
            else:
                self.create_mask(key)
            self.mask_val[key]=copy.copy(val)
            self.full_mask_data=np.logical_or(self.full_mask_data,self.mask_data[key])
        self.full_mask_data=-1*self.full_mask_data
        self.imageData=(self.full_mask_data+1)*self.imageData
        self.imageWidget.imageData=self.imageData
        self.imageWidget.imageLogLinear()
        self.imageData=tmp
        
        
    def save_shape_file(self):
        """
        Saves the shape file
        """
        self.masking=1
        fname=QFileDialog.getSaveFileName(filter='Shape Files (*.shp)')[0]
        #print(fname)
        fh=open(str(fname),'w')
        for i in range(self.shape_ListWidget.count()):
            fh.write(str(self.shape_ListWidget.item(i).text())+'\n')
        fh.close()
        
    def open_shape_file(self):
        """
        Opens the shape file
        """
        self.masking=1
        self.shape_ListWidget.clear()
        fname=QFileDialog.getOpenFileName(filter='Shape Files (*.shp)')[0]
        fh=open(fname,'r')
        lines=fh.readlines()
        #self.shape_ListWidget.addItems(lines)
        self.mask_list=[]
        for line in lines:
            self.shape_ListWidget.addItem(line.strip())
            self.mask_list.append(line.strip)
            item = self.shape_ListWidget.item(self.shape_ListWidget.count()-1)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            s_line=line.strip().split(':')
            self.mask_number=int(s_line[0])
            mask_type=s_line[1]
            self.mask_type[self.mask_number]=mask_type
            if mask_type=='upper-threshold':
                val=eval(s_line[2].split('=')[1])
                self.mask_val[self.mask_number]=1
                self.threshold[self.mask_number]=val
                self.mask_number+=1
            elif mask_type=='lower-threshold':
                val=eval(s_line[2].split('=')[1])
                self.mask_val[self.mask_number]=1
                self.threshold[self.mask_number]=val
                self.mask_number+=1
            elif (mask_type=='rectangle') or (mask_type=='inverted-rectangle'):
                size_pos=s_line[2].split(';')
                pos=eval(size_pos[0].split('=')[1])
                size=eval(size_pos[1].split('=')[1])
                val=eval(size_pos[2].split('=')[1])
                self.mask[self.mask_number]=pg.ROI(pos,size)
                self.mask_val[self.mask_number]=val
                #self.mask[self.mask_number].addRotateFreeHandle((0,0),(0.5,0.5))
                self.mask[self.mask_number].addScaleHandle((1,1),(0,0))
                self.mask[self.mask_number].sigRegionChangeFinished.connect(self.update_shape)
                self.mask[self.mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
                self.pg_axis.addItem(self.mask[self.mask_number])
            elif (mask_type=='ellipse') or (mask_type=='inverted-ellipse'):
                size_pos=s_line[2].split(';')
                pos=eval(size_pos[0].split('=')[1])
                size=eval(size_pos[1].split('=')[1])
                val=eval(size_pos[2].split('=')[1])
                self.mask[self.mask_number]=pg.EllipseROI(pos,size)
                self.mask_val[self.mask_number]=val
                self.mask[self.mask_number].sigRegionChangeFinished.connect(self.update_shape)
                self.mask[self.mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
                self.pg_axis.addItem(self.mask[self.mask_number])
            else:
                pos_val=s_line[2].split(';')
                pos=eval(pos_val[0].split('=')[1])
                val=eval(pos_val[1].split('=')[1])
                self.mask[self.mask_number]=PolyLineROI_new(pos,closed=True)
                self.mask_val[self.mask_number]=val
                self.mask[self.mask_number].sigRegionChangeFinished.connect(self.update_shape)
                self.mask[self.mask_number].sigHoverEvent.connect(self.shape_selected_in_image)
                self.pg_axis.addItem(self.mask[self.mask_number])
            #self.mask[self.mask_number].sigRegionChangeStarted.connect(self.move_shape)
        self.mask_number=self.mask_number+1
        
        #self.create_all_masks()
        
        
    def hide_shapes(self):
        """
        Hide or show the shapes of the masks to edit
        """
        self.masking=1
        if self.hide_shapes_CheckBox.checkState()>0:
            for mask_number in self.mask.keys():
                if self.mask_type!='upper_threshold' and self.mask_type!='lower_threshold':
                    self.mask[mask_number].hide()
        else:
            for mask_number in self.mask.keys():
                if self.mask_type!='upper_threshold' and self.mask_type!='lower_threshold':
                    self.mask[mask_number].show()
                
    def save_mask(self):
        """
        Saves the entire mask combining all the shape ROIs
        """
        fname=str(QFileDialog.getSaveFileName(filter='Mask Files (*.msk)')[0])
        name,extn=os.path.splitext(fname)
        if extn=='':
            fname=name+'.msk'
        elif extn!='.msk':
            QMessageBox.warning(self,'File extension error','Please donot provide file extension other than ".msk". Thank you!')
            return
        else:
            tmpfile=fb.edfimage.EdfImage(data=self.full_mask_data.T,header=None)
            tmpfile.save(fname)
            self.mask_file=fname
        
    def shape_selected_in_image(self,mask):
        """
        Selects the shape_ListItem corresponding to the clicked ROI on the image
        """
        self.masking=1
        for i in range(self.shape_ListWidget.count()):
            self.shape_ListWidget.item(i).setSelected(False)
        for key, val in self.mask.items():
            if mask==self.mask[key]:
                mask_number=key
        for i in range(self.shape_ListWidget.count()):
            num=int(self.shape_ListWidget.item(i).text().split(':')[0])
            if num==mask_number:
                self.shape_ListWidget.item(i).setSelected(True)
                self.shape_ListWidget.setCurrentRow(i)
                break
                
                
if __name__=='__main__':
    # create application
    app = QApplication(sys.argv)
    app.setApplicationName('Mask Widget')
    # create widget
    img=fb.open(sys.argv[1]).data
    w = MaskWidget(img)
    w.setWindowState(Qt.WindowMaximized)
    w.setWindowTitle('Mask Widget')
    w.show()

    # execute applicatio
    sys.exit(app.exec_())