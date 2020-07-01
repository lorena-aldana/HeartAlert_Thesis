import time
import numpy as np
import random
from supercollidersc import SuperColliderClient, OSCsend_receive
import ecgprocpy3 as ecgpro

#Create OSC clients
scserver = SuperColliderClient()
oscother = OSCsend_receive("127.0.0.1", 57120) #osc messages to the language


def set_gui(_gui):
    '''Function to communicate to the functions defined in the GUI'''
    global gui
    gui = _gui

def linlin(data, source_min, source_max, target_min, target_max):
    "Linear mapping function"
    return (data-source_min)/(source_max-source_min)*(target_max-target_min) + target_min


def st_sonification_wa(currentlead, ecgpeaks, st_amp_mean_lead, st_amp, num_leads, playbackrate, wind, thund, rain, mainWindow):
    '''Water ambience sonification function: Triggers the water drop sounds according to the ST elevation measured between consecutive R peaks'''

    #Retrieve values from GUI
    n_drops, RR_per, ambs_amp, wat_amp, strW = which_son_water_values()
    #Set starting parameters
    global now;
    now = time.time()
    num_speakers = 2
    #Sonification parameters
    synth = 'play_water_sound'
    amp = wat_amp / (num_speakers * num_leads)
    #Select a random buffer
    buf_son = 0
    #Calculate period between consecutive R peaks
    rr = ecgpro.find_rr_peaks(ecgpeaks, playbackrate)
    #Ambience sounds
    ambience_sounds(currentlead, playbackrate, wind, thund, rain, mainWindow)

    for peak in range(0,len(ecgpeaks) - 1): #If the last cycle is not complete, there is one less st_amp calculation than number of R peaks found

        if mainWindow.playing == False:
            mainWindow.line.set_xdata([0.1, 0.1])
            return
        if mainWindow.son_water_state == 1:  # Exit thread when stop button is pressed
            mainWindow.line.set_xdata([0.1, 0.1])
            return

        #Define number of drops according to the ST elevation
        numdrops = int(linlin(np.abs(st_amp[peak]), 0.00001, 0.5, 1, n_drops))
        #Set the timetags for each drop
        times_drops = np.linspace(0.0,rr[peak]*RRper,numdrops) #rrpeak already accounts for the playbackrate

        if peak == 0:
            time.sleep(ecgpeaks[peak][0]*playbackrate)
            current_time = ecgpeaks[peak][0]*playbackrate
        else:
            time.sleep(rr[peak-1])
            current_time =  ecgpeaks[peak][0]*playbackrate

        if currentlead == 0:
            gui.plot_update(ecgpeaks[peak][0], current_time)

        #Sonification
        for ix,t_drops in enumerate(times_drops):
            if mainWindow.son_water_state == 1:  # Exit thread when stop button is pressed
                mainWindow.line.set_xdata([0.1, 0.1])
                return

            #Send the messages according to their respective time tag
            scserver.sc_bundle(now + t_drops,"s_new", [synth, -1, 1, 0, "buf", buf_son, 'amp', amp])  # Panning is optional

def ambience_sounds(currentlead, playbackrate, wind, thund, rain, mainWindow):
    '''This function controls the timing and triggering of the additional ambience sounds that represent ST elevation in contiguous ECG lead groups'''
    _, _, ambs_amp, _, _ = which_son_water_values()
    spks = 2.0
    ch = 0

    if currentlead == 0:
        total_amb_sounds = wind+thund+rain
        amb_triggertimes = np.linspace(2.0, 10.0, total_amb_sounds) #Create random trigger times from 0 to 10 seconds

        amb_synths =[]
        if wind == 1:
            amb_synths.append('ambience_synth_wind')
        if thund == 1:
            amb_synths.append('ambience_synth_thund')
        if rain == 1:
            amb_synths.append('ambience_synth_rain')

        random.shuffle(amb_synths)

        for idx, t_amb in enumerate(amb_triggertimes):
            scserver.sc_bundle(now + t_amb, "s_new", [amb_synths[idx], -1, 1, 0, 'amp', ambs_amp/spks, 'ch', ch])


