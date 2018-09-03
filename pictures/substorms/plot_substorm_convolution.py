import matplotlib
matplotlib.use('agg')
from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from substorm_utils.bin_listings import find_substorms_convolution, find_substorms, find_convolution_onsets, convolved_substorm_scores
from substorm_utils.event_id.al_onsets import borovsky_id_algorithm
from substorm_utils.event_id.dipolarizations import find_dipolarizations_br_bz_theta
from spacepy.pybats.bats import Bats2d
from datetime import datetime, timedelta
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import gaussian_kde
from substorm_utils.isi import get_isi
from substorm_utils.kde import get_kde_bootstrap
from pytz import UTC
from spacepy import datamodel as dm
from substorm_utils.timeseries import interp_timeseries
from matplotlib_utils import remove_overhanging_labels
from glob import glob
import os

matplotlib.rcParams['font.size']=8
matplotlib.rcParams['lines.markersize']=4
matplotlib.rcParams['lines.markeredgewidth']=0.8
matplotlib.rcParams['legend.handlelength']=0.7
matplotlib.rcParams['legend.borderpad']=0.2
matplotlib.rcParams['legend.borderaxespad']=0.2
matplotlib.rcParams['legend.handletextpad']=0.4
matplotlib.rcParams['legend.labelspacing']=0.25

run_properties=[
    {
        'name':'Hi-res w/ RCM',
    },
    {
        'name':'Hi-res w/o RCM',
    },
    {
        'name':'SWPC',
    },
]

model_threshold=2.5
obs_threshold=2.5

tstep=timedelta(0,1800)

from decouple import config
datadir=config('DATADIR')

signature_type_labels={
    'All':'All',
    'AL':'AL',
    'image':'IMAGE/\nFUV',
    'plasmoids':'Plasmoids',
    'dipolarizations':'Dipolar-\nizations',
    'epdata':'LANL',
    'MPB':'MPB'
}

def plot_convolution_score(signatures,ax,tmin,tmax,convolution_resolution=timedelta(0,60),bandwidth=timedelta(minutes=10),**kwargs):
    scores,tnums=convolved_substorm_scores(signatures,resolution=convolution_resolution,bandwidth=bandwidth)
    print tnums
    times=np.array([datetime(2005,1,1)+timedelta(0,s) for s in tnums])
    in_range=(times>=tmin) & (times<=tmax)
    times=times[in_range]
    scores=scores[in_range]
    ax.plot(times,scores,**kwargs)
    return scores,times

def make_convolution_figure(signatures,threshold,tstart,tend,bandwidth=timedelta(minutes=10),show_onsets=True,show_all=True,show_threshold=True,show_scores=True,show_individual_onsets=False):
    onsets_all=find_convolution_onsets(signatures,threshold,bandwidth=bandwidth)
    onsets_all=[datetime(2005,1,1)+timedelta(0,s) for s in onsets_all]
    fig=plt.figure(figsize=[4.5,3.5])
    from matplotlib.gridspec import GridSpec

    gs=GridSpec(len(signatures)+1,1,hspace=0,right=0.95,top=0.98,left=0.1,bottom=0.1)
    axes=[]

    for i,key in enumerate(signatures.keys()):
        ax=fig.add_subplot(gs[i,0])
        axes.append(ax)
        if show_scores:
            plot_convolution_score({key:signatures[key]},ax,tstart,tend,bandwidth=bandwidth)
        else:
            ax.set_ylim(0,1)
        onsets=[datetime(2005,1,1)+timedelta(0,s) for s in signatures[key]]
        if show_individual_onsets:
            ax.plot(onsets,np.ones(len(onsets))*0.5,linestyle='',marker='d')
        ax.set_ylabel(signature_type_labels[key])
        ax.set_xlim(tstart,tend)

    if show_all:
        ax=fig.add_subplot(gs[-1,0])
        axes.append(ax)
        ax.set_ylabel('All')
        plot_convolution_score(signatures,ax,tstart,tend,bandwidth=bandwidth)
        ax.set_xlim(tstart,tend)
        if show_threshold:
            ax.text(tstart+timedelta(seconds=(tend-tstart).total_seconds()*0.3),threshold+0.1,'threshold',fontsize=6)
            ax.axhline(threshold,color='r',alpha=0.5,linewidth=1)
    
    from matplotlib.dates import DateFormatter
    for i,ax in enumerate(axes):
        if i==len(axes)-1:
            ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
            ax.set_xlabel(tstart.strftime('Universal time, %d %b %Y'))
        else:
            plt.setp(ax.get_xticklabels(),visible=False)

        ax.tick_params('x',which='both',direction='inout',top=True)
        if show_scores:
            ax.yaxis.set_major_locator(plt.MaxNLocator(3,integer=True))
        else:
            ax.yaxis.set_major_locator(plt.NullLocator())

        if show_onsets:
            for onset in onsets_all:
                ax.axvline(onset,linewidth=0.5,color='k',linestyle='--')

        ymin,ymax=ax.get_ylim()
        min_ymax=1.2
        if ymax<min_ymax:
            ax.set_ylim(ymin,min_ymax)

    fig.canvas.draw()

    for ax in axes:
        remove_overhanging_labels(ax,fig,'y')


    return fig

if __name__=='__main__':
    obs_signatures=get_obs_signature_lists(datadir=datadir)
    threshold=2.5
    tstart=datetime(2005,1,22)
    tend=datetime(2005,1,23)
    fig=make_convolution_figure(obs_signatures,threshold,tstart,tend,bandwidth=timedelta(minutes=10))
    fig.savefig('substorm_convolution.svg')
