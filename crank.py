from numpy import *
from random import *

def crankshaft(mpos123): #moleculeposition, will need bonds later
    mpos=mpos123.copy()
    m=randint(1,6) #random molecule, not end ones

    posb=mpos[m][:] # middle molecule, will get crankshafted
    posa=mpos[m-1][:] #one 'before' it
    posc=mpos[m+1][:] # one 'after' it

    AB=posb-posa
    AC=posc-posa
    
    x=[1,0,0]
    y=[0,1,0]
    z=[0,0,1]
    x1=AC/dot(AC,AC)**.5
    y1=AB-dot(AB,AC)/dot(AC,AC)*AC
    y1=y1/dot(y1,y1)**.5
    z1=cross(x1,y1)
    untransform=[[dot(x,x1),dot(x,y1),dot(x,z1)],[dot(y,x1),dot(y,y1),dot(y,z1)],[dot(z,x1),dot(z,y1),dot(z,z1)]]
    transform=transpose(untransform)
    
    
    theta=2*pi*random()
    rotate=array([[1,0,0],[0,cos(theta),sin(theta)],[0,-sin(theta),cos(theta)]])

    AB1=dot(transform,AB.transpose())
    AB2=dot(rotate,AB1)
    AB=dot(untransform,AB2)
    mpos[m][:]=posa+AB.transpose()
    return mpos

def reptation(mpos123):
    mpos=mpos123.copy()
    theta=pi*random()
    phi=2*pi*random()
    rho=1.53710311951 #unhardcode this later
    vec=[rho*sin(theta)*cos(phi),rho*sin(theta)*sin(phi),rho*cos(theta)]    
    n=len(mpos)
    if random() < .5:    
	for i in range(n-1):
             mpos[i][:]=mpos[i+1][:]
    	mpos[n-1][:]=mpos[n-2][:]+vec
    else:
	for i in range(n-1,0,-1):
	     mpos[i][:]=mpos[i-1][:]
	mpos[0][:]=mpos[1][:]+vec
    return mpos

def torsion(mpos123):
	mpos=mpos123.copy()
	dtheta=pi*random()
	dphi=2*pi*random()
	m=randint(1,6)
	for i in range(m,len(mpos)-1):
		BC=mpos123[:][i+1]-mpos123[:][i]
        	r=dot(BC,BC)**.5
		theta=arccos(BC[2]/r)+dtheta #new theta
		phi=arctan(BC[1]/BC[0])+dphi #new phi
		BC[0]=r*sin(theta)*cos(phi)
		BC[1]=r*sin(theta)*sin(phi)
		BC[2]=r*cos(theta)
		mpos[:][i+1]=mpos[:][i]+BC
	return mpos
	
def writepdb(mpos,text,posline,move):
    j=0
    for i in posline:
        words=text[i][0:30]
	coordstrmatch=text[i][30:-1]
	coordstr=''
	coordstr=coordstr+str('%8.3f') % mpos[j][0]
	coordstr=coordstr+str('%8.3f') % mpos[j][1]
	coordstr=coordstr+str('%8.3f') % mpos[j][2]
	coordstr=coordstr+'\r\n'
        j=j+1
        text[i]=words+coordstr
    f=file(str(move)+'.pdb','w')
    write=''
    for k in range(len(text)):
        write=write+text[k]
    f.write(write)
    print('Wrote '+str(move)+'.pdb')
    f.close

def energy(mpos):
    energy=0.0; #potential energy
    sig=4.6 #angstroms for polyethylene
    e= .42 #kcal/mol for polyethylene
    ktheta= .82 #kcal/mol 
    index=arange(len(mpos))
    for i in index:
        low=index[index<i-2]
        high=index[index>i+2]
        vdw=append(low,high) #index of beads excluding 12 and 13 neighbors
        for j in vdw:
            r=((mpos[i][0]-mpos[j][0])**2+(mpos[i][1]-mpos[j][1])**2+(mpos[i][2]-mpos[j][2])**2)**.5
            energy=energy+4*e*((sig/r)**12-(sig/r)**6)
    for i in range(1,len(mpos)-1):
        BA=mpos[:][i-1]-mpos[:][i]
        BC=mpos[:][i+1]-mpos[:][i]
        angle=arccos(dot(BA,BC)/(dot(BA,BA)**.5*dot(BC,BC)**.5)) #in radians
        energy=energy+ktheta/2*(angle-pi)**2
    return energy/2

