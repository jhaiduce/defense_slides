import matplotlib
matplotlib.use('agg')
from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from substorm_utils.bin_listings import find_convolution_onsets, find_substorms_convolution
from datetime import datetime, timedelta
from substorm_utils.forecast_stats import dump_stats
import numpy as np
from spacepy.pybats import ImfInput
from matplotlib import pyplot as plt
import os
from pytz import UTC
from matplotlib_utils import remove_overhanging_labels
from substorm_utils.parsers.mpb_parsers import parse_index
from sea_functions import get_sea_curves
from scipy.io import loadmat

matplotlib.rcParams['font.size']=8
matplotlib.rcParams['legend.handlelength']=1
matplotlib.rcParams['legend.borderpad']=0.2
matplotlib.rcParams['legend.borderaxespad']=0.2
matplotlib.rcParams['legend.handletextpad']=0.4
matplotlib.rcParams['legend.labelspacing']=0.25
matplotlib.rcParams['lines.linewidth']=0.75


run_properties=[
    {
        'name':'Hi-res w/ RCM',
        'displayname':'SWMF',
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

signature_filters=('AL','MPB','dipolarizations','plasmoids','epdata','image')
mandatory_signatures=()

model_threshold=2.5
obs_threshold=2.5

tstep=timedelta(0,1800)

from decouple import config
datadir=config('DATADIR')

supermag_data=np.loadtxt(os.path.join(datadir,'20160728-19-38-supermag.txt'),skiprows=88)
supermag_times=np.array([datetime(2005,1,1,tzinfo=UTC)+timedelta(seconds=60*i) for i in range(1440*31+1)])
sml=supermag_data[:,6]

imfdata=ImfInput(os.path.join(datadir,'imf_jan2005_merged_zeroed.dat'))
imfdata['time']=[t.replace(tzinfo=UTC) for t in imfdata['time']]
imf_clockangle=np.arctan2(imfdata['by'],imfdata['bz'])
imf_bmag=np.sqrt((imfdata['bx']**2+imfdata['by']**2+imfdata['bz']**2))*1e-9
mu0=4*np.pi*1e-7
imf_bz=imfdata['bz']*1e-9
imf_ux=imfdata['ux']*1000
imf_epsilon=-imf_ux*imf_bmag**2*np.sin(imf_clockangle/2)**4/mu0*1e6

obs_mpb_t,obs_mpb_v=parse_index(os.path.join(datadir,'obs_mpb_index.txt'))

obs_signatures=get_obs_signature_lists(datadir=datadir)

seadata={
    'bz':['IMF $B_z$ (nT)',imfdata['bz'],imfdata['time']],
    'al':['AL (nT)',sml,supermag_times],
    'ux':['Solar wind $u_x$ (km/s)',-imfdata['ux'],imfdata['time']],
    'rho':[r'Solar wind $\rho$ ($cm^{-3}$)',imfdata['rho'],imfdata['time']],
    'epsilon':['Solar wind $\epsilon$ ($\mu W/m^2$)',imf_epsilon,imfdata['time']],
    'MPB':['MPB ($nT^4$)',obs_mpb_v,obs_mpb_t]
}

obs_substorms,obs_onsets=find_substorms_convolution(obs_signatures,obs_threshold,tstep=tstep,return_times=True)

run_onsets={}

run_signatures=get_model_signature_lists(run_properties[0],datadir=datadir)

signature_type_labels={
    'All':'All',
    'AL':'AL',
    'image':'IMAGE/FUV',
    'plasmoids':'Plasmoids',
    'dipolarizations':'Dipolarizations',
    'epdata':'LANL',
    'MPB':'MPB'
}

signature_types=set(['All']+obs_signatures.keys()+run_signatures.keys())
run_colors={run:color for run,color in zip(
    signature_types,
    matplotlib.rcParams['axes.prop_cycle'].by_key()['color']
)}
run_linestyles={run:linestyle for run,linestyle in zip(
    signature_types,
    ['-','-.','--',':',
     (0, (3, 1, 1, 1, 1, 1)),
     (0, (3, 1, 1, 1)),
     (0, (5, 1))]
)}


def plot_sea(ax,onsets,data,times,color,show_iqr=False,**kwargs):
    x,median,bound_low,bound_high=get_sea_curves(data,times,onsets)
    iqr_color=color
    if show_iqr:
        polies=ax.fill_between(x,bound_low,bound_high,facecolor=iqr_color,alpha=0.5,edgecolor=iqr_color)
    else:
        iqr_color='none'
        hatch=None
        polies=ax.fill_between(x,median,median,facecolor=iqr_color,alpha=0.5,edgecolor=iqr_color)
    #polies=ax.plot(mysea.x,mysea.bound_low.ravel(),linestyle='--',color=color,alpha=0.5)
    #polies=ax.plot(mysea.x,mysea.bound_high.ravel(),linestyle='--',color=color,alpha=0.5)
    line,=ax.plot(x,median,color=color,**kwargs)
    return line,polies

def plot_onset_sea(signatures,threshold,data,times,ylabel,ax,signature_types=signature_types):
    onsets=find_convolution_onsets(signatures,threshold)
    onsets=[datetime(2005,1,1)+timedelta(0,s) for s in onsets]
    
    if len(signature_types)==1:
        show_iqr=True
    else:
        show_iqr=False
    
    line,polies=plot_sea(ax,onsets,data,times,color=run_colors['All'],
                         linestyle=run_linestyles['All'],linewidth=2,
                         show_iqr=show_iqr)
    lines=[line]
    polycols=[polies]

    for key in signature_types:
        if key=='All': continue
        if key in signatures:
            onsets=signatures[key]
            onsets=[datetime(2005,1,1)+timedelta(0,s) for s in onsets]
            if len(onsets)==0: continue
            line,polies=plot_sea(ax,onsets,data,times,color=run_colors[key],
                                 linestyle=run_linestyles[key],
                                 show_iqr=show_iqr)
            lines.append(line)
            polycols.append(polies)
        else:
            from matplotlib.lines import Line2D
            from matplotlib.patches import Patch
            lines.append(Line2D([],[],color=run_colors[key],
                                 linestyle=run_linestyles[key]))
            polycols.append(Patch(color='none',edgecolor='none'))
    
    ax.autoscale(False)
    ax.axhline(0,color='k',linestyle=':')
    ax.axvline(0,color='k',linestyle=':')
    ax.set_ylabel(ylabel)
    ax.set_xlabel('Time since onset (h)')
    return zip(polycols,lines),[signature_type_labels[key] for key in signature_types]

def plot_sea_onset_comparison(run_name,var,ax,signature_types=signature_types):

    if run_name=='obs':

        seadata['MPB']=['MPB ($nT^4$)',obs_mpb_v,obs_mpb_t]
        seadata['al']=['AL (nT)',sml,supermag_times]

        ylabel,data,times=seadata[var]

        artists,labels=plot_onset_sea(obs_signatures,obs_threshold,data,times,ylabel,ax,signature_types=signature_types)

    else:

        names=[runprops['name'] for runprops in run_properties]
        runprops=run_properties[names.index(run_name)]


        run_signatures=get_model_signature_lists(runprops,datadir=datadir)

        from spacepy import datamodel as dm
        auroral_inds=dm.fromHDF5(os.path.join(datadir,runprops['name'].replace('/','').replace(' ','_')+'_auroral_inds.h5'))
        al_time=[datetime(2005,1,1,tzinfo=UTC)+timedelta(seconds=60*m) for m in range(0,1440*31)]

        #try:
        #    mpbdata=loadmat(os.path.join(datadir,'John Haiducek - '+runprops['name'].replace('/','').replace(' ','_')+'_mag_grid_lat=33_mpb.mat'))
        #except:
        #    raise

        #mpb_t=[datetime(2005,1,1,tzinfo=UTC)+timedelta(seconds=m*60) for m in range(0,31*24*60)]
        #mpb_v=mpbdata['mpb']
        mpb_t,mpb_v=parse_index(os.path.join(datadir,'mpb_index.txt'))

        seadata['MPB']=['MPB ($nT^4$)',mpb_v,mpb_t]
        seadata['al']=['AL (nT)',auroral_inds['AL'],al_time]

        ylabel,data,times=seadata[var]
        artists,labels=plot_onset_sea(run_signatures,model_threshold,data,times,ylabel,ax,signature_types=signature_types)
    return artists,labels

def plot_all_all_tiled_sea(signature_types=signature_types):
    from matplotlib.gridspec import GridSpec
    fig=plt.figure(figsize=[5.5,3.9])
    varlist=['bz','al','MPB']
    gs=GridSpec(len(varlist),len(run_properties)+1,hspace=0,right=0.98,top=0.95,wspace=0,left=0.12,bottom=0.12)
    axes=[]
    run_names=['obs']+[runprops['name'] for runprops in run_properties]
    
    for i in range(len(varlist)):
        axes.append([])
        for j in range(len(run_names)):
            if j>0:
                ax_kwargs={'sharey':axes[i][0]}
            else:
                ax_kwargs={}
            ax=fig.add_subplot(gs[i,j],**ax_kwargs)
            axes[i].append(ax)

            var=varlist[i]
            run_name=run_names[j]
            artists,labels=plot_sea_onset_comparison(run_name,var,ax,signature_types=signature_types)
            ylabel,data,times=seadata[var]
            if j==0:
                ax.set_ylabel(ylabel)
            else:
                plt.setp(ax.get_yticklabels(),visible=False)
                ax.set_ylabel('')
            if i==len(varlist)-1:
                ax.set_xlabel('Time since\nonset (h)')
            else:
                plt.setp(ax.get_xticklabels(),visible=False)

            ax.yaxis.set_major_locator(plt.MaxNLocator(4))
                
            ax.tick_params('x',which='both',direction='inout',top=True)
            ax.tick_params('y',which='both',direction='inout',top=True)

            if i==0:
                if run_name=='obs':
                    ax.set_title('Observations')
                else:
                    if len(run_properties)>1:
                        ax.set_title(run_name)
                    else:
                        ax.set_title('MHD')

    #axes[0][0].set_ylim(-6.5,6.5)
    #axes[1][0].set_ylim(0,50)
    #axes[2][0].set_ylim(-650,0)
    #axes[3][0].set_ylim(0,3500)
            
    fig.canvas.draw()

    for i in range(len(varlist)):
        for j in range(len(run_names)):
            ax=axes[i][j]
            remove_overhanging_labels(ax,fig,'x')
            remove_overhanging_labels(ax,fig,'y')

    if len(signature_types)>1:
        axes[2][0].legend(artists,labels,loc='best')
    return fig

if __name__=='__main__':
    fig=plot_all_all_tiled_sea()
    fig.savefig('all_all_tiled_onsetcomp_sea.svg')
