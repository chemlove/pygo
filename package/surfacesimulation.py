from simulationobject import Simulation
import cPickle
import numpy
import pdb
#random.seed(10)
import energyfunc
import moveset
import writetopdb

numpy.random.seed(10)

def getsurf(xsize, ysize, spacing):
    """Generates coordinates for a surface given surface parameters; uses hexangonal packing"""
    xlen = xsize / spacing
    ylen = ysize / (spacing * 3.**.5 / 2.) # more dense from hexagonal packing
    surfcoord = numpy.zeros((int(xlen)*int(ylen),3))
    for j in range(1,xlen):
        surfcoord[j,:] = surfcoord[j-1,:] + numpy.array([spacing,0,0])
    k = 0
    for i in range(xlen,len(surfcoord),xlen):
        surfcoord[i,:] = surfcoord[i-xlen,:] + numpy.array([(-1)**k*spacing/2., spacing*3.**.5/2., 0]) 
        k += 1
        for j in range(1,xlen):
            surfcoord[i+j,:] = surfcoord[i+j-1,:] + numpy.array([spacing,0,0])
    com = numpy.sum(surfcoord, axis=0)/len(surfcoord)
    surfcoord -= com # centers surface at (0,0,0)
    return surfcoord

def writesurf(filename, surf_coord):
    fout = open(filename, 'w')
    fout.write('HEADER   This pdb file contains the coordinates for a Go model of surface\r\n')
    whitespace = "".join([" " for i in range(25)])
    for row in surf_coord:
        line = ['ATOM', whitespace, '%8.3f' % row[0], '%8.3f' % row[1], '%8.3f' % row[2], '\r\n']
        fout.write("".join(line))
    fout.close()

