from plot_score_v_count_ratio import plot_skill_score_v_count_ratio, run_properties

if __name__=='__main__':
    from sys import argv
    
    namestr='Hi-res_w_RCM'

    namestrs=[runprops['name'].replace('/','').replace(' ','_') for runprops in run_properties]
    runprops=run_properties[namestrs.index(namestr)]

    fig=plot_skill_score_v_count_ratio(runprops,obs_thresholds=[2.5],show_circle=True,skip_styles=2)
    fig.savefig('score_v_count_ratio_build1.svg')

