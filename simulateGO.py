
#========================================================================================================
# IMPORTS
#========================================================================================================

from datetime import datetime
t1=datetime.now()
from numpy import *
from writetopdb import *
from moveset import *
from energyfunc import *
from optparse import OptionParser
import matplotlib.pyplot as plt
from sys import stdout
from random import *
import profile
import scipy.misc

parser=OptionParser()
parser.add_option("-f", "--files", dest="datafiles", default='GO_protein.pdb', help="protein .pdb file")
parser.add_option("-p", "--parameterfile", dest="paramfiles", default='GO_protein.param', help="protein .param file")
parser.add_option("-d", "--directory", dest="datafile_directory", default='./', help="the directory the data files are in")
parser.add_option("-t", "--temperature", default='300', dest="T", type="float", help="temperature")
parser.add_option("-v", "--verbose", action="store_false", default=True, help="more verbosity")
parser.add_option("-c", "--addconnect", action="store_true", default=False, help="add bonds to .pdb file")
parser.add_option("-n", "--moves", dest="totmoves", type="int", default='100', help="total number of moves")
parser.add_option("-s", "--stepsize", dest="step", type="int", default='50', help="number of moves between each sample")
parser.add_option("-o", "--outputfiles", dest="outputfiles", default='conformation_energies.txt', help="the output file for every [step] energy")
parser.add_option("-g", "--histogram", dest="histname", default='', help="name histogram of conformational energies, if desired")
parser.add_option("-a", "--energyplot", dest="plotname", default='', help="name of plot of accepted conformation energies, if desired")
parser.add_option("-b", "--writepdb", action="store_true", default=False, help="write pdbs")

(options,args)=parser.parse_args()
#========================================================================================================
# CONSTANTS
#========================================================================================================

verbose=options.verbose
T=options.T #Kelvin
totmoves=options.totmoves
step=options.step
energyarray=zeros(totmoves/step+1)
rmsd_array=zeros(totmoves/step+1)
filename=options.datafile_directory + '/' + options.datafiles
paramfile=options.datafile_directory + '/' + options.paramfiles
outputfiles=options.outputfiles
histname=options.histname
plotname=options.plotname
writepdb=options.writepdb

# read .pdb to get number of beads (numbeads)
file=open(filename,'r')
numbeads=0
while 1:
	line=file.readline()
	if not line:
		break
	splitline=line.split('  ')
	if splitline[0]=='ATOM':
		numbeads += 1


# gets bead coordinates from .pdb file
file.seek(0)
coord=empty((numbeads,3)) #3 dimensional
i=0 # index for coordinate matrix
k=0 # index for line number
wordtemplate=[] #template of all words
positiontemplate=[] #template of position lines
ATOMlinenum=[] # array of location of ATOM lines
while 1:
    line = file.readline()
    if not line:
        break
    wordtemplate.append(line)
    splitline=line.split('  ')
    if splitline[0]=='ATOM':
        positiontemplate.append(line)
        ATOMlinenum.append(k)
        coord[i][0]=float(line[31:38])
        coord[i][1]=float(line[39:46])
        coord[i][2]=float(line[47:54])
        i=i+1
    k=k+1
file.close()

#Get native conformation
coord_nat=coord.copy()


#Get parameters from .param file
angleparam=getangleparam(paramfile,numbeads)
torsparam=gettorsionparam(paramfile,numbeads)
#LJparam=getLJparam(paramfile,numbeads)
#nativeparam=getnativefix(paramfile)

if (verbose):
	print 'verbosity is %s' %(str(verbose))
	print 'temperature is %f' %(T)
	print 'total number of moves is %d' %(totmoves)
	print 'autocorrelation step size is %d moves' %(step)
	print 'There are %d residues in %s' %(numbeads,filename)


#speed up terms
numint=scipy.misc.comb(numbeads,2) # number of interactions
numint= numint - 110 # don't count 12 and 13 neighbors

#native LJ parameter getting
nativeparam_n=getnativefix_n(paramfile,numint,numbeads) # [ones and zeros, native epsilon, native sigma]

#nonnative LJ parameter getting
nonnativesig=getLJparam_n(paramfile,numbeads,numint) #[nonnative sigmas for every interaction, epsilon (one value)]
nnepsil=-nonnativesig[-1] # last element
nonnativesig=delete(nonnativesig,-1) #remove epsilon from sigma array
nonnatindex=-1*(nativeparam_n[:,0]-1) # array of ones and zeros
nonnativeparam=column_stack((nonnatindex,nonnativesig)) #[ones and zeros, nonnative sigma]






#========================================================================================================
# SIMULATE
#========================================================================================================

def energy(mpos,rsquare):
	#energy=angleenergy(mpos,angleparam)+torsionenergy(mpos,torsparam)+LJenergy(mpos,LJparam,nativeparam)
	energy=angleenergy(mpos,angleparam)+torsionenergy(mpos,torsparam)+LJenergy_n(rsquare,nativeparam_n,nonnativeparam,nnepsil)
	return energy