def st_sonification_mo(currentlead, ecgpeaks, st_amp_mean_lead,st_amp, num_leads, playbackrate, RpeakUpFr, TwaveUpFr, total_pln_cnt, SoundEventsDur, mainWindow):
    '''Morph sonification function: Controls the timing and tiggering of sounds according to the ST elevation measured between consecutive R peaks.
    In this current implementation the R peak amplitude is used as the T wave amplitude parameter too.'''


    R, T, SoundED, ampM, strM = which_son_morph_values()  # Check slider values
    global now
    now = time.time()
    spks = 2.0
    synth = 'morph_synth'
    lininranges = [[0.0, 2.0], [0.0, 0.8]]
    average_qtc_dur = 0.4
    cont_elevated_leads = total_pln_cnt
    # Calculate period between consecutive R peaks
    rr = ecgpro.find_rr_peaks(ecgpeaks, playbackrate) #rr already takes into account stretching
    #Go through peaks
    for peak in range(0, len(ecgpeaks) - 1):  # If the last cycle is not complete, there is one less st_amp calculation than number of R peaks found
        if mainWindow.playing == False:
            mainWindow.line.set_xdata([0.1, 0.1])
            return
        if mainWindow.son_morph_state == 1:  # Exit thread when stop button is pressed
            mainWindow.line.set_xdata([0.1, 0.1])
            return
        R, T, SoundED, ampM, strM = which_son_morph_values()  # Check slider values

        if peak == 0:
            time.sleep(ecgpeaks[peak][0] * playbackrate)
            current_time = ecgpeaks[peak][0] * playbackrate
        else:
            time.sleep(rr[peak - 1])
            current_time = ecgpeaks[peak][0] * playbackrate

        if currentlead == 0:
            gui.plot_update(ecgpeaks[peak][0], current_time)

        linoutfreqranges = [[100, R], [200, T]]  # Ranges for linear mapping
        times_sounds = [0, (rr[peak]*playbackrate)*average_qtc_dur]


        for trigger_t in range(len(times_sounds)):
            scserver.sc_bundle(now+times_sounds[trigger_t], "/s_new",[synth, -1, 1, 0,
                                                                        'vf', linlin(ecgpeaks[peak][1], lininranges[trigger_t][0],
                                                                                     lininranges[trigger_t][1],
                                                                                     linoutfreqranges[trigger_t][0],
                                                                                     linoutfreqranges[trigger_t][1]),
                                                                        'vrate', (np.mean(rr)),
                                                                        'vdepth',
                                                                        linlin(cont_elevated_leads, 0, 11.0, 0, 1.0),
                                                                        'morphf', linlin(st_amp[peak], 0, 0.6, 0, 1.0),
                                                                        'onset', times_sounds[trigger_t],
                                                                        'smul', ampM / (spks * num_leads),
                                                                        'strfactor=1', strM,
                                                                        'soundeventdur', (SoundED / 1000.0)])


    #
    # for peak in range(len(ecgpeaks)):
    #     if mainWindow.son_morph_state == 1:  # Exit thread when stop button is pressed
    #         mainWindow.line.set_xdata([0.1, 0.1])
    #         return
    #     if peak == 0:
    #         time_to_wait = ((ecgpeaks[peak][0] / SampleRate) * strM) - start
    #     else:
    #         time_to_wait = ((ecgpeaks[peak][0] / SampleRate) - (ecgpeaks[peak - 1][0] / SampleRate)) * strM
    #     time.sleep(time_to_wait)  # Wait until next peak
    #     gui.plot_update(ecgpeaks[peak][0] / SampleRate, time_to_wait)  # Update reference line in plot
    #     R, T, SoundED, ampM, strM = which_son_morph_values()  # Check slider values
    #     times = [(ecgpeaks[peak][0] / SampleRate) * strM, ((ecgpeaks[peak][0] + qstduration - afterQRS - afterQRS) / SampleRate) * strM]  # Set time for R peak and T wave
    #     descriptors = [amp_R_peak[peak], st_stats[peak][0]]  # Amplitude R peak and amplitude T wave
    #     linoutfreqranges = [[100, R], [200, T]]  # Ranges for linear mapping
    #     for t in range(2):
    #         if mainWindow.son_morph_state == 1:  # Exit thread when stop button is pressed
    #             mainWindow.line.set_xdata([0.1, 0.1])
    #             return
    #         synth = 'morph_synth'  # Plays a specific synth
    #         scserver.sendMessage(now + delay + times[t], "/s_new", [synth, -1, 1, 0,
    #                                                                 'vf', linlin(descriptors[t], lininranges[t][0],
    #                                                                              lininranges[t][1],
    #                                                                              linoutfreqranges[t][0],
    #                                                                              linoutfreqranges[t][1]),
    #                                                                 'vrate', (np.mean(dt) * strM),
    #                                                                 'vdepth',
    #                                                                 linlin(contiguity_factor, 0, 11.0, 0, 1.0),
    #                                                                 'morphf', linlin(st_amp_peak[peak], 0, 0.6, 0, 1.0),
    #                                                                 'onset', times[t],
    #                                                                 'smul', ampM / (spks * numofleads),
    #                                                                 'strfactor=1', strM,
    #                                                                 'soundeventdur', (SoundED / 1000.0)])


def updated_son_water_values(numdrops,RRpercentage,sonamb,sonamp_water,pl_stretch_water):
    '''Function to obtain the sonification parameters from the GUI in the water ambience sonification method'''
    global ndrops; global RRper; global amb_sounds_amp; global amp_water; global stretch_water
    ndrops= numdrops
    RRper= RRpercentage
    amb_sounds_amp = sonamb
    amp_water= sonamp_water
    stretch_water= pl_stretch_water

def updated_son_morph_values(RpeakUpperFreqRange, TwaveUpperFreqRange, SoundEventsDur,sonamp_morph, pl_stretch_morph):
    '''Function to obtain the sonification parameters from the GUI in the morph sonification method'''
    global Rpeakfreq; global Tpeakfreq; global SoundEvDur; global amp_morph; global stretch_morph;
    Rpeakfreq= RpeakUpperFreqRange
    Tpeakfreq= TwaveUpperFreqRange
    SoundEvDur=SoundEventsDur
    amp_morph=sonamp_morph
    stretch_morph= pl_stretch_morph

def which_son_morph_values():
    '''Function to obtain the current values from the sliders (Morph Sonification) in the interaction module'''
    return Rpeakfreq, Tpeakfreq, SoundEvDur, amp_morph, stretch_morph

def which_son_water_values():
    '''Function to obtain the current values from the sliders (Water Sonification) in the interaction module'''
    return ndrops, RRper, amb_sounds_amp, amp_water, stretch_water


