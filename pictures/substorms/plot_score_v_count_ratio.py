from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from substorm_utils.bin_listings import find_substorms_convolution, convolved_substorm_scores
from datetime import datetime, timedelta
from substorm_utils.forecast_stats import get_counts,hit_rate,false_alarm_rate, heidke_skill, heidke_ci
import numpy as np
from matplotlib import pyplot as plt
from decouple import config
import matplotlib
from plot_roc_curves import get_sweep_substorm_bins

matplotlib.rcParams['font.size']=8

matplotlib.rcParams['lines.linewidth']=1
matplotlib.rcParams['lines.markersize']=4

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

def plot_skill_score_v_count_ratio(runprops,obs_thresholds=None,model_thresholds=None,skip_styles=0,show_circle=True):
    sweep_shapes=['o','s','v','d','^','>']

    run_signatures=get_model_signature_lists(runprops,datadir=datadir)
    obs_thresholds,model_thresholds,substorm_bins=get_sweep_substorm_bins(obs_signatures,run_signatures,obs_thresholds=obs_thresholds,model_thresholds=model_thresholds)
    true_positive,false_positive,false_negative,true_negative=get_counts(substorm_bins[:,:,0,:],substorm_bins[:,:,1,:],axis=2)



    hit_rates=hit_rate(true_positive,false_positive,false_negative,true_negative)
    false_alarm_rates=false_alarm_rate(true_positive,false_positive,false_negative,true_negative)

    total_model_substorms=(true_positive+false_positive).astype(int)
    total_obs_substorms=(true_positive+false_negative).astype(int)

    skillscores=heidke_skill(true_positive,false_positive,false_negative,true_negative)

    skillscore_ci_lower,skillscore_ci_upper=heidke_ci(substorm_bins[:,:,0,:],substorm_bins[:,:,1,:],axis=2)
    skillscore_err_upper=skillscore_ci_upper-skillscores
    skillscore_err_lower=-(skillscore_ci_lower-skillscores)

    fig=plt.figure(figsize=[5.5,3.5])
    lines=[]

    for i in range(skip_styles):
        plt.plot([],[])

    for i in range(total_obs_substorms.shape[0]):
        if obs_thresholds[i]==2.5:
            plot_kwargs={
                'linewidth':2.5,
                'markersize':8,
                'zorder':10
            }
        else:
            plot_kwargs={}
        line,caps,bars=plt.errorbar(total_model_substorms[i].astype(float)/total_obs_substorms[i],skillscores[i],[skillscore_err_upper[i],skillscore_err_lower[i]],linestyle='',marker=sweep_shapes[i+skip_styles],**plot_kwargs)
        lines.append(line)

    if show_circle:
        i=np.where(np.array(obs_thresholds)==2.5)
        j=np.where(np.array(model_thresholds)==2.5)
        plt.plot(total_model_substorms[i,j].astype(float)/total_obs_substorms[i,j],skillscores[i,j],marker='o',markersize=14,markerfacecolor='none',zorder=15,markeredgecolor='k',markeredgewidth=2)
        
    labels=['Obs. threshold={0:0.1f} ({1:d} events)'.format(obs_thresholds[i],total_obs_substorms[i,0]) for i in range(len(lines))]
    plt.legend(lines,labels,loc='upper left')
    plt.xscale('log')
    plt.xlabel('$n_{model}/n_{obs}$')
    plt.ylabel('Heidke skill score')
    plt.axvline(1,color='k',alpha=0.5,zorder=-1)
    plt.axhline(0,color='k',alpha=0.5,zorder=-1)
    plt.xlim(0.003,40)
    plt.ylim(-0.03,0.3)
    plt.tight_layout()
    return fig

if __name__=='__main__':
    from sys import argv
    
    namestr='Hi-res_w_RCM'

    namestrs=[runprops['name'].replace('/','').replace(' ','_') for runprops in run_properties]
    runprops=run_properties[namestrs.index(namestr)]

    fig=plot_skill_score_v_count_ratio(runprops)
    fig.savefig('score_v_count_ratio.svg')
