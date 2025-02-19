import sys
import os.path as osp

from copy import deepcopy
import datetime
import os
import pickle
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from multihist import Hist1d, Histdd
from tqdm.notebook import tqdm
import pandas as pd
from scipy import stats

import strax
import straxen

def plot_area(peak_basics,low=0,high=5,binning=500):
    p_area = Hist1d(peak_basics['area'], bins=(np.logspace(low, high, binning)))
    p_area.plot()
    plt.xlabel("peak area (PE)", ha='right', x=1)
    plt.ylabel("events", ha='right', y=1)
    plt.xscale('log')
    plt.yscale('log')
    
def plot_width(peak_basics,low=1,high=4,binning=500):
    p_width = Hist1d(peak_basics['range_50p_area'], bins=(np.logspace(low, high, binning)))
    p_width.plot()
    plt.xlabel("peak width 50% (ns)", ha='right', x=1)
    plt.ylabel("events", ha='right', y=1)
    plt.xscale('log')
    plt.yscale('log')
    
def plot_risetime(peak_basics,low=1,high=5,binning=500):
    rise_time = Hist1d(peak_basics['rise_time'], bins=(np.logspace(low, high, binning)))
    rise_time.plot()
    plt.xlabel("rise time (ns)", ha='right', x=1)
    plt.ylabel("events", ha='right', y=1)
    plt.xscale('log')
    
def plot_area_risetime(peak_basics,low=0,high=5,low2=1,high2=4,binning=500):
    ph = Histdd(peak_basics['area'], peak_basics['rise_time'],
                    bins=(np.logspace(low, high, binning), np.logspace(low2, high2, binning)))
    plt.figure(figsize=(12,6))
    ph.plot(log_scale=True, cblabel='events')
    plt.xlabel("peak area (PE)", ha='right', x=1)
    plt.ylabel("rise time (ns)", ha='right', y=1)
    plt.xscale('log')
    plt.yscale('log')
    
def plot_area_width(peak_basics,low=0,high=5,low2=1,high2=4,binning=500):
    ph50 = Histdd(peak_basics['area'], peak_basics['range_50p_area'],
                    bins=(np.logspace(low, high, binning), np.logspace(low2, high2, binning)))
    plt.figure(figsize=(12,6))
    ph50.plot(log_scale=True, cblabel='events')
    plt.xlabel("peak area (PE)", ha='right', x=1)
    plt.ylabel("peak width 50% (ns)", ha='right', y=1)
    plt.xscale('log')
    plt.yscale('log')

def plot_area_maxpmt(peak_basics,low=0,high=5,binning=500,binning2=200):
    phmax = Histdd(peak_basics['area'], peak_basics['max_pmt_area']/peak_basics['area']*100,
                    bins=(np.logspace(low, high, binning), np.linspace(0, 1, binning2)))
    plt.figure(figsize=(12,6))
    phmax.plot(log_scale=True, cblabel='events')
    plt.xlabel("peak area (PE)", ha='right', x=1)
    #plt.ylabel("max PMT area (PE)", ha='right', y=1)
    plt.ylabel("max PMT area fraction (%)", ha='right', y=1)
    plt.xscale('log')
    plt.yscale('log')

def plot_area_top(peak_basics,low=0,high=5,low2=-2,high2=0,binning=500,log=False):
    phmax = Histdd(peak_basics['area'], peak_basics['area_fraction_top'],
                    bins=(np.logspace(low, high, binning), np.logspace(low2, high2, binning)))
    plt.figure(figsize=(12,6))
    phmax.plot(log_scale=True, cblabel='events')
    plt.xlabel("peak area (PE)", ha='right', x=1)
    #plt.ylabel("max PMT area (PE)", ha='right', y=1)
    plt.ylabel("area fraction top", ha='right', y=1)
    plt.xscale('log')
    if (log): plt.yscale('log')
    
def plot_width_top(peak_basics,low=1,high=4,low2=0,high2=1,binning=500):
    phmax = Histdd(peak_basics['range_50p_area'], peak_basics['area_fraction_top'],
                    bins=(np.logspace(low, high, binning), np.linspace(low2, high2, binning)))
    plt.figure(figsize=(12,6))
    phmax.plot(log_scale=True, cblabel='events')
    plt.xlabel("peak width 50% (ns)", ha='right', x=1)
    plt.ylabel("area fraction top", ha='right', y=1)
    plt.xscale('log')

def rectangle(bounds1,bounds2,color):
    plt.gca().add_patch(matplotlib.patches.Rectangle((bounds1[0],bounds2[0]),
                                                     bounds1[1]-bounds1[0],
                                                     bounds2[1]-bounds2[0],
                                                     edgecolor=color,facecolor='none'))

def plot_waveforms(peaks,nn,arealow=2000,areahigh=1e4,xlimh=1000):
    dt = peaks['dt'][0]
    print('total number of records',peaks['data'].shape[0])
    dts = np.arange(0,peaks['data'].shape[1]*dt,dt)
    plt.figure(figsize=(20,5))
    for i in range(nn):
        if (peaks['area'][i]>arealow) & (peaks['area'][i]<areahigh):
            plt.plot(dts,peaks['data'][i])#,drawstyle='steps')
        #plt.axvline(peaks['center_time'][i]-peaks['time'][i], linestyle="-",
        #            color = plt.gca().lines[-1].get_color())
    plt.xlabel("time (ns)", ha='right', x=1)
    plt.ylabel(f"ADC", ha='right', y=1)
    plt.xlim(0,xlimh)

