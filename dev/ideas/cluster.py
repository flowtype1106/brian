'''
Distributed simulations on clusters, using MPI.

Groups hosted on other machines are mapped to virtual groups.
Connection objects do not change (simply, source or target may be virtual).
The ClientNetwork object runs the network normally, except it sends and receives spikes
from times to times to other machines.
The ServerNetwork object creates ClientNetwork objects and distributes them over the
machines. It does not need supervise the simulation.

How about creation? (in particular, connection objects should be created on the target machine)
    It should be possible to create the objects on the target machines, e.g.:
    * create the group/connection on the server
    * communicate the object to the client
    * convert to virtual group on the server

How about monitoring?
    Simply communicate the monitors to the machine hosting the relevant neuron group.

How about plasticity?

Objects on a node:
* (real) groups
* virtual groups
* connections to groups only (from groups and virtual groups)

A time step involves:
* normal calls to real groups (update, threshold, reset)
* broadcast of spikes from all groups; can be done in the threshold operation
* usual connection propagate

Essentially, what needs to be done is:
* removing update/reset from virtual groups
* having a special threshold in virtual group which simply does a broadcast
* adding the broadcast to real groups

Note that this mechanism can handle homogeneous delays in a simple way
(the LS structure pushes the spikes as usual).
Thus, the main difficulty is setting up the simulation.
There can also difficulties with monitors and network operations.

How to distribute the groups?
1) Simplest possibility: use preexisting groups, do not split them.
Then simply divide them equally among processors.
2) Divide every group equally in the number of processors.
3) Divide the set of groups between processors, then divide each group.

Strategy 2 has an advantage: NeuronGroups and Connections can be divided
at initialisation time. Then the connect functions of Connection could be
overriden so that the matrices are only created on the clients
(faster and much better for memory). It could be done on the same way
for neuron groups, but it is probably sufficient to do the construction on
the server and do the transfer when the network run is called. However with
network operations, state transfers should be possible at run time.

One simple possibility would be something like:
from brian import *
from brian.cluster import *

and the latter statement would redefine NeuronGroup, Connection, etc.
Something like:
NeuronGroup = ClusterNeuronGroup
Connection = ClusterConnection

The same script could be run on all processors, that could make
things much simpler. For example, consider 2 processors and the statement
P=NeuronGroup(100,model=...)
creates a ClusterNeuronGroup on each processor, in which either
P[:50] or P[50:] is real while the rest is virtual (it may not be
necessary).
Then P.v=rand(100) would only assign the relevant part of the vector.
It seems to be wasting a lot of time since the same operation is repeated on
all processors, but they are done in parallel so it is not less efficient than
doing everything on a server and transferring the data (in fact it is more
efficient since we avoid the transfers).
Connections would work in the same way, with minor code changes.
Monitors could also work similarly, which would work as
if each group P were replaced by a subgroup.

The only asymmetry would be that processor 0 would gather all information
from monitors at the end, and possibly some analysis, plotting, etc.
So there should probably be some specific code for the server.
That makes it less interesting to use the same script for all nodes...

Also, the statement
from brian.cluster import *
could be avoided by placing a test in brian.__init__ that checks the number
of processor (i.e., whether the script has been run with mpiexec).
'''
import pypar
from brian.neurongroup import *
from brian.network import *

class VirtualGroup(NeuronGroup):
    '''
    A group that is hosted on another machine.
    A number of methods will raise an exception (e.g. accessing the state variables).
    '''
    def __init__(self,group,machine):
        '''
        Initializes the virtual group:
            group: real group
            machine: machine id
        '''
        # How do we deal with clocks?
        self._S0=group._S0
        self.staticvars=group.staticvars
        self.var_index=group.var_index
        self._max_delay=group._max_delay
        self.LS=group.LS
        self._owner=machine
        self._length=len(group)
        self._numstates=group.num_states()        
 
    # Update and reset are disabled
    def update(self):
        pass    
    def reset(self):
        pass
    def __len__(self):
        return self._length
    def num_states(self):
        return self._numstates    
    def __repr__(self):
        return 'Virtual group of '+str(len(self))+' neurons'
    
class ServerNetwork(Network):
    '''
    Network class for running a simulation over a cluster.
    The server manages the clients.
    '''
    pass

class ClientNetwork(Network):
    '''
    Network class for running a simulation over a cluster, client side.
    '''
    pass
