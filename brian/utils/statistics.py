'''
Spike statistics
----------------
In all functions below, spikes is a sorted list of spike times
'''
from numpy import diff,std,mean,array,dot,ones,arange,histogram
from brian.stdunits import ms

# First-order statistics
def firing_rate(spikes):
    '''
    Rate of the spike train.
    '''
    return (len(spikes)-1)/(spikes[-1]-spikes[0])

def CV(spikes):
    '''
    Coefficient of variation.
    '''
    ISI=diff(spikes) # interspike intervals
    return std(ISI)/mean(ISI)

# Second-order statistics
def correlogram(T1,T2,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns a cross-correlogram with lag in [-tmax,tmax] and given bin size.
    T is the total duration (optional) and should be greater than the duration of T1 and T2.
    The result is in Hz (rate of coincidences in each bin).

    N.B.: units are discarded.
    TODO: optimise?
    '''
    # Remove units
    tmax=float(tmax)
    T1=array(T1)
    T2=array(T2)
    i=0
    j=0
    n=int(ceil(tmax/bin)) # Histogram length
    l=[]
    for t in T1:
        while i<len(T2) and T2[i]<t-tmax: # other possibility use searchsorted
            i+=1
        while j<len(T2) and T2[j]<t+tmax:
            j+=1
        l.extend(T2[i:j]-t)
    H,_=histogram(l,bins=arange(2*n+1)*bin-n*bin)
    
    # Divide by time to get rate
    if T is None:
        T=max(T1[-1],T2[-1])-min(T1[0],T2[0])
    # Windowing function (triangle)
    W=zeros(2*n)
    W[:n]=T-bin*arange(n-1,-1,-1)
    W[n:]=T-bin*arange(n)
    
    return H/W

def autocorrelogram(T0,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns an autocorrelogram with lag in [-tmax,tmax] and given bin size.
    T is the total duration (optional) and should be greater than the duration of T1 and T2.
    The result is in Hz (rate of coincidences in each bin).

    N.B.: units are discarded.
    '''
    return correlogram(T0,T0,tmax,bin,T)

def CCF(T1,T2,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns the cross-correlation function with lag in [-tmax,tmax] and given bin size.
    T is the total duration (optional).
    The result is in Hz**2:
    CCF(T1,T2)=<T1(t)T2(t+s)>

    N.B.: units are discarded.
    '''
    return correlogram(T1,T2,tmax,bin,T)/bin

def ACF(T0,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns the autocorrelation function with lag in [-tmax,tmax] and given bin size.
    T is the total duration (optional).
    The result is in Hz**2:
    ACF(T0)=<T0(t)T0(t+s)>

    N.B.: units are discarded.
    '''
    return CCF(T0,T0,tmax,bin,T)

def CCVF(T1,T2,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns the cross-covariance function with lag in [-tmax,tmax] and given bin size.
    T is the total duration (optional).
    The result is in Hz**2:
    CCVF(T1,T2)=<T1(t)T2(t+s)>-<T1><T2>

    N.B.: units are discarded.
    '''
    return CCF(T1,T2,tmax,bin,T)-firing_rate(T1)*firing_rate(T2)

def ACVF(T0,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns the autocovariance function with lag in [-tmax,tmax] and given bin size.
    T is the total duration (optional).
    The result is in Hz**2:
    ACVF(T0)=<T0(t)T0(t+s)>-<T0>**2

    N.B.: units are discarded.
    '''
    return CCVF(T0,T0,tmax,bin,T)

def total_correlation(T1,T2,tmax=20*ms,bin=1*ms,T=None):
    '''
    Returns the total correlation coefficient with lag in [-tmax,tmax].
    T is the total duration (optional).
    The result is a real (typically in [0,1]):
    total_correlation(T1,T2)=int(CCVF(T1,T2))/rate(T1)

    N.B.: units are discarded.
    
    TODO: more direct calculation
    '''
    return float(bin*sum(CCVF(T1,T2,tmax,bin,T))/firing_rate(T1))

if __name__=='__main__':
    from brian import *
    N=100000
    T1=cumsum(rand(N)*10*ms)
    T2=cumsum(rand(N)*10*ms)
    duration=T1[N/2] # Cut so that both spike trains have the same duration
    T1=T1[T1<duration]
    T2=T2[T2<duration]
    print firing_rate(T1)
    C=CCVF(T1,T2,bin=1*ms)
    print total_correlation(T1,T2,bin=1*ms)
    plot(C)
    show()
    #print std(C)*second