def plotwf(peaks,nn,area_cut,width_cut,color='b'):
    peaks=peaks[(peaks['area']<area_cut[1])&(peaks['area']>area_cut[0])&
                     (peaks['range_50p_area']<width_cut[1])&
                      (peaks['range_50p_area']>width_cut[0])]
    dt = peaks['dt'][0]
    print('total number of records',peaks['data'].shape[0])
    dts = np.arange(0,peaks['data'].shape[1]*dt,dt)
    fig, axs = plt.subplots(nn,figsize=(12,8))
    for i in range(nn):
        axs[i].plot(dts,peaks['data'][i],drawstyle='steps',color=color)
        axs[i].set_xlabel("time (ns)", ha='right', x=1)
        axs[i].set_ylabel(f"ADC", ha='right', y=1)
    
def events_vs_time(runs,etype,area_bounds,width_bounds):
    run_n, events = [], np.zeros(len(runs))
    for i in range(len(runs)):
        run_name = runs.iloc[i]['name']
        peaks = st.get_array(run_name,'peak_basics',seconds_range=(0,30),
                            selection_str=(f'(n_channels>3)&(area>{area_bounds[0]})&(area<{area_bounds[1]})&(range_50p_area>{width_bounds[0]})&(range_50p_area>{width_bounds[0]})'))
        #peaks[(peaks['area']>area_bounds[0]) & (peaks['area']<area_bounds[1]) &
        #      (peaks['range_50p_area']>width_bounds[0])&
        #      (peaks['range_50p_area']<width_bounds[1])]
        #for k in range(len(peak_s2)):
        #area_s2.append(peak_s2['area'][k]) 
        p_area = Hist1d(peaks['area'], bins=(np.logspace(3, 5.1, 200)))
        #plt.figure(1)
        #p_area.plot()
        #plt.xlabel("peak area (PE)", ha='right', x=1)
        #plt.ylabel("events", ha='right', y=1)
        #plt.xscale('log')
        #plt.yscale('log')
        p_area = np.array(p_area)
        run_n.append(runs.iloc[i]['number'])
        events[i] = p_area.sum()
    #plt.figure(2)
    plt.plot(run_n,events,'o')
    plt.xlabel('run', ha='right', x=1)
    plt.ylabel(f'S{etype}-like events', ha='right', y=1)
    
def f90(peaks,low=0,high=5,low2=-3,high2=0,binning=500):
    f90 = np.zeros(len(peaks))
    for i in range(len(peaks)):
        f90[i] = peaks['data'][i][:9].sum()/peaks['data'][i][:].sum() 
    ph90 = Histdd(peaks['area'], f90,
                  bins=(np.logspace(low, high, binning), np.logspace(low2, high2, binning)))
    plt.figure(figsize=(12,6))
    ph90.plot(log_scale=True, cblabel='events')
    plt.xlabel("peak area (PE)", ha='right', x=1)
    plt.ylabel("F90", ha='right', y=1)
    plt.xscale('log')
    plt.yscale('log')
    return f90


def select_data(st, run_id):
    area = []
    width = []
    rise_time = []
    max_pmt_area = []
    area_top = []
    time = []
    channel = []
    r_data = pd.DataFrame(columns=['area','range_50p_area','rise_time',
                                   'max_pmt_area','area_fraction_top','time','channel'])
    
    for chunk in st.get_iter(run_id, ['peaks','peak_basics'], max_workers=10,
                         keep_columns = ('area', 'range_50p_area','rise_time',
                                         'max_pmt_area','area_fraction_top','time',
                                         'channel'), seconds_range=(0,30)):
        area = np.append(area,chunk.data['area'])
        width = np.append(width,chunk.data['range_50p_area'])
        rise_time = np.append(rise_time,chunk.data['rise_time'])
        max_pmt_area = np.append(max_pmt_area,chunk.data['max_pmt_area'])
        area_top = np.append(area_top,chunk.data['area_fraction_top'])
        time = np.append(time,chunk.data['time']) 
        channel = np.append(channel,chunk.data['channel'])
    """"""
    r_data['area'] = area
    r_data['range_50p_area'] = width
    r_data['rise_time'] = rise_time
    r_data['max_pmt_area'] = max_pmt_area
    r_data['area_fraction_top'] = area_top
    r_data['time'] = time
    r_data['channel'] = channel
    """"""
    return r_data




def plot_some_peaks(peaks, max_plots = 5, randomize = False):
    """Plot the first peaks in the peaks collection (max number of 5 by default)"""
    if randomize:
        # This randomly takes max_plots in the range (0, len(peaks)). Plot these indices
        indices = np.random.randint(0, len(peaks), max_plots)
    else:
        # Just take the first max_plots peaks in the data
        indices = range(max_plots)
    for i in indices:
        p = peaks[i]
        start, stop = p['time'], p['endtime']
        st.plot_peaks(run_id,
                      time_range = (start, stop))
        plt.title(f'S{p["type"]} of ~{int(p["area"])} PE (width {int(p["range_50p_area"])} ns)\n'
                  f'detected by {p["n_channels"]} PMTs at:\n'
                  f'{datetime.datetime.fromtimestamp(start/1e9).isoformat()}')  # should in s not ns hence /1e9
        plt.show()