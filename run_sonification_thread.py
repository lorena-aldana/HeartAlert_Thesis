import threading
import sonifications_main as SONM

class run_sonification(threading.Thread):
    '''Class to start the sonifications as threads'''
    def __init__(self,selected_son, ecgpeaks,st_amp_lead,st_amp_all_data,numofleads,pl_stretch_water,wind_state, thund_state, rain_state, mainWindow, RpeakUpperFreqRange, TwaveUpperFreqRange, total_pln_cnt, pl_stretch_morph, SoundEventsDur):
        super(run_sonification, self).__init__()
        #water ambience parameters:
        self.son_type = selected_son
        self.ecgpeaks = ecgpeaks
        self.st_amp_lead = st_amp_lead
        self.st_amp_all_data = st_amp_all_data
        self.numofleads = numofleads
        self.pl_stretch_water= pl_stretch_water
        self.wind_state = wind_state
        self.thund_state = thund_state
        self.rain_state = rain_state
        self.mainWindow = mainWindow
        #morph parameters:
        self.RpeakUpFr = RpeakUpperFreqRange
        self.TwaveUpFr = TwaveUpperFreqRange
        self.total_pln_cnt = total_pln_cnt
        self.pl_stretch_morph = pl_stretch_morph
        self.SoundEventsDur =  SoundEventsDur
        #General parameters:
        self._stop_event = threading.Event()
        self.runFlag = False

    def run(self):
        self.runFlag = True

        for leads in range(self.numofleads):

            self.current_lead = leads

            if self.son_type == "Water":
            #Start the water ambience sonification
                threading._start_new_thread(SONM.st_sonification_wa,
                                (self.current_lead, self.ecgpeaks[leads],self.st_amp_lead[leads],self.st_amp_all_data[leads],self.numofleads,self.pl_stretch_water,self.wind_state, self.thund_state, self.rain_state, self.mainWindow))

            elif self.son_type == "Morph":
            #start the morph sonification
                threading._start_new_thread(SONM.st_sonification_mo,
                                            (self.current_lead, self.ecgpeaks[leads], self.st_amp_lead[leads],
                                             self.st_amp_all_data[leads], self.numofleads, self.pl_stretch_morph,self.RpeakUpFr, self.TwaveUpFr, self.total_pln_cnt, self.SoundEventsDur, self.mainWindow))

    def stop(self):
        '''To stop running the thread'''
        self.runFlag = False