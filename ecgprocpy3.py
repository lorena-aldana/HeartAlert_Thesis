from scipy import signal
import numpy as np
import matplotlib.pyplot as plt
import os

#Filter functions

def hilbert_transform(sigfiltered):
    "Hilbert transform function"
    ht = abs(signal.hilbert(sigfiltered))
    return ht

def bpIIR_filter(data,fc1,fc2, SR, order=4):
    '''This function filters (bandpass) the ECG signal
    and removes the DC component'''
    # Band pass filter design
    # Remove DC component
    sig_centered= data- np.mean(data) 
    sigarr = sig_centered
    cutoffpass = fc1 / (SR / 2.0);
    cutoffstop = fc2 / (SR / 2.0)  # 5.0 inferior cf, 70.0
    b, a = signal.iirfilter(order, [cutoffpass, cutoffstop], btype='bandpass', analog=False, ftype='butter')
    # Apply High pass filter
    signalfilt = signal.filtfilt(b, a, sigarr[:])
    return signalfilt

def hpIIR_filter(data, fc1, SR, order=2):
    '''High pass IIR filter design'''
    cutoffpass = fc1 / (SR / 2.0);
    b, a = signal.iirfilter(order, cutoffpass, btype='high', analog=False, ftype='butter')
    signalfilt = signal.filtfilt(b, a, data)
    return signalfilt

def lpIIR_filter(data, fc1, SR, order=4):
    '''Low pass filter design'''
    cutoffpass = fc1 / (SR / 2.0);
    b, a = signal.iirfilter(order, cutoffpass, btype='low', analog=False, ftype='butter')
    signalfilt = signal.filtfilt(b, a, data, method='gust')
    # signalfilt = signal.lfilter(b, a, data)
    return signalfilt

def bpFIR_filter(data, fil_len, fc1, fc2, SR):
    '''Band pass filter design'''
    cutoffpass = fc1 / (SR / 2.0);
    cutoffstop = fc2 / (SR / 2.0)
    b = signal.firwin(fil_len, [cutoffpass, cutoffstop], pass_zero=False, window='hamming')
    signalfilt = signal.lfilter(b,[1.0],data)
    return signalfilt


def filter_multi_channel(signal, sr=1000.0, fc1=0.5, fc2=50):
    '''This function filters an remove the DC component of a multichannel ECG signal'''
    channels = np.shape(signal)[1]
    filt_matrix = []
    for ch in range(channels):
        filtered = bpIIR_filter(signal[signal.columns[ch]], fc1, fc2, SR=sr)
        filt_matrix.append(filtered)
    return filt_matrix

#Amplitude scaling

def amplitude_scaling(data, SampleRate, db):
    """Function to perform amplitude scaling on real medical ECG data"""
    dcdata=data-np.mean(data)
    data=dcdata
    if db=='p': #Physionet Database
        factor= 1
        scaleddata=data*factor
    elif db=='m': #Mac200 Database
        factor= 0.00488 #in mV #Original value: 4.88e-6
        scaleddata=data*factor
    return scaleddata

#R peak detection functions

def R_peaks_detection_onelead(ampdata, timedata, thld):
    
    '''This function chooses one peak in the given time window.
    It is the main function in ecgprocpy3 for calculating R peaks'''

    detected_peaks=[]
    lastPeak = []
    above_threshold = False
    for x in range(len(ampdata)):
        last_above_thrld = above_threshold
        curValue = ampdata[x]
        if curValue > thld:
            above_threshold = True
        else:
            above_threshold = False

        if above_threshold == True:
            if len(lastPeak) == 0 or curValue > lastPeak[1]:
                lastPeak = [timedata[x], ampdata[x]]
        if last_above_thrld == True and above_threshold == False:
            detected_peaks.append(lastPeak)
            lastPeak = []

        last_above_thrld = above_threshold

    if len(detected_peaks)>0: #select max peak among peaks found
        peakamp,loc= max([(x[1], i) for i, x in enumerate(detected_peaks)])
        selectedpeak= detected_peaks[loc]
        return selectedpeak


