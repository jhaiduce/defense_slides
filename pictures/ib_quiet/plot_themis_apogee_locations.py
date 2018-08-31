import matplotlib
matplotlib.use('Agg')
from ib_utils.timeseries import interp_timeseries, UTC
from ib_utils.data_loaders import load_noaaconj_quiet,get_orbit
from matplotlib import pyplot as plt
import numpy as np
from datetime import datetime, tzinfo

from decouple import config
datadir=config('DATADIR')

matplotlib.rcParams['legend.fontsize']='medium'
matplotlib.rcParams['mathtext.default']='regular'
matplotlib.rcParams['font.size']=8

def add_planet(ax, rad=1.0, ang=0.0, **extra_kwargs):
    '''
    Creates a circle of radius=self.attrs['rbody'] and returns the
    MatPlotLib Ellipse patch object for plotting.  If an axis is specified
    using the "ax" keyword, the patch is added to the plot.

    Unlike the add_body method, the circle is colored half white (dayside)
    and half black (nightside) to coincide with the direction of the 
    sun. Additionally, because the size of the planet is not intrinsically
    known to the MHD file, the kwarg "rad", defaulting to 1.0, sets the
    size of the planet.

    Extra keywords are handed to the Ellipse generator function.
    '''

    from matplotlib.patches import Circle, Wedge

    body = Circle((0,0), rad, fc='w', ec='k', zorder=1000, **extra_kwargs)
    arch = Wedge((0,0), rad, 90.+ang, -90.+ang, fc='k', 
                 zorder=1001, **extra_kwargs)

    ax.add_artist(body)
    ax.add_artist(arch)

    return body, arch

edgecolor='k'

fig=plt.figure(figsize=(4.5,5.5))
ax_time=fig.add_axes([0.14,0.4,0.85,0.57])
ax_xy=fig.add_axes([0.14,0.05,0.35,0.25])
ax_yz=fig.add_axes([0.56,0.05,0.35,0.25])

satnames, times, coords, MLTs, maglats,maglons,thetas,phis = load_noaaconj_quiet(datadir=datadir)

tail_sat_colors={
    'goes11':'DarkViolet',
    'goes12':'DarkSalmon',
    'goes13':'Brown',
    'goes14':'Chocolate',
    'goes15':'Coral',
    'themisa':'DarkCyan',
    'themisb':'MediumBlue',
    'themisc':'Aqua',
    'themisd':'DarkOrange',
    'themise':'DarkViolet',
}

tail_sat_shapes={
    'goes11':'>',
    'goes12':'<',
    'goes13':'v',
    'goes14':'^',
    'goes15':'s',
    'themisa':'p',
    'themisb':'o',
    'themisc':'8',
    'themisd':'d',
    'themise':'h',
}

label_offsets_xy={
    'themisa':(0,5),
    'themisd':(-10,5),
    'themise':(-10,5),
}

label_offsets_yz={
    'themisa':(-10,5),
    'themisd':(-10,5),
    'themise':(-10,5),
}

#for satname in ['themisa','themisd','themisd']:
for satname in tail_sat_colors.keys():
    if satname in ('themisb','themisc'): continue
    if satname.startswith('goes'): continue
    tstart=datetime(2009,2,13,tzinfo=UTC)
    tend=datetime(2009,2,14,tzinfo=UTC)
    orbit_t,x,y,z=get_orbit(satname.lower(),tstart,tend)
    r=np.sqrt(x**2+y**2+z**2)
    t=datetime(2009,2,13,4,22,tzinfo=UTC)
    xt=interp_timeseries(x,orbit_t,[t])[0]
    yt=interp_timeseries(y,orbit_t,[t])[0]
    zt=interp_timeseries(z,orbit_t,[t])[0]
    orbit_t=[time.replace(tzinfo=None) for time in orbit_t]

    markersize=7
    edgecolor='w'

    ax_xy.plot(yt,xt,linestyle='',marker=tail_sat_shapes[satname],markersize=markersize,color=tail_sat_colors[satname],label=satname,markeredgecolor=edgecolor)
    ax_yz.plot(yt,zt,linestyle='',marker=tail_sat_shapes[satname],markersize=markersize,color=tail_sat_colors[satname],label=satname,markeredgecolor=edgecolor)
    ax_xy.annotate('THM-'+satname[-1],xy=(yt,xt),xytext=label_offsets_xy.get(satname,(-10,5)),textcoords='offset points')
    ax_yz.annotate('THM-'+satname[-1],xy=(yt,zt),xytext=label_offsets_yz.get(satname,(-10,5)),textcoords='offset points')

    if satname in ('themisa',):
        x=interp_timeseries(x,orbit_t,times)
        y=interp_timeseries(y,orbit_t,times)

        ax_time.plot(y,x,linestyle='',marker=tail_sat_shapes[satname],markersize=markersize,color=tail_sat_colors[satname],label=satname,markeredgecolor=edgecolor)
        ax_time.plot([-1,0,1,0],[0,1,0,-1],linestyle='')
    
