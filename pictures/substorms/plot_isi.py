import matplotlib
matplotlib.use('agg')
from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from substorm_utils.bin_listings import find_substorms_convolution, find_substorms, find_convolution_onsets
from datetime import datetime, timedelta
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import gaussian_kde
from substorm_utils.isi import get_isi
from substorm_utils.kde import get_kde_bootstrap
from matplotlib_utils import remove_overhanging_labels
from pytz import UTC

matplotlib.rcParams['font.size']=8
matplotlib.rcParams['legend.handlelength']=0.7
matplotlib.rcParams['legend.borderpad']=0.2
matplotlib.rcParams['legend.borderaxespad']=0.2
matplotlib.rcParams['legend.handletextpad']=0.4
matplotlib.rcParams['legend.labelspacing']=0.25
matplotlib.rcParams['lines.linewidth']=0.75

run_properties=[
    {
        'name':'Hi-res w/ RCM',
        'path':'/data2/jhaiduce/substorms_Jan2005_young-comp'
    },
    #{
    #    'name':'Hi-res w/o RCM',
    #    'path':'/data2/jhaiduce/Jan2005_rerun'
    #},
    #{
    #    'name':'SWPC',
    #    'path':'/data1/jhaiduce/Jan2005_swpc'
    #},
]

model_threshold=2.5
obs_threshold=2.5

signature_type_labels={
    'All':'All',
    'AL':'AL',
    'image':'IMAGE/FUV',
    'plasmoids':'Plasmoids',
    'dipolarizations':'Dipolarizations',
    'epdata':'LANL',
    'MPB':'MPB'
}

tstep=timedelta(0,1800)

from decouple import config
datadir=config('DATADIR')

def plot_isi(ax,bins,times,color,bw=None,show_ci=False):
    from isi_functions import get_kde_cached,get_kde_ci
    
    isi=get_isi(times)/3600
    kde=get_kde_cached(isi,bw,bins)
    
    if show_ci:
        ci=get_kde_ci(isi,bins,2000,bw)
        polies=ax.fill_between(bins,ci[0],ci[2],facecolor=color,edgecolor='none',alpha=0.5)
    else:
        polies=ax.fill_between(bins,kde,kde,facecolor='none',edgecolor='none',alpha=0.5)
        
    line,=ax.plot(bins,kde,color=color)

    return line,polies

def isi_subplot(ax,run_names,onset_type,bin_max=15):
    fills=[]
    lines=[]
    labels=[]

    for run_name in run_names:
        
        if run_name=='obs':
            signatures=get_obs_signature_lists(datadir=datadir)
            threshold=obs_threshold
        else:
            runprops,=[runprops for runprops in run_properties if runprops['name']==run_name]
            
            signatures=get_model_signature_lists(runprops,datadir=datadir)
            threshold=model_threshold

        if onset_type=='all':
            onsets=find_convolution_onsets(signatures,threshold,bandwidth=timedelta(0,60*10))
            #onsets=[(onset-datetime(2005,1,1,tzinfo=UTC)).total_seconds() for onset in onsets]
            #print onsets
            #substorms,onsets=find_substorms(signatures,threshold=1,return_times=True,signature_filters=['AL'])
            #onsets=onsets.compressed()
            #print onsets
        else:
            onsets=signatures.get(onset_type,[])

        bins=np.linspace(0,bin_max,100)
        bw=0.2

        if len(onsets)>3:
            if run_name=='obs':
                color='LightSteelBlue'
            else:
                all_runnames=[runprops['name'] for runprops in run_properties]
                irun=all_runnames.index(run_name)
                import matplotlib
                run_colors=matplotlib.rcParams['axes.prop_cycle'].by_key()['color']
                color=run_colors[irun]

            if run_name=='obs' or onset_type=='plasmoids':
                show_ci=True
            else:
                show_ci=False
            line,fill=plot_isi(ax,bins,onsets,color,bw,show_ci=show_ci)
            lines.append(line)
            fills.append(fill)
            if run_name=='obs':
                labels.append('Observations')
            else:
                if len(run_properties)>1:
                    labels.append(run_name)
                else:
                    labels.append('MHD')
    return zip(lines,fills),labels

def make_isi_figure(run_names,onset_type,bin_max=15):

    fig=plt.figure()
    ax=fig.add_subplot(1,1,1)

    handles,labels=isi_subplot(ax,run_names,onset_type,bin_max)

    if len(labels)>1:
        ax.legend(handles,labels,loc='best')
    if onset_type=='all':
        ax.set_title('All signatures')
    else:
        ax.set_title(signature_type_labels[onset_type])
    ax.set_ylabel('Probability density')
    ax.set_xlabel('Waiting time (h)')
    return fig

def make_tiled_isi_figure(onset_types):
    run_names=[runprops['name'] for runprops in run_properties]
    run_names=['obs']+run_names

    fig=plt.figure(figsize=(5.5,1.5*len(onset_types)))

    from matplotlib.gridspec import GridSpec
    gs=GridSpec(len(onset_types),len(onset_types[0]),hspace=0,right=0.98,top=0.9,wspace=0,left=0.1,bottom=0.12)

    labelpos=(0.95,0.95)
    from string import ascii_lowercase
    subplot_labels=[ascii_lowercase[i] for i in range(6)]

    axes=[]
    for i in range(len(onset_types)):
        axes.append([])
        for j in range(len(onset_types[i])):
            
            if j>0:
                ax_kwargs={'sharey':axes[i][0]}
            else:
                ax_kwargs={}
                
            ax=fig.add_subplot(gs[i,j],**ax_kwargs)
            axes[i].append(ax)
            # Add a label to the axis
            label=subplot_labels[i*2+j]
            text=ax.text(labelpos[0],labelpos[1],label,transform=ax.transAxes,weight='bold',fontsize=11,verticalalignment='top',color='k',horizontalalignment='right')

            onset_type=onset_types[i][j]
            handles,labels=isi_subplot(ax,run_names,onset_type,bin_max=20)

            if onset_type=='all':
                title='All signatures'
            else:
                title=signature_type_labels[onset_type]
            ax.text(0.5,0.95,title,transform=ax.transAxes,fontsize=10,color='k',horizontalalignment='center',verticalalignment='top')
                
            if j==0:
                ax.set_ylabel('Probability density')
            else:
                plt.setp(ax.get_yticklabels(),visible=False)
                ax.set_ylabel('')
            if i==len(onset_types)-1:
                ax.set_xlabel('Waiting time (h)')
            else:
                plt.setp(ax.get_xticklabels(),visible=False)
                ax.set_xlabel('')
            ax.tick_params('x',which='both',direction='inout',top=True)
            ax.tick_params('y',which='both',direction='inout',top=True)
            if i==0 and j==1:
                ax.legend(handles,labels,loc='center right')
            ymin,ymax=ax.get_ylim()
            ax.set_ylim(0,ymax)
    fig.canvas.draw()

    for i in range(2):
        for j in range(2):
            ax=axes[i][j]
            remove_overhanging_labels(ax,fig,'x')
            remove_overhanging_labels(ax,fig,'y')
            
    return fig

if __name__=='__main__':
    
    fig=make_tiled_isi_figure([
        ['AL','dipolarizations'],
        ['MPB','all'],
    ])
        
    fig.savefig('isi.svg')