r2=getLJr2(coord,numint,numbeads)
u0=energy(coord,r2)
accepted_energy=[u0]
energyarray[0]=u0
rmsd_array[0]=rmsd(coord_nat,coord)

if(writepdb):
	a=getmovietransform(coord)
	untransform=dot(a,eye(3))
	transform=transpose(untransform)
	mcoord=moviecoord(coord,transform)
	writeseqpdb(mcoord,wordtemplate,ATOMlinenum,0)

# constants for move stats
torsmoves=0
reptmoves=0
crankmoves=0
atormoves=0
acceptedat=0
acceptedt=0
acceptedr=0
acceptedc=0
accepted=0
rejected=0
movetype=''

move=0
theta=0. #for histogramming accepted torsion angles
accepted_angle=[]

while move<totmoves:
        rand=random()
	if rand < .7:
            newcoord=torsion(coord)
	    torsmoves += 1
	    movetype='t'
	elif rand < 0:
            newcoord=reptation(coord)
	    reptmoves += 1
	    movetype='r'
	elif rand < .85:
	    theta=45./180*pi-random()*pi*45./180*2 
	    newcoord=axistorsion(coord,theta)
	    movetype='at'
	    atormoves += 1
	else:
	    newcoord=crankshaft(coord)
	    crankmoves += 1
	    movetype='c'
	r2new=getLJr2(newcoord,numint,numbeads)
	u1=energy(newcoord,r2new)
        move += 1
	stdout.write(str(move)+'\r')
	stdout.flush()
	kb=0.0019872041 #kcal/mol/K
        boltz=exp(-(u1-u0)/(kb*T))
	if u1< u0 or random() < boltz:
        	accepted += 1
		if movetype=='t':
			acceptedt += 1
    		elif movetype=='r':
			acceptedr += 1
    		elif movetype=='at':
			acceptedat +=1
			accepted_angle.append(theta)
    		else: 
        		acceptedc += 1
    		if (writepdb):
			mcoord=moviecoord(newcoord,transform)
			#mcoord=moviecoord(newcoord)
			writeseqpdb(mcoord,wordtemplate,ATOMlinenum,accepted)
		r2=r2new   
		coord=newcoord
    		u0=u1
    		accepted_energy.append(u0)
	else:
	    rejected += 1
	if move%step==0:
	    energyarray[move/step]=u0
	    rmsd_array[move/step]=rmsd(coord_nat,coord)
t2=datetime.now()
#========================================================================================================
# OUTPUT
#========================================================================================================
#acceptfile=outputfiles[0]
#savetxt(acceptfile,accepted_energy)
#print 'wrote accepted energies to %s' %(acceptfile)

savetxt(outputfiles,energyarray)
print 'wrote every %d conformation energies to %s' %(step,outputfiles)

#savetxt('anglefile.txt',accepted_angle)
#print 'wrote accepted torsion angles to anglefile.txt'

savetxt('rmsd.txt',rmsd_array)
print 'wrote rmsd array to rmsd.txt'

if plotname != '':
	print 'generating conformational energy plot...'
	plt.figure(1)
	plt.plot(range(len(energyarray)),energyarray)
	plt.xlabel('move/%d' %(step))
	plt.ylabel('energy (kcal/mol)')
	plt.title('Go-like model monte carlo simulation at '+str(T)+' K')
	plt.savefig(plotname)
	print 'conformational energy plot saved to %s' %(plotname)

#if rmsdname != '':
	#print 'generating rmsd plot...'
	#plt.figure(3)
	#plt.plot(range(len(rmsdname)),rmsd)

if histname != '':
	print 'generating conformation energy histogram'
	plt.figure(2)
	plt.hist(energyarray,40)
	plt.title('conformation energies at %f Kelvin taken every %d moves' %(T,step))
	plt.xlabel('conformation energies (kcal/mol)')
	plt.savefig(histname)
	print 'conformation energy histogram saved to %s' %(histname)

if(verbose):
	print 'total accepted moves: %d' %(accepted)
	print 'total rejected moves: %d' %(rejected)
	print 'bend/torsion: %d moves accepted out of %d tries' %(acceptedt,torsmoves)
	print 'reptation: %d moves accepted out of %d tries' %(acceptedr,reptmoves)
	print 'crankshaft: %d moves accepted out of %d tries' %(acceptedc,crankmoves)
	print 'twist/torsion: %d moves accepted out of %d tries' %(acceptedat,atormoves)
	print('Simulation time: '+str(t2-t1))

#x=range(len(rmsd_array))
#plt.plot(x,rmsd_array)
#plt.ylabel('RMSD')
#plt.xlabel('move/100')
#plt.title('RMSD from native conformation at %f Kelvin taken every %d moves' %(T,step))
#plt.savefig(rmsdname)
