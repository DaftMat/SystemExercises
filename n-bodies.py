#mpirun -n 3 python3 n-bodies.py 12 1000
from mpi4py import MPI
import sys
import math
import random
import numpy as np
import matplotlib.image as mpimg
from scipy import misc
import matplotlib.pyplot as plt 
import matplotlib.cm as cm
import time

# split a vector "x" in "size" part, each of them having "n" elements
def split(x, n, size):
	return [x[n*i:n*(i+1)] for i in range(size)]

# unsplit a list x composed of n lists of t elements
def unsplit(x):
	y = []
	n = len(x)
	for i in range(n):
		for j in range(len(x[i])):
			y.append(x[i][j])
	return y

def circlev(rx, ry):
	r2=math.sqrt(rx*rx+ry*ry)
	numerator=(6.67e-11)*1e6*solarmass
	return math.sqrt(numerator/r2)

# from http://physics.princeton.edu/~fpretori/Nbody/code.htm
class Data_item:

	def __init__(self, id, positionx, positiony, speedx, speedy, weight):
		self.id = id
		self.positionx = positionx
		self.positiony = positiony
		self.weight = weight

		if positionx==0 and positiony==0:    # the center of the world, very heavy one...
			self.speedx = 0
			self.speedy = 0
		else:
			if speedx==0 and speedy==0:			# initial values
				magv=circlev(positionx, positiony)
				absangle = math.atan(math.fabs(positiony/positionx))
				thetav= math.pi/2-absangle
				phiv = random.uniform(0,1)*math.pi
				self.speedx = -1*math.copysign(1, positiony)*math.cos(thetav)*magv
				self.speedy = math.copysign(1, positionx)*math.sin(thetav)*magv
				#Orient a random 2D circular orbit
				if (random.uniform(0,1) <=.5):
					self.speedx=-self.speedx
					self.speedy=-self.speedy
			else:
				self.speedx = speedx
				self.speedy = speedy
	
	def __str__(self):
		return "ID="+str(self.id)+" POS=("+str(self.positionx)+","+str(self.positiony)+") SPEED=("+str(self.speedx)+","+str(self.speedy)+") WEIGHT="+str(self.weight)

def display(m, l):
	for i in range(len(l)):
		print("PROC"+str(rank)+":"+m+"-"+str(l[i]))

def displayPlot(d):
	plt.gcf().clear()			# to remove to see the traces of the particules...
	plt.axis((-1e17,1e17,-1e17,1e17))
	xx = [ d[i].positionx  for i in range(len(d)) ]
	yy = [ d[i].positiony  for i in range(len(d)) ]
	plt.plot(xx, yy, 'ro')
	plt.draw()
	plt.pause(0.00001)			# in order to see something otherwise too fast...


def interaction(d, i, j):
	dist = math.sqrt( (d[j].positionx-d[i].positionx)*(d[j].positionx-d[i].positionx) +  (d[j].positiony-d[i].positiony)*(d[j].positiony-d[i].positiony) )
	if i==j:
		return (0,0)
	g = 6.673e-11
	factor = g * d[i].weight * d[j].weight / (dist*dist+3e4*3e4)
	return factor * (d[j].positionx-d[i].positionx) / dist, factor * (d[j].positiony-d[i].positiony) / dist

def update(d, f, dt):
	vx = d.speedx + dt * f[0]/d.weight
	vy = d.speedy + dt * f[1]/d.weight
	px = d.positionx + dt * vx
	py = d.positiony + dt * vy
	return Data_item(id=d.id, positionx=px, positiony=py, speedx=vx, speedy=vy, weight=d.weight)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
solarmass=1.98892e30

nbbodies = int(sys.argv[1])
NBSTEPS = int(sys.argv[2])

plt.draw()
plt.show(block=False)

#random.seed(0)  		# to uncomment if you want to have always the same random numbers, hence the same behaviour

l = []
data=[]

if rank == 0:
	data = [ Data_item(id=i, positionx=1e18*math.exp(-1.8)*(.5-random.uniform(0,1)), positiony=1e18*math.exp(-1.8)*(.5-random.uniform(0,1)), speedx=0, speedy=0, weight=(random.uniform(0,1)*solarmass*10+1e20)) for i in range(nbbodies-1)]
	# then add a heavy body in the center...
	data.append( Data_item(id=nbbodies-1, positionx=0, positiony=0, speedx=0, speedy=0, weight=1e6*solarmass))
	for i in range(nbbodies):
		print(data[i])
	displayPlot(data)
	l = split(data, int(nbbodies / size), size)
	print("Distributing...")

data = comm.bcast(data, root=0)
local_data = comm.scatter(l, root=0)
local_n = len(local_data)
#display("INITIAL", local_data)

force = [[0,0] for i in range(local_n) ]

for t in range(NBSTEPS):
	for i in range(local_n):
		force[i]=[0,0]
		for j in range(nbbodies):
			f = interaction(data, i+local_n*rank, j)
			force[i][0]=force[i][0]+f[0]    # the force in the X axis
			force[i][1]=force[i][1]+f[1]    # the force in the Y axis
	for i in range(local_n):
		local_data[i] = update(local_data[i], force[i], 1e11)
	#	display("t="+str(t), local_data)
	l = comm.allgather(local_data)
	data = unsplit(l)
	if rank==0:
		displayPlot(data)