def find_R_peaks_onechannel(sig, sr=1000.0, window=200, thpercentage = 0.70, fc1=0.5, fc2=40.0, plot = False):
    '''This function filters the signal, calculates the time stamps for the peaks function and find
    the R peaks in one ECG lead'''
    #Filter the signal
    sigf= bpIIR_filter(sig, fc1, fc2, SR=sr)
    #Hilbert transform
    ht = hilbert_transform(sigf)
    #Set threshold for peaks detection
    maxamp = np.max(ht)
    minamp = np.min(ht)
    thld = (np.abs(maxamp-minamp)*thpercentage) #Threshold is 75 of the amplitude in the signal
    #
    originalsigtoplot= sig 
    sig = ht #now the sig variable contains the hilbert transform 
    #Calculate time stamps
    tref=0.0
    tlist=[] #Initialize list for timestamps
    dtsamples = (1 / sr)  # Time between samples
    peaks=[]
    peaks_final_sel=[]
    size_an_window=window
    for count, element in enumerate(sig,1): # Start counting from 1
        if count % size_an_window == 0: 
            segment= sig[count-size_an_window:count] #Only calculate peaks of the first channel
            for x in range(len(segment)):  # Create time stamps accroding to sample rate
                tlist.append(tref)
                tref = tref + dtsamples
            times = tlist[len(tlist)-size_an_window:len(tlist)]
            peak_found=R_peaks_detection_onelead(segment, times, thld) #Calculate peaks in given lead
            peaks.append(peak_found)
    peaks_final_sel=[x for x in peaks if x is not None] #Time, amplitude

    if plot == True:
        plt.clf()
        xax = np.linspace(0, len(sig)/sr, len(sig))
        th_arr= len(xax) * [thld]
        #Plot hilbert transform:
        plt.plot(xax, sig)
        plt.plot(xax,th_arr, 'r')
        #Plot Original signal
        plt.plot(xax, originalsigtoplot, 'g', alpha= 0.25)
        for i in range(len(peaks_final_sel)):
            plt.plot(peaks_final_sel[i][0],peaks_final_sel[i][1], "*" )
        plt.xlabel('Time [s]')
        plt.ylabel ('Amplitude [mV]')

    return peaks_final_sel

def find_R_peaks_multi_channel(signal, sr=1000.0, window=200):
    '''This function calculates peaks of a multichannel ECG signal'''
    channels = np.shape(signal)[1]
#     print (channels)
    all_peaks_matrix=[]
    for ch in range(channels):
        rpks = find_R_peaks_onechannel(signal[signal.columns[ch]],sr, window)
        all_peaks_matrix.append(rpks)
    return all_peaks_matrix


def find_rr_peaks(peaks, strechfactor):
    """This function calculated the time difference between consecutive R peaks"""
    for x in range(len(peaks)):
        pks_loc = [x[0] * strechfactor for x in peaks]
        rr =  [a - b for a, b in zip(pks_loc[1:], pks_loc[:-1])]
    return rr

def hr(peaks, sr, N):
    '''Calculates the HR based every N peaks.
    At least N peaks are needed for the calculation.
    The first N values are equal to zero while there are enough peaks to calculate the heart rate'''
    HR = []
    for x in range(N):
        HR.append(0)
    for x in range(N, len(peaks)):
        pks_loc = [x[0] for x in peaks[x-N:x]]
        RRdeltas = [a - b for a, b in zip(pks_loc[1:], pks_loc[:-1])] 
        hrmean = np.mean(RRdeltas)
        HR.append(int(60 / hrmean))
    return HR


def update_thr(nmax, nmin, omax, omin):
    '''In a real-time ECG sonification implementation, this function updates the threshold for detecting R peaks'''
    maxbuf=[]
    minbuf=[]
    buf_ct=[]

    if nmax>omax:
        omax=nmax
    if nmin<omin:
        omin=nmin
    maxbuf.append(omax)
    minbuf.append(omin)
    buf_ct.append([omax,omin])
    if len(maxbuf)>5: #200 ms
        maxbuf.pop(0)
        minbuf.pop(0)
    mean_max_buf=np.mean(maxbuf)
    mean_min_buf=np.mean(minbuf)
    nnmax=omax
    nnmin=omin
    if len(buf_ct) > 5:
        up_flag=1 #update threshold every 5 ctcles of nSamples
    else:
        up_flag=0
    return nnmax, nnmin, mean_max_buf, mean_min_buf, up_flag


def seg_dur_for_analysis(dt, sr=1000.0):

    '''This function calculates the duration of half QRS complex, the total QRS complex, isoelectricity  
    and the PR segment based on the heart rate or time difference between consecutive peaks'''

    dtinsamples = dt*sr
    total_qrs_width = 1/10.0*(dtinsamples) #samples #QRS is aprox 1/10 of the RR
    QRSdur = (total_qrs_width/2) #samples
    qt_interval= (dtinsamples)/2.5 #samples #QT is aprox 2.5 of the RR according to pdf
    qtc=((qt_interval/sr)/np.cbrt(dt)*sr)  #The formula is in seconds, then to samples
    pr_int_dur=(dtinsamples)/6.25 
    iso_dur= (dtinsamples - qtc - pr_int_dur)  #iso_dur in samples
    # print (("qrs: %s, qtc: %s, isodur: %s, pr: %s")%(QRSdur, qtc, iso_dur, pr_int_dur))

    return int(QRSdur), int(qtc), int(iso_dur), int(pr_int_dur)

