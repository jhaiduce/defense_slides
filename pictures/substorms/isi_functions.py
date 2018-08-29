from scipy.stats import gaussian_kde
from substorm_utils.kde import get_kde_bootstrap
from cache_decorator import cache_result
import numpy as np

@cache_result()
def get_kde_cached(isi,bw,x):
    return gaussian_kde(isi,bw_method=bw)(x)


@cache_result()
def get_kde_ci(isi,bins,nsamples,bw):
    estimates=get_kde_bootstrap(isi,bins,nsamples,bw)
    ci=np.percentile(estimates,[2.5,50,97.5],axis=1)
    return ci