class SurfaceSimulation(Simulation):
    kb = 0.0019872041 #kcal/mol/K

    def __init__(self, name, outputdirectory, coord, temp, surf_coord):
        self.coord = coord
        self.addsurface(surf_coord) # translates self.coord
        Simulation.__init__(self, name, outputdirectory, self.coord, temp) # self.coord != coord anymore
        self.surfE_array = numpy.empty((Simulation.totmoves/Simulation.save + 1,2))
        self.surfE_array[0,:] = self.surfE
        self.moveparam = numpy.array([2., # translation
                        2., # rotation
                        10., # bend
                        10., # torsion
                        1., # global crankshaft
                        5.]) # ParRot move
        self.moveparam = self.moveparam * numpy.pi / 180 * self.T / 300 * 50 / Simulation.numbeads
        self.energyarray[0] = self.u0
        self.trmoves = 0
        self.rmoves = 0
        self.acceptedtr = 0
        self.acceptedr = 0

    def setenergy(self):
        Simulation.setenergy(self)
        self.surfE = energyfunc.csurfenergy(self.coord, SurfaceSimulation.surface, Simulation.numbeads, SurfaceSimulation.nspint, SurfaceSimulation.surfparam, SurfaceSimulation.scale)
        self.u0 += sum(self.surfE)

    def addsurface(self, surf_coord):
        self.surface = surf_coord
        ## randomly orient protein
        self.coord = moveset.rotation(self.coord,numpy.random.random(3))
        self.coord[:,2] += 10 - numpy.min(self.coord[:,2]) # protein is minimum 1 nm from surface
        
    def output(self):
        Simulation.output(self)
        if self.trmoves:
            print 'translation:       %d percent acceptance (%i/%i)' %(float(self.acceptedtr)/float(self.trmoves)*100, self.acceptedtr, self.trmoves)
        if self.rmoves:
            print 'rotation:          %d percent acceptance (%i/%i)' %(float(self.acceptedr)/float(self.rmoves)*100, self.acceptedr, self.rmoves)
      
    def loadstate(self):
        Simulation.loadstate(self)
        self.surfE_array = numpy.load('%s/surfenergy%s.npy' %(self.out, self.suffix))

    def loadextend(self, extenddirec):
        Simulation.loadextend(self, extenddirec) # u0 is reset
        self.energyarray[0] = self.u0
        self.surfE_array[0,:] = self.surfE

    def savesurfenergy(self):
        filename='%s/surfenergy%s' % (self.out, self.suffix)
        numpy.save(filename, self.surfE_array)

    def update_energy(self, torschange, angchange, dict):
        Simulation.numbeads = dict['numbeads']
        SurfaceSimulation.surface = dict['surface']
        SurfaceSimulation.nspint = dict['nspint']
        SurfaceSimulation.surfparam = dict['surfparam']
        SurfaceSimulation.scale = dict['scale']
        Simulation.update_energy(self, torschange, angchange, dict)
        self.newsurfE = energyfunc.csurfenergy(self.newcoord, SurfaceSimulation.surface, Simulation.numbeads, SurfaceSimulation.nspint, SurfaceSimulation.surfparam,SurfaceSimulation.scale)
        self.u1 += numpy.sum(self.newsurfE)

    def save_state(self, dict):
        Simulation.save = dict['save']
        Simulation.save_state(self, dict)
        self.surfE_array[self.move/Simulation.save,:] = self.surfE

    def accept_state(self):
        Simulation.accept_state(self) 
        self.surfE = self.newsurfE

    def run(self, nummoves, dict):
        Simulation.numbeads = dict['numbeads']
        Simulation.percentmove = dict['percentmove']   
        Simulation.save = dict['save']
        Simulation.totmoves = dict['totmoves']
        Simulation.numint = dict['numint']
        Simulation.angleparam = dict['angleparam']
        Simulation.torsparam = dict['torsparam']
        Simulation.nativeparam = dict['nativeparam']
        Simulation.nonnativeparam = dict['nonnativeparam']
        Simulation.nnepsil = dict['nnepsil']
        Simulation.nsigma2 = dict['nsigma2']
        Simulation.writetraj = dict['writetraj']
        SurfaceSimulation.surface = dict['surface']
        SurfaceSimulation.nspint = dict['nspint']
        SurfaceSimulation.nsurf = dict['nsurf']
        SurfaceSimulation.surfparam = dict['surfparam']
        SurfaceSimulation.scale = dict['scale']
        xlength = dict['xlength']
        ylength = dict['ylength']
        spacing = dict['spacing']
        yspacing = dict['yspacing']
        mass = dict['mass']
        Simulation.tsteps = dict['tsteps']
        Simulation.tsize = dict['tsize']
     
        for i in xrange(nummoves):
            randmove = numpy.random.random()
            randdir = numpy.random.random()
            m = numpy.random.randint(1, Simulation.numbeads-1) #random bead, not end ones
            uncloseable = False
    
            # translation
            if randmove < Simulation.percentmove[0]:
                jac = 1
                [x,y,z] = numpy.random.normal(0, self.moveparam[0], 3)
                self.newcoord = moveset.translation(self.coord, x, y, z)
                self.trmoves += 1
                movetype = 'tr'
                torschange = numpy.array([])
                angchange = numpy.array([])
            
            # rotation
            elif randmove < Simulation.percentmove[1]:
                jac = 1
                rand = numpy.random.random(3)
                rand[0] = 0.5 + self.moveparam[1] - 2*self.moveparam[1]*rand[0]
                rand[2] *= self.moveparam[1]
                self.newcoord = moveset.rotation(self.coord, rand)
                self.rmoves += 1
                movetype = 'rot'
                torschange = numpy.array([])
                angchange = numpy.array([])
                
            # angle bend
            elif randmove < Simulation.percentmove[2]:
                theta = numpy.random.normal(0, self.moveparam[2])
                self.newcoord, jac = moveset.canglebend(self.coord, m, randdir, theta)
                self.amoves += 1
                movetype = 'a'
                torschange = numpy.array([])
                angchange = numpy.array([m-1])
    
            # axis torsion
            elif randmove < Simulation.percentmove[3]:
                jac = 1
                theta = numpy.random.normal(0, self.moveparam[3])
                self.newcoord = moveset.caxistorsion(self.coord, m, randdir, theta)
                movetype = 'at'
                self.atmoves += 1
                angchange = numpy.array([])
                if randdir < .5:
                    torschange = numpy.array([m-2])
                    if m < 2:
                        torschange = numpy.array([])
                elif m == Simulation.numbeads - 2:
                    torschange = numpy.array([])
                else:
                    torschange = numpy.array([m-1])
    
            # global crankshaft
            elif randmove < Simulation.percentmove[4]:
                jac = 1
                theta = numpy.random.normal(0,self.moveparam[4],Simulation.numbeads-2)
                self.newcoord = moveset.cglobalcrank(self.coord,theta)
                self.gcmoves += 1
                movetype = 'gc'
                torschange = numpy.arange(Simulation.numbeads-3)
                angchange = numpy.arange(Simulation.numbeads-2)
    
        	# parrot move
            elif randmove < Simulation.percentmove[5]:
                theta = numpy.random.normal(0, self.moveparam[5])
                movetype = 'p'
                self.pmoves += 1
                angchange = numpy.array([])
                if m == 1:
                    self.newcoord = moveset.caxistorsion(self.coord, m, 1, theta)
                    torschange = numpy.array([0])
                    jac = 1
                elif m == Simulation.numbeads - 2:
                    self.newcoord = moveset.caxistorsion(self.coord, m, 0, theta)
                    torschange = numpy.array([m-2])
                    jac = 1
                else:
                    self.newcoord, jac = moveset.parrot(self.coord, m, randdir, theta)
                    if numpy.any(numpy.isnan(self.newcoord)):
                        uncloseable = True
                        self.rejected += 1
                        self.pclosure += 1
                        self.move += 1
                        del self.newcoord
                        del jac
                    elif randdir < .5:
                        torschange = numpy.arange(m-2,m+2)
                        torschange = torschange[torschange<(Simulation.numbeads-3)]
                    else:
                        torschange = numpy.arange(Simulation.numbeads-m-5,Simulation.numbeads-m-1)
                        torschange = torschange[torschange>-1]
                        torschange = torschange[torschange<(Simulation.numbeads-3)]
    
            # run molecular dynamics
            else:
                self=moveset.runMD_surf(self, Simulation.tsteps, Simulation.tsize, dict)
                movetype = 'md'
                self.mdmoves += 1
                torschange = numpy.arange(Simulation.numbeads-3)
                angchange = numpy.arange(Simulation.numbeads-2)
                jac = 1
            
            # check boundary conditions
            if not uncloseable:
                # x direction
                max = numpy.max(self.newcoord[:,0])
                min = numpy.min(self.newcoord[:,0])
                if max  > .5*xlength:
                    self.newcoord[:,0] -= numpy.ceil((max-xlength*.5)/spacing)*spacing
                elif min < -.5*xlength:
                    self.newcoord[:,0] += numpy.ceil((-.5*xlength-min)/spacing)*spacing
                # y direction
                max = numpy.max(self.newcoord[:,1])
                min = numpy.min(self.newcoord[:,1]) 
                if max  > .5*ylength:
                    self.newcoord[:,1] -= numpy.ceil((max-ylength*.5)/yspacing)*yspacing
                elif min < -.5*ylength:
                    self.newcoord[:,1] += numpy.ceil((-.5*ylength-min)/yspacing)*yspacing
    
            # accept or reject
            if not uncloseable and movetype=='md':
                self.update_energy(torschange, angchange, dict)
                self.newH=self.u1+.5/4.184*numpy.sum(mass*numpy.sum(self.vel**2,axis=1)) # in kcal/mol
                self.move += 1
                boltz = numpy.exp(-(self.newH-self.oldH)/(Simulation.kb*self.T))
                if numpy.random.random() < boltz:
                    self.accept_state()
                    self.accepted += 1
                    self.acceptedmd += 1
                else:
                    self.rejected += 1
            elif not uncloseable:
                self.update_energy(torschange, angchange, dict)
                self.move += 1
                boltz = jac*numpy.exp(-(self.u1-self.u0)/(Simulation.kb*self.T))
                if numpy.random.random() < boltz:
                    self.accept_state()
                    self.accepted += 1
                    if movetype == 'tr':
                        self.acceptedtr += 1
                    elif movetype == 'rot':
                        self.acceptedr += 1
                    elif movetype == 'a':
                        self.accepteda += 1
                    elif movetype == 'at': 
                        self.acceptedat += 1
                    elif movetype == 'gc':
                        self.acceptedgc += 1
                    else:
                        self.acceptedp += 1
                else:
                    self.rejected += 1
            if self.move % Simulation.save == 0:
                self.save_state(dict)
        return self 
    


