#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Abinit Post Process Application
author: Martin Alexandre
last edited: May 2013
"""

import os
import sys
import time
import string
import commands
from scipy.constants import physical_constants as pc
from scipy.io import netcdf
import numpy as np


#Utility
import utility.analysis as Analysis

try:
    from PyQt4 import QtGui,QtCore
except :
    pass;

class MolecularDynamicFile:

  Bohr_Ang = pc['Bohr radius'][0]
  Ha_eV = pc['Hartree energy in eV'][0]         # Conversion factor 1 Hartree = 27,2113845 eV
  kb_eVK = pc['Boltzmann constant in eV/K'][0]   # Boltzman constant in eV/K  = (1.380658e-23)/(1.60217733e-19) #eV/K
  amu_emass = pc['atomic mass constant'][0]/pc['electron mass'][0] # 1 atomic mass unit, in electronic mass
  fact = pc['electron volt-joule relationship'][0]*Ha_eV/(Bohr_Ang**3*(10**9)) # Conversion factor hartree/bohr^3 to GPa
  namefile1 = ""
  namefile2 = ""
  ni = 0
  nf = 0
  Nbtime = 0
  goodFile= False
  type_of_file = ""


#-----------------------------#
#-------CONSTRUCTOR-----------#
#-----------------------------#

  def __init__(self, pnamefile):
      # Take the last HIST/OUT.nc file in the directory (when APPA is launch)
      if pnamefile == "":
          OUT_list = []
          filesdir = os.listdir(os.getcwd())
          for files in filesdir :
              if os.path.isfile(files):
                  stats = os.stat(files)
                  fic_tuple = time.localtime(stats[8]), files
                  lili = string.split(files, '.')
#                  if files.find('_OUT.nc') == len(files)-7 and len(files)>7 :
#                      OUT_list.append(fic_tuple)
                  if files.find('HIST.nc') == len(files)-7 and len(files)>7 :
                      OUT_list.append(fic_tuple)
                  if files.find('HIST.nc') == len(files)-7 and len(files)>7 :
                      OUT_list.append(fic_tuple)
              if len(OUT_list) > 0 :
                  OUT_list.sort() ; OUT_list.reverse()
                  fic_HIST=OUT_list[0][1].replace('_OUT.nc','_HIST')
                  fic_HIST=OUT_list[0][1]
                  if os.path.exists(fic_HIST) :
                      self.namefile1 = fic_HIST
                      self.namefile2 = fic_HIST
#                      self.namefile2 = fic_HIST.replace('_HIST','_OUT.nc')
                      self.type_of_file = 'netcdf'
      # or the file in parameter :
      else:
          if str(pnamefile).find('_OUT.nc') != -1:  
              self.namefile2 = str(pnamefile)
              self.namefile1 = str(pnamefile).replace('_OUT.nc','_HIST')              
              self.type_of_file = 'netcdf'
          elif str(pnamefile).find('HIST.nc') != -1 :
              self.namefile1 = str(pnamefile)
              if(os.path.exists(self.namefile1.replace('HIST.nc','OUT.nc'))):
                  self.namefile2 = str(pnamefile).replace('HIST.nc','OUT.nc')
              else:
                  self.namefile2 = str(pnamefile)
              self.type_of_file = 'netcdf'

              self.namefile1 = str(pnamefile)
              self.type_of_file = 'netcdf'
          elif str(pnamefile).find('HIST') != -1 :
              self.namefile1 = str(pnamefile)
              if(os.path.exists(self.namefile1.replace('HIST','OUT.nc'))):
                  self.namefile2 = str(pnamefile).replace('HIST','OUT.nc')
              else:
                  self.namefile2 = str(pnamefile)
              self.type_of_file = 'netcdf'
          else:
              self.type_of_file = 'ASCII_output'
              self.namefile2 = str(pnamefile)

                
      if (self.type_of_file == 'ASCII_output'):
          self.read_ascii()
            
      if (self.type_of_file == 'netcdf'):
          self.read_netcdf()


#-----------------------------#
#--------METHODS--------------#
#-----------------------------#
  def read_ascii(self):

      # Load file
      message = "Unable to load {0} ".format(self.namefile2)
      #try:
      lines = open(os.path.join(os.getcwd(),self.namefile2),'r').read().split('\n')[:-1]
      #except:
      #    sys.exit(0)	

      #Read the number of image:
      message = "Unable to read the number of image "
      try:
          ans = filter(lambda line: "nimage =" in line ,lines)
          #temp = commands.getoutput('grep \"nimage =\" ' + self.namefile2 + '  | awk \'{print $3}\'')
          self.n_image = int(ans)
      except:
          self.n_image = 1

      # reading potential energy:
      message = "Unable to read potential energy "
      if self.n_image == 1 :
          ans = filter(lambda line: "Total energy (etotal) [Ha]" in line ,lines)
      else:
          ans = filter(lambda line: "Potential energy" in line ,lines)
      
      self.E_pot = np.array(map(lambda line: line.split()[-1] ,ans), dtype=np.float64)
      
      self.ni = 1 #Set the initial step to 1
      self.nf = len(self.E_pot)
      self.Nbtime = len(self.E_pot)
            
      #Reading the number of atom
      message = "Unable to read the number of atoms"
      ans = filter(lambda line: "natom  " in line ,lines).pop().split()[-1]
      self.natom = int(ans)

      #Reading acell:
      message = "Unable to read acell"
      ans = map(lambda line: line.split()[1:4], filter(lambda line: "acell " in line ,lines))
      self.acell = np.array(ans, dtype=np.float64)

      #Reading the primitive vectors:
      message = "Unable to read the primitive vectors"

      index = filter(lambda i:  'Real(R)+Recip(G)' in lines[i] , np.arange(len(lines))).pop()
      rprim = np.array(map(lambda line: np.array(line.split()[1:4], dtype = np.float64) ,lines[index+1:index+4]))

      if index:
	  self.rprimd = np.array([[rprim,]*self.Nbtime])
      else:
          self.rprimd = np.reshape(np.array(temp.split()[0:self.n_image*self.Nbtime*9],dtype=np.float64), (self.Nbtime,self.n_image,3,3))
          self.rprimd[:,:,0,:] = self.rprimd[:,:,0,:] * self.acell[0,:]
          self.rprimd[:,:,1,:] = self.rprimd[:,:,1,:] * self.acell[1,:]
          self.rprimd[:,:,2,:] = self.rprimd[:,:,2,:] * self.acell[2,:]

      #Reading velocity of particules:
      message = "Unable to read the velocity of particules"
      index = filter(lambda i:  'Cartesian velocities' in lines[i] , np.arange(len(lines)))

      if index:
	  self.vel = map(lambda ind: lines[ind+1:ind+self.natom+1] ,index)
          self.vel = np.reshape( np.array( map(lambda v: map(lambda line: np.float64(line.split()) ,v) ,self.vel)),(self.Nbtime,self.n_image,self.natom,3) )
      else:
	  self.vel = None

      #Reading position of particules (Cartesian):
      message = "Unable to read the position of particules (cart)"
      index = filter(lambda i:  'Cartesian coordinates' in lines[i] , np.arange(len(lines)))

      if index:
	  self.xcart = map(lambda ind: lines[ind+1:ind+self.natom+1] ,index)
          self.xcart = np.reshape( np.array( map(lambda xcart: map(lambda line: np.float64(line.split()) ,xcart) ,self.xcart)),(self.Nbtime,self.n_image,self.natom,3) )
      else:
	  self.xcart = None

      #Reading position of particules (Reduced):
      message = "Unable to read the position of particules (red)"
      index = filter(lambda i:  'Reduced coordinates' in lines[i] , np.arange(len(lines)))

      if index:
	  self.xred = map(lambda ind: lines[ind+1:ind+self.natom+1] ,index)
          self.xred = np.reshape( np.array( map(lambda red:  map(lambda line: np.float64(line.split()), red) ,self.xred)),(self.Nbtime,self.n_image,self.natom,3) )
      else:
	  self.xred = None

      #Reading stress of particules:
      message = "Unable to read stress of particules"
      index = filter(lambda i:  'Cartesian components of stress' in lines[i], np.arange(len(lines)))

      if index:
	  self.stress = map(lambda ind: lines[ind+1:ind+1+3] ,index)
          self.stress = np.array( map(lambda stress:  map(lambda line: np.array(line.split())[2::3], stress) ,self.stress))
          self.stress = np.float64(np.reshape( self.stress[:self.Nbtime], (self.Nbtime,self.n_image,6) ))
      else:
	  self.stress = None
 
      """
      self.temp = self.stress.copy()
      s = (self.Nbtime,self.n_image,6)
      self.stress = np.zeros(s)
      nb = len(self.temp) / 6
      ni = self.Nbtime - nb
      
      self.stress[ni:]    = self.temp    
      self.stress[ni:,:,1]= self.temp[:,:,2]
      self.stress[ni:,:,2]= self.temp[:,:,4]
      self.stress[ni:,:,3]= self.temp[:,:,1]
      self.stress[ni:,:,4]= self.temp[:,:,3]
      del self.temp
     
      print self.stress
      """ 

      #Reading the type of particules:
      message = "Unable to read the type of particules"
      index = filter(lambda i:  ' typat ' in lines[i], np.arange(len(lines)))
      self.typat = np.float64((' '.join(map(lambda ind: lines[ind:ind+1+int(self.natom/20)] ,index).pop())).split()[1:])

      #Reading mass of particules:
      message = "Unable to read the mass of particules"
      index = filter(lambda i:  'amu' in lines[i], np.arange(len(lines)))
      self.amu = np.float64(' '.join(map(lambda ind: lines[ind:ind+int(max(self.typat))] ,index).pop()).split()[1:])

      #Reading znucl :
      message = "Unable to read znucl"
      index = filter(lambda i:  'znucl' in lines[i], np.arange(len(lines)))
      self.znucl = np.float64(map(lambda ind: lines[ind] ,index).pop().split()[1:])

      #Reading dtion:
      try:
          #try to read dtion :
          index = filter(lambda i:  'dtion' in lines[i], np.arange(len(lines)))
          self.dtion = np.float64(map(lambda ind: lines[ind] ,index).pop().split()[1:])
      except:
          #If dtion doesn't exist, it's set to 100 (default value)
          self.dtion = 100
      
      self.goodFile = True

      #-----------Calculation of some quantities------------#
      #-----------not available in the output File----------# 
      self.mass_calculation()
      self.volume_calculation()
      self.angles_calculation()
      self.E_kinCalculation()
      self.temperature_calculation()
      self.pressure_calculation()
      #-----------------------------------------------------#

      #-----------------------------------------------------#

#      except:    
#          self.goodFile = False
#          print "Error, " +message+ ", please use netcdf file "
#          try:
#              QtGui.QMessageBox.critical(None,"Warning","Error, " +message+ ", please use netcdf file ")#
#          except :
#              pass;
        
 
  def read_netcdf(self):
    #Check the version of scipy for the netcdf library
      module = __import__('scipy')
      if float(module.__version__.split('.')[1]) >= 9:
          module = "data"
      else:
          module = "__array_data__"


      #if 1==1:
      try :
          #Set the two netcdf_file variable with the HOST and ncfile:
          self.hist_file = netcdf.netcdf_file(str(self.namefile1), 'r')
          self.nc_file   = netcdf.netcdf_file(str(self.namefile2), 'r')

          #---------------READING DATA----------------------#
          self.ni = 1 #Set the initial step to 1
          temp = getattr(self.hist_file.variables['etotal'],module).shape[0]
          self.nf = temp 
          self.Nbtime = temp
          
          #Set the number of image (only 1 for netcdf)
          self.n_image = 1

          #Reading the number of atom
          self.natom = self.hist_file.dimensions['natom']

          #Reading the primitive vectors:
          self.rprimd = np.reshape(getattr(self.hist_file.variables['rprimd'],module),(self.Nbtime,self.n_image,3,3))

          #Reading acell:
          self.acell = np.reshape(getattr(self.hist_file.variables['acell'],module),(self.Nbtime,self.n_image,3))
          
          #Reading stress of particules:
          self.stress = np.reshape(getattr(self.hist_file.variables['strten'],module),(self.Nbtime,self.n_image,6))

          #Reading the type of particules:
          self.typat = getattr(self.nc_file.variables['typat'],module)
          
          #Reading mass of particules:
          self.amu = getattr(self.nc_file.variables['amu'],module)
          
          #Reading potential energy:
          self.E_pot = getattr(self.hist_file.variables['etotal'],module)

          #Reading potential energy:
          self.E_kin_ion = getattr(self.hist_file.variables['ekin'],module)

          #Reading potential energy:
          self.mdtime = getattr(self.hist_file.variables['mdtime'],module)
            
          #Reading position of particules:
          self.xcart = np.reshape(getattr(self.hist_file.variables['xcart'],module),(self.Nbtime,self.n_image,self.natom,3))
          self.xred = np.reshape(getattr(self.hist_file.variables['xred'] ,module),(self.Nbtime,self.n_image,self.natom,3))

          #Reading forces of particules:
          self.fcart = np.reshape(getattr(self.hist_file.variables['fcart'],module),(self.Nbtime,self.n_image,self.natom,3))
          self.fred  = np.reshape(getattr(self.hist_file.variables['fred'] ,module),(self.Nbtime,self.n_image,self.natom,3))
          
          #Reading velocity of particules:
          self.vel = np.reshape(getattr(self.hist_file.variables['vel'],module),(self.Nbtime,self.n_image,self.natom,3))
          
          #Reading dtion:
          try:
              #try to read dtion :
              self.dtion = getattr(self.nc_file.variables['dtion'],module)
          except:
              # If dtion doesn't exist, it's set to default abinit value => 100 :
              self.dtion = 100

          #Reading znucl of particules:
          self.znucl = getattr(self.nc_file.variables['znucl'],module)            
          #----------------------------------------------------
          self.goodFile = True
          
          #-----------Calculation of some quantities------------#
          #-----------not available in the output File----------# 
          self.mass_calculation()
          self.volume_calculation()
          self.angles_calculation()
          self.E_kinCalculation()
          self.temperature_calculation()
          self.pressure_calculation()
          #-----------------------------------------------------#

      except:
          self.goodFile = False
          print "Error,unable to read this netcdf file "

  def E_kinCalculation(self):
      natom = self.getNatom() 
      mass  = self.getMass()
      vel   = self.getVel()
      self.E_kin= np.zeros(self.Nbtime-1)
      self.E_kin[:] = np.sum((vel[:,:,0]**2+vel[:,:,1]**2+vel[:,:,2]**2)[:,:] * mass[:] * 0.5,axis=1)

  def mass_calculation(self):
      self.mass=[]
      typat = self.getTypat()
      amu = self.getAmu()
      for typ in typat:
          self.mass.extend([self.amu_emass*amu[int(typ-1)]])

  def temperature_calculation(self):
      Nbstep = self.getNbStep()-1
      E_kin = self.getE_kin()
      self.temperature = np.zeros(Nbstep)
      for itim in range(Nbstep):
          self.temperature[itim] = 2.*E_kin[itim]*self.Ha_eV/(3.*self.kb_eVK*self.getNatom())

  def pressure_calculation(self):          
      Nbstep  = self.getNbStep()-1
      TEMPER  = self.getTemp()
      Vol     = self.getVol()
      Stress  = self.getStress()
      natom   = self.getNatom()
      
      self.pressure= np.zeros(Nbstep)
      for itim in range(Nbstep):
          Pionique = (natom/Vol[itim])*self.kb_eVK*TEMPER[itim] * self.fact /self.Ha_eV
          PP=-(Stress[itim][0]+Stress[itim][1]+Stress[itim][2])/3. + Pionique
          self.pressure[itim] = PP
  
  def volume_calculation(self):
      Nbstep = self.getNbStep()
      rprim  = self.getRPrim()

      self.volume =  np.zeros(Nbstep)
      self.volume[:] = rprim[:,0,0]*(rprim[:,1,1]*rprim[:,2,2]-rprim[:,1,2]*rprim[:,2,1]) \
          +  rprim[:,0,1]*(rprim[:,1,2]*rprim[:,2,0]-rprim[:,1,0]*rprim[:,2,2]) \
          +  rprim[:,0,2]*(rprim[:,1,0]*rprim[:,2,1]-rprim[:,1,1]*rprim[:,2,0])

  def angles_calculation(self):
      Nbstep = self.getNbStep()
      rprim  = self.getRPrim() 
      self.angles = np.zeros((Nbstep,3))
      self.angles[:,0] = (np.arccos((rprim[:,0,0]*rprim[:,1,0]+rprim[:,0,1]*rprim[:,1,1]+rprim[:,0,2]*rprim[:,1,2])\
                          /np.sqrt((rprim[:,0,0]**2+rprim[:,0,1]**2+rprim[:,0,2]**2)*(rprim[:,1,0]**2+rprim[:,1,1]**2+rprim[:,1,2]**2))))
      self.angles[:,1]  = (np.arccos((rprim[:,0,0]*rprim[:,2,0]+rprim[:,0,1]*rprim[:,2,1]+rprim[:,0,2]*rprim[:,2,2])\
                          /np.sqrt((rprim[:,0,0]**2+rprim[:,0,1]**2+rprim[:,0,2]**2)*(rprim[:,2,0]**2+rprim[:,2,1]**2+rprim[:,2,2]**2))))
      self.angles[:,2] = (np.arccos((rprim[:,2,0]*rprim[:,1,0]+rprim[:,2,1]*rprim[:,1,1]+rprim[:,2,2]*rprim[:,1,2])\
                          /np.sqrt((rprim[:,2,0]**2+rprim[:,2,1]**2+rprim[:,2,2]**2)*(rprim[:,1,0]**2+rprim[:,1,1]**2+rprim[:,1,2]**2))))
      

#-----------------------------#
#-------ACCESSOR--------------#
#-----------------------------#

  def isGoodFile(self):
      # return Boolean True/False according to the HIST and NC file:
      return self.goodFile

  def getNameFile(self,fullpath=False):
      # return string with the name of the file
      if self.goodFile:
          if fullpath :
              return self.namefile2
          else:
              name = self.namefile2.split('/')
              return name[len(name)-1]
      else:
          return 0
        
  def getNatom(self):
      # return integer with the number of atom
      if self.goodFile:
          return self.natom
      else:
          return 0
        
  def getVol(self):
      # return double with the value of the volume (in bohr^3)
      if self.goodFile:
          return self.volume[self.ni:self.nf]    # Temporarily. (ni-1) for start slicing at 0
      else:
          return 0

  def getTypat(self):
      # return 1D array with the type of particules
      if self.goodFile:
          return self.typat
      else:
          return 0

  def getNTypat(self):
      # return the number of type of particules
      if self.goodFile:
          return np.max(self.typat)
      else:
          return 0
      
  def getAmu(self):
      # return 1D array with the atomic mass
      if self.goodFile:
          return self.amu
      else:
          return 0

  def getZnucl(self):
      # return 1D array with the number atomic of all the atoms
      if self.goodFile:
          return self.znucl
      else:
          return 0

  def getMass(self):
      # return 1D array with the mass of all particules
      if self.goodFile:
          return self.mass
      else:
          return 0

  def getNbTime(self):
      # return integer with the number of step in the simulation
      if self.goodFile :
          return self.Nbtime
      else:
          return 0

  def getNImage(self):
      # return integer with the number of image in the simulation
      if self.goodFile :
          return self.n_image
      else:
          return 0

  def getRPrim(self,image = 1):
      # return the primitive vector (Borh)
      if self.goodFile :
          return self.rprimd[self.ni-1:self.nf,image-1]
      else:
          return 0

  def getNbStep(self):
      # return the number of step between ni and nf
      if self.goodFile:
          return self.nf-self.ni+1
      else:
          return 0

  def getDtion(self):
      # return ion time steps in atomic units of time
      if self.goodFile:
          return self.dtion
      else:
          return 0

  def getVel(self,image = 1):
      # return 3D array with the velocity (vx,vy,z) for all particule at each time ( V[t][[at][vx,vy,vz]) for one image
      # between ni and nf
      if self.goodFile:
          if self.n_image == 1:
              return self.vel[self.ni:self.nf,image-1]   # Temporarily because vel[t=0] = 0. put (ni-1) for start slicing at 0 
          elif self.n_image != 1 :
              return self.getVelCentroid()
      else:
          return 0

  def getXCart(self,image = 1):
      # return 3D array with the position (x, y, z) for all particule at each time ( pos[t][at][x,y,z]) for one image in cartesian coordiantes
      # between ni and nf
      if self.goodFile:
          if self.n_image == 1:
              return self.xcart[self.ni:self.nf,image-1] # Temporarily because pos[t=0] = 0. put (ni-1) for start slicing at 0
          elif self.n_image != 1 :
              return self.getXCartCentroid()
      else:
          return 0

  def getXRed(self,image = 1):
      # return 3D array with the position (x, y, z) for all particule at each time ( pos[t][at][x,y,z]) for one image in reduced coordinates
      # between ni and nf
      if self.goodFile:
          if self.n_image == 1:
              return self.xred[self.ni:self.nf,image-1] # Temporarily because pos[t=0] = 0. put (ni-1) for start slicing at 0
          elif self.n_image != 1 :
              return self.getXCartCentroid(xred=True)
      else:
          return 0

  def getFCart(self,image = 1):
      # return 3D array with the forces (x, y, z) for all particule at each time ( pos[t][at][x,y,z]) for one image in cartesian coordinates
      # between ni and nf
      if self.goodFile:
          if self.n_image == 1:
              return self.fcart[self.ni:self.nf,image-1] # Temporarily because pos[t=0] = 0. put (ni-1) for start slicing at 0
          elif self.n_image != 1 :
              return self.getXCartCentroid(xred=True)
      else:
          return 0

  def getFRed(self,image = 1):
      # return 3D array with the forces (x, y, z) for all particule at each time ( f[t][at][x,y,z]) for one image in reduced coordinates
      # between ni and nf
      if self.goodFile:
          if self.n_image == 1:
              return self.fred[self.ni:self.nf,image-1] # Temporarily because pos[t=0] = 0. put (ni-1) for start slicing at 0
          elif self.n_image != 1 :
              return self.getXCartCentroid(xred=True)
      else:
          return 0

  def getVelCentroid(self):
      # return 3D array with the velocity (vx,vy,z) for all particule at each time ( V[t][[at][vx,vy,vz]) for the centroid
      # between ni and nf
      if self.goodFile:
          return np.sqrt(np.mean(self.vel[self.ni:self.nf,:]**2,axis=1))   # Temporarily because vel[t=0] = 0. put (ni-1) for start slicing at 0 
      else:
          return 0

  def getXCartCentroid(self,xred=False):
      # return 3D array with the position (x, y, z) for all particule at each time ( pos[t][at][x,y,z]) for the centroid
      # between ni and nf
      if self.goodFile:
          if(xred):
              return np.mean(self.xred[self.ni:self.nf,:],axis=1) # Temporarily because pos[t=0] = 0. put (ni-1) for start slicing at 0
          else:
              return np.mean(self.xcart[self.ni:self.nf,:],axis=1) # Temporarily because pos[t=0] = 0. put (ni-1) for start slicing at 0
      else:
          return 0


  def getE_pot(self):
      # return 1D array with the potential energy (Ha)
      if self.goodFile :
          return self.E_pot[self.ni-1:self.nf-1]   #Temporarily. put (nf) for finish slicing at 299,
      else:                                        #Skip the last step to get the same array size (see vel and pos).
          return 0
      
  def getMdtime(self):
      if self.goodFile :
          return self.mdtime[self.ni-1:self.nf-1]   #Temporarily. put (nf) for finish slicing at 299,
      else:                                        #Skip the last step to get the same array size (see vel and pos).
          return 0

  def getE_kin_ion(self):
      # return 1D array with the Energy KINetic ionic (Ha)
      if self.goodFile :
          return self.E_kin_ion[self.ni-1:self.nf-1]   #Temporarily. put (nf) for finish slicing at 299,
      else:                                        #Skip the last step to get the same array size (see vel and pos).
          return 0
        
  def getE_kin(self):
      # return 1D array with the kinetic energy (Ha)
      if self.goodFile :
          return self.E_kin[self.ni-1:self.nf-1]#Temporarily. put (nf) for finish slicing at 299,
      else:                                     #Skip the last step to get the same array size (see vel and pos).
          return 0
        
        
  def getE_Tot(self):
      # return 1D array with the total energy (Ha) between ni and nf
      if self.goodFile :
          E_kin =  self.getE_kin()
          E_pot =  self.getE_pot()
          Nbstep = self.getNbStep()
          ETOT = E_kin[0:Nbstep] + E_pot[0:Nbstep]
          return ETOT
      else:
          return 0

  def getTemp(self):
      # return 1D array with the Temperature (K)
      if self.goodFile :
          return  self.temperature[self.ni-1:self.nf-1]#Temporarily. put (nf) for finish slicing at 299,
      else:                                            #Skip the last step to get the same array size (see vel and pos).  
          return 0

  def getIonMove(self):
      if self.goodFile :
          self.ionMove = [12]
          return self.ionMove
      else:
          return 0

  def getStress(self,image = 1):
      # return 2D array with the Stess (GPa)
      if self.goodFile:
          if self.n_image==1:
               return self.stress[self.ni-1:self.nf-1,image-1] * 29421.033e0#Temporarily. put (nf) for finish slicing at 299,
          else:                                                     #Skip the last step to get the same array size (see vel and pos).
               return self.stress[self.ni-1:self.nf-1,image-1] #In PIMD, stress is already give in GPA#
      else:   

          return 0
        
  def getAcell(self,image = 1):
      if self.goodFile:
          acell = np.zeros(((self.nf-self.ni),image,3))
          for i in range(3):
              acell[:,image-1,i]=np.sqrt(self.rprimd[image-1,self.ni:self.nf,i,0]**2+\
                                         self.rprimd[image-1,self.ni:self.nf,i,1]**2+\
                                         self.rprimd[image-1,self.ni:self.nf,i,2]**2)
          return acell[:,image-1,:] # Temporarily. (ni-1) for start slicing at 0
      else:
          return 0

  def getAngles(self):
      if self.goodFile:
          return self.angles[self.ni:self.nf] * 180 / np.pi   # Temporarily. (ni-1) for start slicing at 0 
      else:
          return 0


  def getPress(self):
      # return 1D array with the Pressure between ni and nf (GPa)
      if self.goodFile :
          return self.pressure[self.ni-1:self.nf-1]
      else:
          return 0

  def getMoy(self,data):
      #return average of data
      if self.goodFile :
          nb = len(data)
          M=0.0
          for i in range(nb):
              M = M + data[i]
          M = M / nb
          return M
      else:
          return 0

  def getStandardDeviation(self,data ,averageData = 0):
      res = 0
      if averageData == 0:
          averageData = self.getMoy(data)

      for i in range(len(data)):
          res += (data[i] - averageData)**2
          
      res /= len(data)
      res = res**0.5

      return res

  def getAtomName(self):
      #return array with the name of the atom
      PTOE  = Analysis.PeriodicTableElement()
      znucl = self.getZnucl()
      name  = []
      for i in range(len(znucl)):
          name.append(PTOE.getName(znucl[i]))
      return name

  def getNi(self):
      #return ni (integer)
      return self.ni

  def getNf(self):
      #return nf (integer)
      return self.nf

  def setNi(self,pNi):
      #to set ni (integer)
      self.ni = pNi

  def setNf(self,pNf):
      #to set nf (integer)
      self.nf = pNf


#-----------------------------#
#-----------------------------#
#-----------------------------#



#######GROUND STATES OUTPUT (BETA)#############
class outputFile:
#-----------------------------#
#-------CONSTRUCTOR-----------#
#-----------------------------#
    Ha_eV = 27.2113834e0   # Conversion factor 1 Hartree = 27,2113834 eV
    def __init__(self, pnamefile):

        self.V = []
        self.P = []
        self.E = []
        self.ecut = []
        self.Nbk = []
        self.ionMove = []
        self.a = []
        self.stress = {}
        self.begin = True
        self.date = ""
        self.hour = ""
        self.name = ""
        self.goodFile = False
        self.namefile =""

	#-------READ THE LAST OUTPUT FILE OR THE CHOOSEN FILE--------#
        if pnamefile == "":
            OUT_list = []
            filesdir = os.listdir(os.getcwd())
            for files in filesdir :
                if os.path.isfile(files):
                    stats = os.stat(files)
                    fic_tuple = time.localtime(stats[8]), files
                    lili = string.split(files, '.')
                    if files.find('.out') == len(files)-4 and len(files)>4 :
                        OUT_list.append(fic_tuple)
                if len(OUT_list) > 0 :
                    OUT_list.sort() ; OUT_list.reverse()
                    fic=OUT_list[0][1]
                    if os.path.exists(fic):
                        self.namefile = fic
        else:
            self.namefile = str(pnamefile)
	#-------------------------------------------------------------#

	if self.namefile !="":

            try :
	    #if 1==1:
		self.ionMove = np.array(commands.getoutput('grep \"ionmov =\" '+ self.namefile + ' | awk \'{print $6}\'').split(), dtype=float)
		for i in range(len(self.ionMove)):
			if self.ionMove[i] == 12 :
			    return

		self.date = commands.getoutput('grep \"Starting date\" ' + self.namefile + ' | awk \'{print $4,$5,$6,$7}\'')
		self.hour = commands.getoutput('grep \"( at\" '+ self.namefile + ' | awk \'{print $4}\'')
		self.Nbk  = np.array(commands.getoutput('grep \"nkpt =\" '+ self.namefile + ' | awk \'{print $12}\'').split(), dtype=float)

		self.V = np.array(commands.getoutput('grep \"Unit cell volume ucvol\" '+ self.namefile + ' | awk \'{print $5}\'').split(), dtype=float)
		self.P = np.array(commands.getoutput('grep \"Pressure\" '+ self.namefile + ' | awk \'{print $8}\'').split(), dtype=float)
		self.E = np.array(commands.getoutput('grep \"etotal\" '+ self.namefile + '|sed /\"Total energy\"/d  | awk \'{print $2}\'').split(), dtype=float)
		self.ecut = np.array(commands.getoutput('grep \"ecut(hartree)\" '+ self.namefile + ' | awk \'{print $2}\'').split(), dtype=float)


		self.a = np.array(commands.getoutput('grep -A '+ str(len(self.E)+1)+ ' \"after computation\" '+ self.namefile+ '| sed \'/acell/!d\' | awk \'{print $2}\'').split(), dtype=float)
		self.b = np.array(commands.getoutput('grep -A '+ str(len(self.E)+1)+ ' \"after computation\" '+ self.namefile+ '| sed \'/acell/!d\' | awk \'{print $3}\'').split(), dtype=float)
		self.c = np.array(commands.getoutput('grep -A '+ str(len(self.E)+1)+ ' \"after computation\" '+ self.namefile+ '| sed \'/acell/!d\' | awk \'{print $4}\'').split(), dtype=float)

		#Reading stress of particules:
		temp = commands.getoutput(' grep -A 3  \"stress tensor (GPa)\" '+ self.namefile + '|sed \'/Car/d\' |sed \'/--/d\' | awk \'{print $4,$7}\' ')
		temp = temp.split()
		s = (len(self.E),6)
		temp2 = np.zeros(s)
		for i in range(len(self.E)):
			temp2[i] = np.array( [ temp[(6*i)+0], temp[(6*i)+2], temp[(6*i)+4], temp[(6*i)+1], temp[(6*i)+3], temp[(6*i)+5] ], dtype=float)
		self.stress = temp2

		#Reading the primitive vectors:
		temp = commands.getoutput(' grep -A 3  \"Real(R)+Recip(G)\" '+ self.namefile + '  | sed \'/space primitive vectors,/d\'|sed \'/--/d\' | awk \'{print $2,$3,$4 }\' ')
		temp = temp.split()
		s = (len(self.E),3,3)
		temp2 = np.zeros(s)
		for i in range(len(self.E)):
			a =  np.array( [temp[(9*i)+0], temp[(9*i)+1], temp[(9*i)+2]], dtype=float)
			b =  np.array( [temp[(9*i)+3], temp[(9*i)+4], temp[(9*i)+5]], dtype=float)
			c =  np.array( [temp[(9*i)+6], temp[(9*i)+7], temp[(9*i)+8]], dtype=float)
			temp2[i] = np.array( [a,b,c], dtype=float)
		self.rprimd =temp2

		if len(self.E) > 0:
			self.goodFile = True
		else :
			try :
			    QtGui.QMessageBox.critical(None,"Warning","Your output file is not correct")
		        except:
		            print "Your output file is not correct"
		if len(self.a) == 1:
			self.a = np.zeros(len(self.E))+self.a[0]
			self.b = np.zeros(len(self.E))+self.b[0]
			self.c = np.zeros(len(self.E))+self.c[0]

		if len(self.ecut) == 1:
			self.ecut = np.zeros(len(self.E))+self.ecut[0]
	    except:
	        print "Unable to read file, please contact abinit Group"
	        QtGui.QMessageBox.critical(None,"Warning","Unable to read file, please contact abinit Group")



#-----------------------------#
#-------ACCESSOR--------------#
#-----------------------------#

    def getNameFile(self):
	# return string with the name of the file
        if self.goodFile:
	    name = self.namefile.split('/')
            return name[len(name)-1]
        else:
            return 0

    def getNbDataset(self):
	if self.goodFile:
	    return len(self.E)
	else:
	    return 0

    def getE_Tot(self):
	if self.goodFile:
	    return np.array(self.E)
	else:
	    return 0

    def getVol(self):
	if self.goodFile:
	    return np.array(self.V)
	else:
	    return 0

    def getSigma(self):
	if self.goodFile:
	    return self.sigma
	else:
	    return 0

    def getAcell(self):
	if self.goodFile:
	    return self.acell
	else:
	    return 0

    def getPress(self):
	if self.goodFile:
	    return np.array(self.P)
	else:
	    return 0

    def getNbK(self):
	if self.goodFile:
	    return np.array(self.Nbk)
	else:
	    return 0

    def getIonMove(self):
	if self.goodFile:
	    return np.array(self.ionMove)
	else:
	    return 0

    def getRPrim(self):
	if self.goodFile:
	    return self.rprimd
	else:
	    return 0

    def getEcut(self):
	if self.goodFile:
	    return np.array(self.ecut)
	else:
	    return 0

    def getA(self):
	if self.goodFile:
	    return self.a
	else:
	    return 0

    def getB(self):
	if self.goodFile:
	    return self.b
	else:
	    return 0

    def getC(self):
	if self.goodFile:
	    return self.c
	else:
	    return 0

    def getDate(self):
	if self.goodFile:
	    return self.date
	else:
	    return 0

    def getStress(self):
	if self.goodFile:
	    return self.stress
	else:
	    return 0

    def getHour(self):
	if self.goodFile:
	    return self.hour
	else:
	    return 0

    def isGoodFile(self):
        return self.goodFile
