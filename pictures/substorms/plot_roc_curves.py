from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from substorm_utils.bin_listings import find_substorms_convolution, convolved_substorm_scores
from datetime import datetime, timedelta
from substorm_utils.forecast_stats import get_counts,hit_rate,false_alarm_rate, heidke_skill, heidke_ci
import numpy as np
from matplotlib import pyplot as plt
from decouple import config
import matplotlib

matplotlib.rcParams['font.size']=8
matplotlib.rcParams['lines.linewidth']=1
matplotlib.rcParams['lines.markersize']=4


from cycler import cycler
matplotlib.rcParams['axes.prop_cycle']=(
    cycler('color',matplotlib.rcParams['axes.prop_cycle'].by_key()['color'])+
    cycler('marker',['o','s','v','d','^','>','*','.','h','p']))


datadir=config('DATADIR')

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

signature_filters=('AL','MPB','dipolarizations','plasmoids','epdata','image')
mandatory_signatures=()

model_threshold=2
obs_threshold=2

tstep=timedelta(0,1800)

obs_signatures=get_obs_signature_lists(datadir=datadir)

def get_sweep_substorm_bins(obs_signatures,run_signatures,convolution_resolution=timedelta(0,60),bandwidth=timedelta(0,10*60),obs_thresholds=None,model_thresholds=None):

    obs_scores,obs_tnums=convolved_substorm_scores(obs_signatures,resolution=convolution_resolution,bandwidth=bandwidth)
    substorms=[]
    
    if obs_thresholds is None:
        obs_thresholds=np.array([1,2.0,2.5,3])
        
    if model_thresholds is None:
        model_thresholds=np.linspace(0,7,15)

    for obs_threshold in obs_thresholds:
        substorms.append([])
        obs_substorms=find_substorms_convolution(obs_signatures,obs_threshold,convolution_resolution=convolution_resolution,bandwidth=bandwidth)
        for model_threshold in model_thresholds:
            run_substorms=find_substorms_convolution(run_signatures,model_threshold,convolution_resolution=convolution_resolution)
            substorms[-1].append([run_substorms,obs_substorms])
            
    return obs_thresholds,model_thresholds,np.array(substorms)

def plot_roc(runprops):
    run_signatures=get_model_signature_lists(runprops,datadir=datadir)
    obs_thresholds,model_thresholds,substorm_bins=get_sweep_substorm_bins(obs_signatures,run_signatures)
    true_positive,false_positive,false_negative,true_negative=get_counts(substorm_bins[:,:,0,:],substorm_bins[:,:,1,:],axis=2)

    hit_rates=hit_rate(true_positive,false_positive,false_negative,true_negative)
    false_alarm_rates=false_alarm_rate(true_positive,false_positive,false_negative,true_negative)

    total_model_substorms=(true_positive+false_positive).astype(int)
    total_obs_substorms=(true_positive+false_negative).astype(int)

    skillscores=heidke_skill(true_positive,false_positive,false_negative,true_negative)

    skillscore_ci_lower,skillscore_ci_upper=heidke_ci(substorm_bins[:,:,0,:],substorm_bins[:,:,1,:],axis=2)
    skillscore_err_upper=skillscore_ci_upper-skillscores
    skillscore_err_lower=-(skillscore_ci_lower-skillscores)

    fig=plt.figure(figsize=(4.5,3.5))
    plt.plot([0,1],color='k',marker='',alpha=0.6)
    lines=[]
    for i in range(false_alarm_rates.shape[0]):
        if obs_thresholds[i]==2.5:
            plot_kwargs={
                'linewidth':2.5,
                'markersize':8,
                'zorder':10
            }
        else:
            plot_kwargs={}

        lines.extend(plt.plot(false_alarm_rates[i],hit_rates[i],linestyle='-',clip_on=False,**plot_kwargs))

    i=np.where(obs_thresholds==2.5)
    j=np.where(model_thresholds==2.5)
    plt.plot(false_alarm_rates[i,j],hit_rates[i,j],marker='o',markersize=14,markerfacecolor='none',zorder=15,markeredgecolor='k',markeredgewidth=2)
    plt.xlabel('Probability of False Detection')
    plt.ylabel('Probability of Detection')
    labels=['Obs. threshold={0:0.1f} ({1:d})'.format(obs_thresholds[i],total_obs_substorms[i,0]) for i in range(len(lines))]
    plt.legend(lines,labels,loc='lower right')
    namestr=runprops['name'].replace('/','').replace(' ','_')
    plt.xlim(0,1)
    plt.ylim(0,1)
    plt.tight_layout()
    plt.savefig('roc_curves.svg')
    plt.close(fig)

if __name__=='__main__':
    namestr='Hi-res_w_RCM'

    namestrs=[runprops['name'].replace('/','').replace(' ','_') for runprops in run_properties]
    runprops=run_properties[namestrs.index(namestr)]

    plot_roc(runprops)