#ST elevation functions

def st_amplitude_one_lead(sig, sr=1000.0, window=200, thpercentage = 0.70, fc1=0.5, fc2= 50, accuracy= 0.0001, st_length = 50, longer_qrs = 0, plot = False):
    '''This function estimates the ST elevation in each heart beat based on the amplitude difference between
    J point and TP segment'''
    warning_flag = False
    first_deriv= np.gradient(sig) 
    jpoints = []
    jpoint_search_flag = 0 
    tppoints = []
    tpseg_searchflag = 0
    cur_hbeat = 0
    rrdeltas = []
    hr = []
    #Starting segments reference values for a 60 BPM
    qrs_width = 50
    qtc_width = 400
    iso_dur = 50

    #Filter signal
    sigfil = bpIIR_filter(sig, fc1, fc2, sr)
    peaks = find_R_peaks_onechannel(sig, sr, window, thpercentage, fc1, fc2) #To avoid dobule filtering in the peaks detection
    sig = sigfil #Filetered signal for the plotting, not for the peaks

    #Determine dt in each heart beat
    for pks in range(1, len(peaks)):
        rri = peaks[pks][0] - peaks[pks-1][0]
        rrdeltas.append(rri)
        hr.append(60/rri)

    #Find J point and TP segment
    for sig_idx, val in enumerate (range(len(sig))):
        #If the maximum number of peaks has been reached
        if cur_hbeat < len(peaks):
            #Find sample where the peaks are
            if sig_idx == int(peaks[cur_hbeat][0]*sr):
                #Calculate segments durations
                if cur_hbeat < len(peaks)-1: #update segment values, there is one dt value less than peaks
                    qrs_width, qtc_width, iso_dur, _ = seg_dur_for_analysis(rrdeltas[cur_hbeat], sr)
                #Calculate J point
                jpoint_search_flag = 1
                search_start = int(sig_idx+qrs_width+longer_qrs) #Start is a peak
                search_end = int(sig_idx+(qtc_width/2.0)) #End is half of qtc
                for der_idx, valdev in enumerate(first_deriv[search_start:search_end]):
                    if valdev < accuracy and valdev > -(accuracy) and jpoint_search_flag==1:
                        jpoints.append(search_start+der_idx)
                        jpoint_search_flag = 0 #Only stores the first value found
                #Calculate T-P segment
                tpseg_searchflag = 1
    #             tpsearch_start = int(search_start+(qtc_width-(qrs_width*2)))
                tpsearch_start = int(search_start+der_idx+(qtc_width-(qrs_width*2)))
                tpsearch_end = int(tpsearch_start+iso_dur)
                for der_idx, valdev in enumerate(first_deriv[tpsearch_start:tpsearch_end]):
                    if valdev < accuracy and valdev > -(accuracy) and tpseg_searchflag==1:
                        tppoints.append(tpsearch_start+der_idx)
                        tpseg_searchflag = 0 #Only stores the first value found
                cur_hbeat = cur_hbeat+1


    if (len(jpoints)) != (len(tppoints)):
        #This means that the last ECG cycle was incomplete. Thus, it is not possible to calcylate the ST-elevation in this cycle.
        #The following flag is not used in this implementation, but it should be used as a hint in upcoming developments to solve the previously mentioned issue
        warning_flag = True
        # print (('peaks %s, J points: %s and tp points: %s')%(len(peaks),len(jpoints), len(tppoints)))

    if plot == True:
        plt.clf()
        plt.plot(sig)
        plt.plot(first_deriv, alpha = 0.5)
        for x in range(len(jpoints)):
            plt.plot(jpoints[x], sig[jpoints[x]], 'r*') #Plot J points
            plt.plot(tppoints[x], sig[tppoints[x]], 'b<') #Plot TP segment

    #Calculate amplitude in the ST segment
    st_amp_inmv = []
    if warning_flag == False:
        for val in range(len(jpoints)):
            st_amp_inmv.append(np.mean(sig[jpoints[val]:jpoints[val]+st_length]) - np.mean(sig[tppoints[val]:tppoints[val]+st_length]))
    else:
        for val in range(len(jpoints)-1):
            st_amp_inmv.append(np.mean(sig[jpoints[val]:jpoints[val] + st_length]) - np.mean(sig[tppoints[val]:tppoints[val] + st_length]))
    
    return st_amp_inmv, hr