ax_time.set_aspect(1,adjustable='datalim')
ax_xy.set_aspect(1,adjustable='datalim')
ax_yz.set_aspect(1,adjustable='datalim')
ax_xy.axis('off')
ax_yz.axis('off')

for ax,orig in (ax_xy,(1,0)), (ax_yz,(1,1)):

    lw=2
    hw=0.1
    hl=0.11
    ohg=0
    yhw=hw
    yhl=hl
    arrowprops=dict(arrowstyle='<|-,head_width=0.5,head_length=1',color='k',linewidth=2,shrinkB=0)

    # draw x and y axis
    ax.annotate('',xy=orig,xytext=( 1-orig[0], orig[1]),
                arrowprops=arrowprops,
                clip_on = False, xycoords=ax.transAxes,textcoords=ax.transAxes)

    ax.annotate('',xy=orig,xytext=( orig[0], 1-orig[1]),
                arrowprops=arrowprops,
                clip_on = False, xycoords=ax.transAxes,textcoords=ax.transAxes)


ax_xy.annotate('',xy=(0.1,-9),xytext=(0.1,-10),
               xycoords='data',textcoords='data',
               clip_on=False,annotation_clip=False,
               arrowprops=dict(arrowstyle='|-|',linewidth=1,color='k'))
#ax_yz.annotate('',xy=(-0.9,0.5),xytext=(-0.9,1),
#               xycoords='data',textcoords='data',
#               clip_on=False,annotation_clip=False,
#               arrowprops=dict(arrowstyle='|-|',linewidth=1,color='k'))
ax_xy.text(0.2,-9.5,'1 Re',horizontalalignment='right')
ax_xy.text(0.4,-0.1,'Y GSM',transform=ax_xy.transAxes)
ax_xy.text(1.03,0.5,'X GSM',transform=ax_xy.transAxes,rotation=90)
ax_yz.text(0.4,1.03,'Y GSM',transform=ax_yz.transAxes)
ax_yz.text(1.03,0.5,'Z GSM',transform=ax_yz.transAxes,rotation=90)
ax_time.text(0.9,0.9,'a',transform=ax_time.transAxes,fontweight='bold',fontsize=12)
ax_xy.text(0.15,0.1,'b',transform=ax_xy.transAxes,fontweight='bold',fontsize=14)
ax_yz.text(0.1,0.1,'c',transform=ax_yz.transAxes,fontweight='bold',fontsize=14)

ax_time.axvline(0,linestyle='--',color='k')
ax_time.axhline(0,linestyle='--',color='k')

ax_xy.set_xlim(0,-2)
ax_yz.set_xlim(0,-2)

plt.draw()

x0,y0,width,height=ax_xy.get_position().bounds
aspect=width/height

xmin,xmax=ax_xy.get_ylim()
deltaX=xmax-xmin
zmin,zmax=ax_yz.get_ylim()
deltaZ=zmax-zmin

deltaY=1.0
Y0=-0.6
X0=-11.8
Z0=0.5

ax_xy.set_aspect(1,adjustable='datalim')
ax_yz.set_aspect(1,adjustable='datalim')

ax_time.set_xlabel('Y GSM (Re)')
ax_time.set_ylabel('X GSM (Re)')
ax_time.set_xlim(4,-8)
add_planet(ax_time,ang=90)
ax_time.legend(loc='lower left',numpoints=1,handlelength=0.3)
plt.savefig('themis_apogee_locations.svg')
