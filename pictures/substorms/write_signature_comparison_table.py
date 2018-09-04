from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from substorm_utils.bin_listings import find_substorms_convolution, convolved_substorm_scores, filter_onsets, make_grid
from datetime import datetime, timedelta
from substorm_utils.forecast_stats import get_counts,hit_rate,false_alarm_rate, heidke_skill, heidke_ci, metric_ci
from latex_format_number import latex_format_number, latex_format_int, guess_precision
from cache_decorator import cache_result
import numpy as np

from decouple import config
datadir=config('DATADIR')

model_threshold=2.5
obs_threshold=2.5

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

signature_type_labels={
    'All':'All',
    'AL':'AL',
    'image':'IMAGE/FUV',
    'plasmoids':'Plasmoids',
    'dipolarizations':'Dipolarizations',
    'epdata':'LANL EP data',
    'MPB':'MPB'
}

@cache_result(clear=False)
def get_table_data(table_signatures,nsamples=32000):

    obs_signatures=get_obs_signature_lists(datadir=datadir)
    obs_substorms=find_substorms_convolution(obs_signatures,obs_threshold)

    table_data=[]

    for runprops in run_properties:
        table_data.append([])

        run_signatures=get_model_signature_lists(runprops,datadir=datadir)
        for signature in table_signatures:
            if signature=='All':
                signature_run_substorms=find_substorms_convolution(run_signatures,model_threshold)
                signature_obs_substorms=obs_substorms
            else:
                if signature in run_signatures:
                    signature_run_substorms,keys=make_grid({signature:run_signatures[signature]})
                    signature_run_substorms=signature_run_substorms.flatten()
                if signature in obs_signatures:
                    signature_obs_substorms,keys=make_grid({signature:obs_signatures[signature]})
                    signature_obs_substorms=signature_obs_substorms.flatten()

            if signature in obs_signatures and signature in run_signatures or signature=='All':
                counts=get_counts(signature_run_substorms,signature_obs_substorms)
                true_positive,false_positive,false_negative,true_negative=counts
                obs_total=true_positive+false_negative
                run_total=true_positive+false_positive
                skill=heidke_skill(*counts)
                skill_ci=heidke_ci(signature_run_substorms,signature_obs_substorms,nsamples)
                signature_hit_rate=hit_rate(*counts)
                signature_hit_rate_ci=metric_ci(signature_run_substorms,signature_obs_substorms,hit_rate,nsamples)
                signature_false_alarm_rate=false_alarm_rate(*counts)
                signature_false_alarm_rate_ci=metric_ci(signature_run_substorms,signature_obs_substorms,false_alarm_rate,nsamples)
            else:
                if signature in run_signatures:
                    run_total=np.sum(signature_run_substorms)
                else:
                    run_total=None
                if signature in obs_signatures:
                    obs_total=np.sum(signature_obs_substorms)
                else:
                    obs_total=None
                skill=None
                skill_ci=(None,None)
                signature_hit_rate=None
                signature_hit_rate_ci=(None,None)
                signature_false_alarm_rate=None
                signature_false_alarm_rate_ci=(None,None)
                
            all_counts=get_counts(signature_run_substorms,obs_substorms)
            all_skill=heidke_skill(*all_counts)
            all_skill_ci=heidke_ci(signature_run_substorms,obs_substorms,nsamples)
            all_hit_rate=hit_rate(*all_counts)
            all_hit_rate_ci=metric_ci(signature_run_substorms,obs_substorms,hit_rate,nsamples)
            all_false_alarm_rate=false_alarm_rate(*all_counts)
            all_false_alarm_rate_ci=metric_ci(signature_run_substorms,obs_substorms,false_alarm_rate,nsamples)

            table_data[-1].append([signature,run_total,obs_total,skill,skill_ci,signature_hit_rate,signature_hit_rate_ci,signature_false_alarm_rate,signature_false_alarm_rate_ci,all_skill,all_skill_ci,all_hit_rate,all_hit_rate_ci,all_false_alarm_rate,all_false_alarm_rate_ci])

    return table_data

def make_table_string(table_signatures):

    table_data=get_table_data(table_signatures)

    run_names=[runprops['name'] for runprops in run_properties]

    texstr='<table>\n'
    texstr+='<thead>\n'
    texstr+='<tr><td/><th>SWMF events</th><th>Obs. events</th>\n'
    texstr+='</tr></thead>\n'

    def ci_to_err(value,ci):

        if ci[0] is not None and ci[0]!=0 and ci[1]!=0:
            return [ci[1]-value,value-ci[0]]
        else:
            return None

    def format_ci(ci):
        if ci[0] is None or ci[0]==ci[1]:
            return ''
        else:
            mid=0.5*(ci[0]+ci[1])
            p=guess_precision(mid,ci[1]-mid)
            return '[{0},{1}]'.format(latex_format_number(ci[0],precision=p),
                                latex_format_number(ci[1],precision=p))

    for i,(run_name,run_data) in enumerate(zip(run_names,table_data)):
        if len(run_names)>1:
            texstr+=r'&\multicolumn{{6}}{{c}}{{\textit{{{0}}}}}\\'.format(run_name)+'\n'
        for [signature,run_total,obs_total,skill,skill_ci,signature_hit_rate,signature_hit_rate_ci,signature_false_alarm_rate,signature_false_alarm_rate_ci,all_skill,all_skill_ci,all_hit_rate,all_hit_rate_ci,all_false_alarm_rate,all_false_alarm_rate_ci] in run_data:

            skill_err=ci_to_err(skill,skill_ci)
            all_skill_err=ci_to_err(all_skill,all_skill_ci)
            signature_hit_rate_err=ci_to_err(signature_hit_rate,signature_false_alarm_rate_ci)
            signature_false_alarm_rate_err=ci_to_err(signature_false_alarm_rate,signature_false_alarm_rate_ci)

            line='<tr class="signature_{signature_id}"><th scope="row">{signature}</th><td>{run_total}</td><td>{obs_total}</td></tr>'.format(
                signature_id=signature,
                signature=signature_type_labels[signature],
                run_total=latex_format_int(run_total),
                obs_total=latex_format_int(obs_total),
                sig_skill=latex_format_number(skill,skill_err,show_uncert=False,overline=True,extra_digits=1),
                sig_skill_ci=format_ci(skill_ci),
                all_skill=latex_format_number(all_skill,all_skill_err,show_uncert=False,overline=True,extra_digits=1),
                all_skill_ci=format_ci(all_skill_ci),
                sig_hit_rate=latex_format_number(signature_hit_rate,signature_hit_rate_err,show_uncert=False,overline=True,extra_digits=1),
                sig_false_alarm_rate=latex_format_number(signature_false_alarm_rate,signature_false_alarm_rate_err,show_uncert=False,overline=True,extra_digits=1),
            )+'\n'
            import re
            line=re.sub(r'\\overline\{(\d+)\}',r'<span style="text-decoration:overline">\1</span>',line)
            texstr+=line
    texstr+='</table>\n'
    return texstr

if __name__=='__main__':
    table_signatures=['AL','MPB','dipolarizations','image','epdata','plasmoids','All']
    texstr=make_table_string(table_signatures)
    with open('signature_comparison_table.html','w') as fh:
        fh.write(texstr)
    

