from substorm_utils.signature_lists import get_model_signature_lists, get_obs_signature_lists
from plot_substorm_convolution import make_convolution_figure, datadir
from datetime import datetime, timedelta

if __name__=='__main__':
    obs_signatures=get_obs_signature_lists(datadir=datadir)
    threshold=2.5
    tstart=datetime(2005,1,22)
    tend=datetime(2005,1,23)
    fig=make_convolution_figure(obs_signatures,threshold,tstart,tend,bandwidth=timedelta(minutes=10),show_onsets=False,show_threshold=False,show_all=True)
    fig.savefig('substorm_convolution_build2.svg')
