import unittest
from math import log10,floor
import re

def latex_format_int(n):
    try:
        return str(int(n))
    except:
        return '-'

def guess_precision(n,uncert,uncert_precision=1):
    # Base-10 exponent of the value
    if abs(n)>0:
        exp_val=int(floor(log10(abs(n))))
    else:
        exp_val=0

    try:
        # Get the base-10 exponent of the error
        exp_err=int(floor(log10(abs(uncert))))
    except:

        # Default precision
        p=3
            
    else:
        # Calculate precision
        p=max(exp_val-exp_err+uncert_precision,1)

    return p

def latex_format_number(n,uncert=None,exp_lower=1e-3,exp_upper=1e4,precision='auto',uncert_precision=1,show_uncert=True,overline=False,extra_digits=0):

    try:
        int(n)
    except (ValueError,TypeError):
        return '-'

    # Base-10 exponent of the value
    if abs(n)>0:
        exp_val=int(floor(log10(abs(n))))
    else:
        exp_val=0

    try:
        nuncert=len(uncert)
    except:
        nuncert=1
    else:
        assert nuncert<=2
        assert nuncert>0
        if nuncert==2:
            uncert_max,uncert_min=uncert
            uncert=min(abs(uncert_min),abs(uncert_max))
        else:
            uncert=uncert[0]
    if precision=='auto':
        p=guess_precision(n,uncert,uncert_precision)
    else:
        try:
            p=int(precision)
        except:
            raise ValueError('Precision must be a number or ''auto ''.')
        
        assert p>0
        
    if uncert==None or show_uncert==False:
        # Determine whether format should be exponential or not, and compute number of decimal places
        if(abs(n)>=exp_upper or abs(n)<exp_lower and n!=0):
            format_type='e'
            d=p-1
        else:
            format_type='f'

            # Determine number of decimal places
            d=max(p-exp_val+extra_digits-1,0)

            # Round off the insignificant digits
            n=round(n/pow(10,exp_val-(p+extra_digits)+1))*pow(10,exp_val-(p+extra_digits)+1)

        # Format the number as a string
        format_string='{{0:0.{0:d}{1}}}'.format(d,format_type)
        s=format_string.format(n)

        if overline:
            # Draw a bar over the last significant digit
            if extra_digits:
                s=s[:-extra_digits-1]+'\\overline{'+s[-extra_digits-1]+'}'+s[-extra_digits:]
            else:
                s=s[:-1]+'\\overline{'+s[-1]+'}'

        # Format exponential using LaTeX syntax
        matchstr=r'e(|-)?[+0]*([\d]+)'
        s=re.sub(matchstr,r'\\times10^{\1\2}',s)

        return s
    else:
        if nuncert==1:
            return "{0:s}\pm{1:s}".format(latex_format_number(n,exp_lower=exp_lower,exp_upper=exp_upper,precision=p,overline=overline,extra_digits=extra_digits),latex_format_number(uncert,exp_lower=exp_lower,exp_upper=exp_upper,precision=uncert_precision))
        else:
            return "{0:s}[+{1:s},-{2:s}]".format(
                latex_format_number(n,exp_lower=exp_lower,exp_upper=exp_upper,precision=p,overline=overline,extra_digits=extra_digits),
                latex_format_number(uncert_max,exp_lower=exp_lower,exp_upper=exp_upper,precision=uncert_precision),
                latex_format_number(uncert_min,exp_lower=exp_lower,exp_upper=exp_upper,precision=uncert_precision),
            )

class test_latex_format_number(unittest.TestCase):

    def test_latex_format_number(self):
        self.assertEqual(latex_format_number(1,0.1),'1.0\\pm0.1')
        self.assertEqual(latex_format_number(1234,100),'1200\\pm100')
        self.assertEqual(latex_format_number(1e4,10),'1.000\\times10^{4}\\pm10')
        self.assertEqual(latex_format_number(1e5,1e4),'1.0\\times10^{5}\\pm1\\times10^{4}')
        self.assertEqual(latex_format_number(1e-3,1e-4),'0.0010\\pm1\\times10^{-4}')
        self.assertEqual(latex_format_number(1e-4,1e-5),'1.0\\times10^{-4}\\pm1\\times10^{-5}')
        self.assertEqual(latex_format_number(-1e-4,1e-5),'-1.0\\times10^{-4}\\pm1\\times10^{-5}')
        self.assertEqual(latex_format_number(-1e4,1e3),'-1.0\\times10^{4}\\pm1000')
        self.assertEqual(latex_format_number(1,0.11),'1.0\\pm0.1')
        self.assertEqual(latex_format_number(1,0.09),'1.00\\pm0.09')
        self.assertEqual(latex_format_number(1,2),'1\\pm2')
        self.assertEqual(latex_format_number(1,10),'1\\pm10')
        self.assertEqual(latex_format_number(0),'0.00')
        self.assertEqual(latex_format_number(0,(2,1)),'0[+2,-1]')
        self.assertEqual(latex_format_number(0.016,0.01,show_uncert=False,overline=True),'0.0\\overline{2}')
        self.assertEqual(latex_format_number(0.016,0.01,show_uncert=True,overline=True,extra_digits=1),'0.0\\overline{1}6\\pm0.01')
    
if __name__=='__main__':
    unittest.main()
