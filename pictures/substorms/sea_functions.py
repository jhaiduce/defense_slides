from spacepy.seapy import Sea
from cache_decorator import cache_result

@cache_result(clear=False)
def get_sea_curves(data,times,onsets,window=2.5,delta=1./60):
    mysea=Sea(data,times,onsets,window=2.5,delta=1./60)
    mysea.sea()

    return mysea.x,mysea.semedian,mysea.bound_low.ravel(),mysea.bound_high.ravel()
