print ('This is Heart Alert')

#Import libraries
import sys
from PyQt5 import QtGui, QtCore, QtWidgets
import numpy as np
import math
import matplotlib.pyplot as plt
import ecgprocpy3 as ecgpro
from run_sonification_thread import run_sonification as rson
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg as FigureCanvas,
NavigationToolbar2QT as NavigationToolbar)

#Import own libraries:
import sonifications_main as SONM #Functions for sonification
from supercollidersc import SuperColliderClient #OSC communication functions

# Creates GUI
class Window(QtWidgets.QMainWindow):

    def __init__(self): #Initialization
        super(Window,self).__init__()
        self.setGeometry(15, 15, 1000, 600) #(start x,start y, xwidth, ywidth)
        self.setWindowTitle("HEART ALERT")

        #Create main Layout
        mainlayout = QtWidgets.QHBoxLayout()

            # To Apply main layout to the main window
        self.widget = QtWidgets.QWidget()  # Create a widget
        self.widget.setLayout(mainlayout)  # Apply main Layout to widget!!!
        self.setCentralWidget(self.widget)  # Set main layout to layout of widget!!!
            #Create first two sublayouts
        optionsandconlayout= QtWidgets.QVBoxLayout()
        optionsandconlayout.setSpacing(20)
        mainlayout.addLayout(optionsandconlayout)
        plotandintlayout = QtWidgets.QVBoxLayout()
        plotandintlayout.setSpacing(5)
        mainlayout.addLayout(plotandintlayout)

            #Create the other sublayouts
        optionslayout = QtWidgets.QVBoxLayout(); playsconlayout= QtWidgets.QVBoxLayout()
        ecggraphlayout = QtWidgets.QVBoxLayout();
        self.maininteractionlayout = QtWidgets.QVBoxLayout() #Main interaction layout has to be the same size of the plot

        self.maininteractionlayout.setSpacing(10)
        ecggraphlayout.setSpacing(10)

        self.interactionlayout_firstrow = QtWidgets.QHBoxLayout();self.interactionlayout_firstrow.setSpacing(10)
        self.interactionlayout_secondrow= QtWidgets.QHBoxLayout();self.interactionlayout_firstrow.setSpacing(10)
        optionsandconlayout.addLayout(optionslayout); optionsandconlayout.addLayout(playsconlayout)
        plotandintlayout.addLayout(ecggraphlayout);
        plotandintlayout.addLayout(self.maininteractionlayout)
        self.maininteractionlayout.addLayout(self.interactionlayout_firstrow) #Interaction buttons
        self.maininteractionlayout.addLayout(self.interactionlayout_secondrow)

        #1. Options Layout

            #Module title
        font01 = QtGui.QFont()
        font01.setPointSize(13)
        font01.setBold(True)
        font01.setWeight(75)

        labeloptionsmodule = QtWidgets.QLabel('Options module', self)
        optionslayout.addWidget(labeloptionsmodule)
        labeloptionsmodule.setAlignment(QtCore.Qt.AlignCenter)  # setMargin(10)
        labeloptionsmodule.setFont(font01)  # Apply Font


            #Select ECG file
        btselectfile = QtWidgets.QPushButton('Select ECG file', self)
        optionslayout.addWidget(btselectfile)  # Add buttons
        btselectfile.clicked.connect(self.open_ecg_file)  # Action of window

            #Sample Rate Label
        labelSR = QtWidgets.QLabel('Select Sample Rate and Database:', self)
        optionslayout.addWidget(labelSR)

            #Sample Rate Dropdown mENU

        srdropdown = QtWidgets.QComboBox(self)
        srdropdown.addItem("500.0");
        srdropdown.addItem("1000.0");
        optionslayout.addWidget(srdropdown)
        srdropdown.activated[str].connect(self.sr_dropmenu_select)

            # Database Dropdown mENU

        dbdropdown = QtWidgets.QComboBox(self)
        dbdropdown.addItem("Mac2000");
        dbdropdown.addItem("Physionet");
        optionslayout.addWidget(dbdropdown)
        dbdropdown.activated[str].connect(self.db_dropmenu_select)

            # Analyze ECG Button
        btanalyzecg = QtWidgets.QPushButton('Analyze ECG', self)
        optionslayout.addWidget(btanalyzecg)  # Add buttons
        btanalyzecg.clicked.connect(self.analyze_ecg)  # Action of window

            #Leads Label
        labelleads = QtWidgets.QLabel('Select Leads to plot and Sonify:', self)
        optionslayout.addWidget(labelleads)

            # Leads Dropdown Menu
        leadsdropdown = QtWidgets.QComboBox(self)
        leadsdropdown.addItem("All leads");
        leadsdropdown.addItem("Frontal plane"); leadsdropdown.addItem("Horizontal plane");
        leadsdropdown.addItem("Lateral leads");leadsdropdown.addItem("Inferior leads");
        leadsdropdown.addItem("Anterior leads");leadsdropdown.addItem("Septal leads");
        leadsdropdown.addItem("I"); leadsdropdown.addItem("II");leadsdropdown.addItem("III")
        leadsdropdown.addItem("AVR");leadsdropdown.addItem("AVL");leadsdropdown.addItem("AVF")
        leadsdropdown.addItem("V1");leadsdropdown.addItem("V2");leadsdropdown.addItem("V3")
        leadsdropdown.addItem("V4");leadsdropdown.addItem("V5");leadsdropdown.addItem("V6")


        optionslayout.addWidget(leadsdropdown)
        leadsdropdown.activated[str].connect(self.leads_dropmenu_select)  # Only send the signal when the item is changed


        #2. Play Control Layout

            # Sonification module  Label

        labelsonmodule = QtWidgets.QLabel('Sonification module', self)
        optionslayout.addWidget(labelsonmodule)
        labelsonmodule.setAlignment(QtCore.Qt.AlignCenter)#setMargin(10)
        labelsonmodule.setFont(font01) #Apply Font

            #Label Indicating to select sonification:
        labelsonselect=  QtWidgets.QLabel('Select Sonification type:', self)
        optionslayout.addWidget(labelsonselect)
        labelsonmodule.setAlignment(QtCore.Qt.AlignCenter)

            # Dropdown Menu
        sondropdown = QtWidgets.QComboBox(self)
        sondropdown.addItem("Water")
        sondropdown.addItem("Morph")
        sondropdown.move(10, 60)
        playsconlayout.addWidget(sondropdown)
        sondropdown.activated[str].connect(self.son_dropmenu_select)

            #Play Sonification button
        btplay = QtWidgets.QPushButton('Play Sonification', self)
        playsconlayout.addWidget(btplay)  # Add buttons
        btplay.clicked.connect(self.play_sonification)  # Action of window
            #Stop Sonification button
        btstop = QtWidgets.QPushButton('Stop Sonification', self)
        playsconlayout.addWidget(btstop)  # Add buttons
        btstop.clicked.connect(self.stop_sonification)  # Action of window

        #3. ECG Graph Layout

        # Plotting
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlim([0, 10])
        self.ax.set_ylim([0, 10])
        self.toolbar = NavigationToolbar(self.canvas, self)
        ecggraphlayout.addWidget(self.canvas)
        ecggraphlayout.addWidget(self.toolbar)

        #Plotting Options

        self.plot_peaks= QtWidgets.QCheckBox('Plot peaks',self)
        ecggraphlayout.addWidget(self.plot_peaks)
        self.plot_checkboxstate_peaks= self.plot_peaks.checkState()
        self.plot_peaks.stateChanged.connect(self.plot_ecg)


        #Interaction menu

        labelinteractionmodule = QtWidgets.QLabel('Interaction module', self)
        self.maininteractionlayout.addWidget(labelinteractionmodule)
        labelinteractionmodule.setAlignment(QtCore.Qt.AlignCenter)  # setMargin(10)
        labelinteractionmodule.setFont(font01)  # Apply Font

        self.interaction_layout_1()

        #5. Starting values

        self.db='m'
        self.SampleRate= 500.0
        #self.lead= [0,1,2,3,4,5]
        self.lead = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        self.labels = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]
        #self.labels = ["I", "II", "III", "AVR", "AVL", "AVF"]
        self.vfstate=0
        self.son_morph_state = 0
        self.son_water_state = 0
        self.selectedson= 'Water'
        self.pl_stretch_water = 1.0
        self.pl_stretch_morph = 1.0
        self.sonamp_morph = 0.5
        self.sonamp_water = 0.5
        self.RpeakUpperFreqRange= 200.0
        self.TwaveUpperFreqRange= 400.0
        self.SoundEventsDur= (600/1000.0)

        self.data = ''
        #Init OSC send
        self.scserver = SuperColliderClient()

    def interaction_layout_1(self):
        # 4. Interaction Layout

            #Delete previous Layout
        for i in reversed(range(self.interactionlayout_firstrow.count())):
            self.interactionlayout_firstrow.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.interactionlayout_secondrow.count())):
            self.interactionlayout_secondrow.itemAt(i).widget().setParent(None)


    #First row of the interaction layout
            #NUM DROPS #NUM DROPS #NUM DROPS #NUM DROPS #NUM DROPS #NUM DROPS
        self.sliderinteractlabel1ndrops = QtWidgets.QLabel('Number of drops') # ('Interaction Button Layout 1', self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteractlabel1ndrops)  # Add Label
        self.sliderinteractlabel1ndrops.setAlignment(QtCore.Qt.AlignCenter)
        self.sliderinteractvalue1ndropsbox = QtWidgets.QLineEdit('Sonification level')
        self.interactionlayout_firstrow.addWidget(self.sliderinteractvalue1ndropsbox)
            # Slider 01 # Slider 01 # Slider 01 # Slider 01
        self.sliderinteract1ndrops = QtWidgets.QSlider(self)  # ('Interaction Button Layout 1', self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteract1ndrops)  # Add buttons

        self.sliderinteract1ndrops.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract1ndrops.setRange(1,10)
        self.sliderinteract1ndrops.setValue(3)
        self.sliderinteract1ndrops.setTickInterval(1)
        self.sliderinteract1ndrops.setTickPosition(1)
        self.sliderinteract1ndrops.setSingleStep(1)
        self.sliderinteractvalue1ndropsbox.setFixedSize(40, 20)

        #Get slider value un update label #Get slider value un update label
        self.sliderinteract1ndropscurrentvalue = self.sliderinteract1ndrops.value() #Store the value from the slider
        self.sliderinteractlabel1ndrops.setText('Drops:')
        self.sliderinteractvalue1ndropsbox.setText(str(self.sliderinteract1ndropscurrentvalue))

        self.sliderinteract1ndrops.valueChanged.connect(self.slider1_ndrops_update)
        self.numdrops = self.sliderinteract1ndropscurrentvalue

            # DISTRIBUTION DROPS # DISTRIBUTION DROPS  # DISTRIBUTION DROPS  # DISTRIBUTION DROPS  # DISTRIBUTION DROPS
        self.sliderinteractlabel1dropsdist = QtWidgets.QLabel('Drops distribution')  # ('Interaction Button Layout 1', self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteractlabel1dropsdist)  # Add Label
        self.sliderinteractlabel1dropsdist.setAlignment(QtCore.Qt.AlignCenter)
        self.sliderinteractvalue1dropsdistbox = QtWidgets.QLineEdit('Drops Dist')
        self.interactionlayout_firstrow.addWidget(self.sliderinteractvalue1dropsdistbox)
            # Slider 02 # Slider 02 # Slider 02 # Slider 02
        self.sliderinteract1dropsdist = QtWidgets.QSlider(self)  # ('Interaction Button Layout 1', self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteract1dropsdist)  # Add buttons

        self.sliderinteract1dropsdist.setOrientation(QtCore.Qt.Horizontal);self.sliderinteract1dropsdist.setFixedHeight(100)
        self.sliderinteract1dropsdist.setRange(40, 100)
        #self.sliderinteract1dropsdist.setMinimum(40);self.sliderinteract1dropsdist.setMaximum(100)
        self.sliderinteract1dropsdist.setValue(40);self.sliderinteract1dropsdist.setTickInterval(10)
        self.sliderinteract1dropsdist.setTickPosition(1);
        self.sliderinteract1dropsdist.setSingleStep(10)#self.sliderinteract1dropsdist.setTickPosition(1);
        self.sliderinteractvalue1dropsdistbox.setFixedSize(40, 20)
        # Get slider value un update label
        self.sliderinteract1dropsdistcurrentvalue = self.sliderinteract1dropsdist.value()  # Store the value from the slider
        self.sliderinteractlabel1dropsdist.setText('Drops distribution:')
        self.sliderinteractvalue1dropsdistbox.setText(str(self.sliderinteract1dropsdistcurrentvalue/100.0))

        self.sliderinteract1dropsdist.valueChanged.connect(self.slider1_dropsdist_update)
        self.RRpercentage = self.sliderinteract1dropsdistcurrentvalue/100.0

        # AMBIENCE SOUNDS VOLUME VOLUME VOLUME VOLUME VOLUME VOLUME VOLUME
        self.sliderinteractvalue1ambiencelevel = QtWidgets.QLabel('Ambience Sounds level')
        self.interactionlayout_firstrow.addWidget(self.sliderinteractvalue1ambiencelevel)
        self.sliderinteractvalue1ambiencelevel.setAlignment(QtCore.Qt.AlignCenter)
        self.sliderinteractvalue1ambiencelevelbox = QtWidgets.QLineEdit('Sonification level')
        self.interactionlayout_firstrow.addWidget(self.sliderinteractvalue1ambiencelevelbox)
        self.sliderinteract1ambiencelevel = QtWidgets.QSlider(self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteract1ambiencelevel)

        self.sliderinteract1ambiencelevel.setRange(1, 100)
        self.sliderinteract1ambiencelevel.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract1ambiencelevel.setValue(30)
        self.sliderinteract1ambiencelevel.setTickInterval(10)
        self.sliderinteract1ambiencelevel.setTickPosition(1)
        self.sliderinteract1ambiencelevel.setSingleStep(10)
        self.sliderinteractvalue1ambiencelevelbox.setFixedSize(40, 20)

        self.sliderinteract1ambiencelevel_currentvalue = self.sliderinteract1ambiencelevel.value()  # Store the value from the slider
        self.sliderinteractvalue1ambiencelevel.setText('Ambience Sounds Level dB:')
        self.sliderinteractvalue1ambiencelevelbox.setText(str(round(20 * math.log10((self.sliderinteract1ambiencelevel_currentvalue / 100.0) / 1.0), 2)))

        self.sliderinteract1ambiencelevel.valueChanged.connect(self.slider1ambiencevolume_update)  # Connect to function
        self.sonamb = self.sliderinteract1ambiencelevel_currentvalue / 100.0

    # Second row of the interaction layout
        # DROPS VOLUME #VOLUME #VOLUME #VOLUME #VOLUME #VOLUME
        self.sliderinteractvalue1sonlevel = QtWidgets.QLabel('Sonification level')
        self.interactionlayout_secondrow.addWidget(self.sliderinteractvalue1sonlevel)
        self.sliderinteractvalue1sonlevel.setAlignment(QtCore.Qt.AlignCenter)
        self.sliderinteractvalue1sonlevelbox = QtWidgets.QLineEdit('Sonification level')
        self.interactionlayout_secondrow.addWidget(self.sliderinteractvalue1sonlevelbox)
        self.sliderinteract1level = QtWidgets.QSlider(self)
        self.interactionlayout_secondrow.addWidget(self.sliderinteract1level)

        self.sliderinteract1level.setRange(1, 100)
        self.sliderinteract1level.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract1level.setValue(50)
        self.sliderinteract1level.setTickInterval(10)
        self.sliderinteract1level.setTickPosition(1)
        self.sliderinteract1level.setSingleStep(10)
        self.sliderinteractvalue1sonlevelbox.setFixedSize(40, 20)

        self.sliderinteract1levelcurrentvalue = self.sliderinteract1level.value()  # Store the value from the slider
        self.sliderinteractvalue1sonlevel.setText('Level dB:')
        self.sliderinteractvalue1sonlevelbox.setText(str(round(20*math.log10((self.sliderinteract1levelcurrentvalue/100.0)/1.0),2)))

        self.sliderinteract1level.valueChanged.connect(self.slider1volume_update)  # Connect to function
        self.sonamp_water = self.sliderinteract1levelcurrentvalue / 100.0


        #Playback speed #Playback speed #Playback speed #Playback speed #Playback speed
        self.sliderinteractlabel2stretch = QtWidgets.QLabel('Playback Speed')  # ('Interaction Button Layout 1', self)
        self.interactionlayout_secondrow.addWidget(self.sliderinteractlabel2stretch)
        self.sliderinteractlabel2stretch.setAlignment(QtCore.Qt.AlignCenter)

        self.sliderinteractlabel2box = QtWidgets.QLineEdit('Playback speed')
        self.interactionlayout_secondrow.addWidget(self.sliderinteractlabel2box)


        self.sliderinteract2stretch = QtWidgets.QSlider(self)
        self.interactionlayout_secondrow.addWidget(self.sliderinteract2stretch)

        self.sliderinteract2stretch.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract2stretch.setFixedHeight(100)
        self.sliderinteract2stretch.setRange(-1, 1)
        self.sliderinteract2stretch.setValue(0)
        self.sliderinteract2stretch.setTickInterval(1)
        self.sliderinteract2stretch.setTickPosition(1)
        self.sliderinteractlabel2box.setFixedSize(40, 20)

        self.sliderinteract2stretchcurrentvalue= self.sliderinteract2stretch.value()
        self.sliderinteractlabel2stretch.setText('Playback Speed:')
        self.sliderinteractlabel2box.setText(str(self.sliderinteract2stretchcurrentvalue))
        self.sliderinteract2stretch.valueChanged.connect(self.slider1_playspeed_update)
        self.playspeed_water = self.sliderinteract2stretchcurrentvalue
        if self.playspeed_water == 0:
            self.pl_stretch_water = 1.0
        elif self.playspeed_water == -1:
            self.pl_stretch_water = 2.0
        elif self.playspeed_water == 1:
            self.pl_stretch_water = 0.5
        #updated values

        SONM.updated_son_water_values(self.numdrops, self.RRpercentage, self.sonamb, self.sonamp_water,self.pl_stretch_water)


    def interaction_layout_2(self):
        # 4. Interaction Layout

        # Delete previous Layout
        for i in reversed(range(self.interactionlayout_firstrow.count())):
            self.interactionlayout_firstrow.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.interactionlayout_secondrow.count())):
            self.interactionlayout_secondrow.itemAt(i).widget().setParent(None)

    #First row of interaction layout #First row of interaction layout  #First row of interaction layout  #First row of interaction layout
            #R peak frequency #R peak frequency #R peak frequency #R peak frequency #R peak frequency
        self.sliderinteract2frqRpklabel=QtWidgets.QLabel('R peak freq')
        self.interactionlayout_firstrow.addWidget(self.sliderinteract2frqRpklabel)
        self.sliderinteract2frqRpkbox= QtWidgets.QLineEdit('R peak freq')
        self.interactionlayout_firstrow.addWidget(self.sliderinteract2frqRpkbox)
        self.sliderinteract2frqRpk=  QtWidgets.QSlider(self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteract2frqRpk)

        self.sliderinteract2frqRpk.setRange(100,1000)
        self.sliderinteract2frqRpk.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract2frqRpk.setValue(200)
        self.sliderinteract2frqRpk.setSingleStep(100)
        self.sliderinteract2frqRpk.setTickInterval(200)
        self.sliderinteract2frqRpk.setTickPosition(1)
        self.sliderinteract2frqRpkbox.setFixedSize(40, 20)

        self.sliderinteract2frqRpk_currentvalue = self.sliderinteract2frqRpk.value()
        self.sliderinteract2frqRpklabel.setText('R peak freq. upper limit:')
        self.sliderinteract2frqRpkbox.setText(str(self.sliderinteract2frqRpk_currentvalue))

        self.sliderinteract2frqRpk.valueChanged.connect(self.RpeakFrqUpdate)
        self.RpeakUpperFreqRange= self.sliderinteract2frqRpk_currentvalue

        #T wave frequency #T wave frequency #T wave frequency #T wave frequency
        self.sliderinteract2frqTwvlabel =QtWidgets.QLabel('T wave freq')
        self.interactionlayout_firstrow.addWidget(self.sliderinteract2frqTwvlabel)
        self.sliderinteract2frqTwvbox= QtWidgets.QLineEdit('T wave freq')
        self.interactionlayout_firstrow.addWidget(self.sliderinteract2frqTwvbox)
        self.sliderinteract2frqTwv = QtWidgets.QSlider(self)
        self.interactionlayout_firstrow.addWidget(self.sliderinteract2frqTwv)

        self.sliderinteract2frqTwv.setRange(100,1000)
        self.sliderinteract2frqTwv.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract2frqTwv.setValue(400)
        self.sliderinteract2frqTwv.setSingleStep(100)
        self.sliderinteract2frqTwv.setTickInterval(200)
        self.sliderinteract2frqTwv.setTickPosition(1)
        self.sliderinteract2frqTwvbox.setFixedSize(40, 20)

        self.sliderinteract2frqTwv_currentvalue = self.sliderinteract2frqTwv.value()
        self.sliderinteract2frqTwvlabel.setText('T wave freq. upper limit:')
        self.sliderinteract2frqTwvbox.setText(str(self.sliderinteract2frqTwv_currentvalue))

        self.sliderinteract2frqTwv.valueChanged.connect(self.TwaveFrqUpdate)
        self.TwaveUpperFreqRange= self.sliderinteract2frqTwv_currentvalue

        #sound events duration
        self.soundeventsdurlabel = QtWidgets.QLabel('Event duration (ms)')
        self.interactionlayout_firstrow.addWidget(self.soundeventsdurlabel)
        self.soundeventsdurbox = QtWidgets.QLineEdit('Sound event dur')
        self.interactionlayout_firstrow.addWidget(self.soundeventsdurbox)
        self.soundeventsdur= QtWidgets.QSlider(self)
        self.interactionlayout_firstrow.addWidget(self.soundeventsdur)

        self.soundeventsdur.setRange(0,1000) #This would be ms
        self.soundeventsdur.setOrientation(QtCore.Qt.Horizontal)
        self.soundeventsdur.setValue(600)
        self.soundeventsdur.setSingleStep(100)
        self.soundeventsdur.setTickInterval(200)
        self.soundeventsdur.setTickPosition(1)
        self.soundeventsdurbox.setFixedSize(40, 20)

        self.soundeventsdur_currentvalue = self.soundeventsdur.value()
        self.soundeventsdurbox.setText(str(self.soundeventsdur_currentvalue))

        self.soundeventsdur.valueChanged.connect(self.SoundEventDur_update)
        self.SoundEventsDur = self.soundeventsdur_currentvalue


    # Second row of int layout # Second row of int layout # Second row of int layout # Second row of int layout

            # VOLUME #VOLUME #VOLUME #VOLUME #VOLUME #VOLUME
        self.sliderinteractvalue2sonlevel = QtWidgets.QLabel('Sonification level')
        self.interactionlayout_secondrow.addWidget(self.sliderinteractvalue2sonlevel)
        self.sliderinteractvalue2sonlevel.setAlignment(QtCore.Qt.AlignCenter)
        self.sliderinteractvalue2sonlevelbox = QtWidgets.QLineEdit('Sonification level')
        self.interactionlayout_secondrow.addWidget(self.sliderinteractvalue2sonlevelbox)
        self.sliderinteract2level = QtWidgets.QSlider(self)
        self.interactionlayout_secondrow.addWidget(self.sliderinteract2level)

        self.sliderinteract2level.setRange(1, 100)
        self.sliderinteract2level.setOrientation(QtCore.Qt.Horizontal)
        self.sliderinteract2level.setValue(50)
        self.sliderinteract2level.setTickInterval(10)
        self.sliderinteract2level.setTickPosition(1)
        self.sliderinteract2level.setSingleStep(10)
        self.sliderinteractvalue2sonlevelbox.setFixedSize(40, 20)

        self.sliderinteract2levelcurrentvalue = self.sliderinteract2level.value()  # Store the value from the slider
        self.sliderinteractvalue2sonlevel.setText('Level dB:')
        self.sliderinteractvalue2sonlevelbox.setText(str(round(20*math.log10((self.sliderinteract2levelcurrentvalue/100.0)/1.0),2)))


        self.sliderinteract2level.valueChanged.connect(self.slider2volume_update)  # Connect to function
        self.sonamp_morph = self.sliderinteract2levelcurrentvalue / 100.0

        # Playback speed #Playback speed #Playback speed #Playback speed #Playback speed
        self.sliderinteract2label2stretch = QtWidgets.QLabel('Playback Speed')  # ('Interaction Button Layout 1', self)
        self.interactionlayout_secondrow.addWidget(self.sliderinteract2label2stretch)
        self.sliderinteract2label2stretch.setAlignment(QtCore.Qt.AlignCenter)

        self.sliderinteract2label2box = QtWidgets.QLineEdit('Playback speed')
        self.interactionlayout_secondrow.addWidget(self.sliderinteract2label2box)

        self.slider2interact2stretch = QtWidgets.QSlider(self)
        self.interactionlayout_secondrow.addWidget(self.slider2interact2stretch)

        self.slider2interact2stretch.setOrientation(QtCore.Qt.Horizontal)
        self.slider2interact2stretch.setFixedHeight(100)
        self.slider2interact2stretch.setRange(-1, 1)
        self.slider2interact2stretch.setValue(0)
        self.slider2interact2stretch.setTickInterval(1)
        self.slider2interact2stretch.setTickPosition(1)
        self.sliderinteract2label2box.setFixedSize(40, 20)

        self.slider2interact2stretchcurrentvalue = self.slider2interact2stretch.value()
        self.sliderinteract2label2stretch.setText('Playback Speed:')
        self.sliderinteract2label2box.setText(str(self.slider2interact2stretchcurrentvalue))
        self.slider2interact2stretch.valueChanged.connect(self.slider2_playspeed_update)
        self.playspeed_morph = self.slider2interact2stretchcurrentvalue
        if self.playspeed_morph == 0:
            self.pl_stretch_morph = 1.0
        elif self.playspeed_morph == -1:
            self.pl_stretch_morph = 2.0
        elif self.playspeed_morph == 1:
            self.pl_stretch_morph = 0.5

        #Updated values
        SONM.updated_son_morph_values(self.RpeakUpperFreqRange, self.TwaveUpperFreqRange, self.SoundEventsDur,self.sonamp_morph, self.pl_stretch_morph)

    def slider1_ndrops_update(self):  # numdrops
        self.sliderinteract1ndropscurrentvalue = self.sliderinteract1ndrops.value()  # Store the value from the slider
        self.sliderinteractvalue1ndropsbox.setText(str(self.sliderinteract1ndropscurrentvalue))
        self.numdrops = self.sliderinteract1ndropscurrentvalue
        SONM.updated_son_water_values(self.numdrops,self.RRpercentage,self.sonamb,self.sonamp_water,self.pl_stretch_water)

    def slider1_dropsdist_update(self):  # RRpercentage
        self.sliderinteract1dropsdistcurrentvalue = self.sliderinteract1dropsdist.value()  # Store the value from the slider
        self.sliderinteractvalue1dropsdistbox.setText(str(self.sliderinteract1dropsdistcurrentvalue / 100.0))
        self.RRpercentage = self.sliderinteract1dropsdistcurrentvalue / 100.0
        SONM.updated_son_water_values(self.numdrops, self.RRpercentage, self.sonamb, self.sonamp_water,self.pl_stretch_water)

    def slider1ambiencevolume_update(self):
        self.sliderinteract1ambiencelevel_currentvalue = self.sliderinteract1ambiencelevel.value()  # Store the value from the slider
        self.sliderinteractvalue1ambiencelevelbox.setText(
            str(round(20 * math.log10((self.sliderinteract1ambiencelevel_currentvalue / 100.0) / 1.0), 2)))
        self.sonamb = self.sliderinteract1ambiencelevel_currentvalue / 100.0
        SONM.updated_son_water_values(self.numdrops, self.RRpercentage, self.sonamb, self.sonamp_water,self.pl_stretch_water)

    def slider1volume_update(self):
        self.sliderinteract1levelcurrentvalue = self.sliderinteract1level.value()
        self.sliderinteractvalue1sonlevelbox.setText(str(round(20*math.log10((self.sliderinteract1levelcurrentvalue/100.0)/1.0),2)))
        self.sonamp_water = self.sliderinteract1levelcurrentvalue/100.0
        SONM.updated_son_water_values(self.numdrops, self.RRpercentage, self.sonamb, self.sonamp_water,self.pl_stretch_water)

    def slider1_playspeed_update(self):
        self.sliderinteract2stretchcurrentvalue = self.sliderinteract2stretch.value()
        self.sliderinteractlabel2box.setText(str(self.sliderinteract2stretchcurrentvalue))
        self.playspeed_water = self.sliderinteract2stretchcurrentvalue
        if self.playspeed_water== 0:
            self.pl_stretch_water=1.0
        elif self.playspeed_water== -1:
            self.pl_stretch_water=2.0
        elif self.playspeed_water== 1:
            self.pl_stretch_water=0.5

        SONM.updated_son_water_values(self.numdrops, self.RRpercentage, self.sonamb, self.sonamp_water,self.pl_stretch_water)

    def RpeakFrqUpdate(self):
        self.sliderinteract2frqRpk_currentvalue = self.sliderinteract2frqRpk.value()
        self.sliderinteract2frqRpkbox.setText(str(self.sliderinteract2frqRpk_currentvalue))
        self.RpeakUpperFreqRange = self.sliderinteract2frqRpk_currentvalue

        SONM.updated_son_morph_values(self.RpeakUpperFreqRange,self.TwaveUpperFreqRange,self.SoundEventsDur,self.sonamp_morph,self.pl_stretch_morph)

    def TwaveFrqUpdate(self):
        self.sliderinteract2frqTwv_currentvalue = self.sliderinteract2frqTwv.value()
        self.sliderinteract2frqTwvbox.setText(str(self.sliderinteract2frqTwv_currentvalue))
        self.TwaveUpperFreqRange = self.sliderinteract2frqTwv_currentvalue

        SONM.updated_son_morph_values(self.RpeakUpperFreqRange, self.TwaveUpperFreqRange, self.SoundEventsDur,self.sonamp_morph, self.pl_stretch_morph)

    def SoundEventDur_update(self):

        self.soundeventsdur_currentvalue = self.soundeventsdur.value()
        self.soundeventsdurbox.setText(str(self.soundeventsdur_currentvalue))
        self.SoundEventsDur = self.soundeventsdur_currentvalue

        SONM.updated_son_morph_values(self.RpeakUpperFreqRange, self.TwaveUpperFreqRange, self.SoundEventsDur,self.sonamp_morph, self.pl_stretch_morph)

    def slider2volume_update(self):
        self.sliderinteract2levelcurrentvalue = self.sliderinteract2level.value()  # Store the value from the slider
        self.sliderinteractvalue2sonlevelbox.setText(
            str(round(20 * math.log10((self.sliderinteract2levelcurrentvalue / 100.0) / 1.0), 2)))
        self.sonamp_morph = self.sliderinteract2levelcurrentvalue / 100.0

        SONM.updated_son_morph_values(self.RpeakUpperFreqRange, self.TwaveUpperFreqRange, self.SoundEventsDur,self.sonamp_morph, self.pl_stretch_morph)

    def slider2_playspeed_update(self):
        self.slider2interact2stretchcurrentvalue = self.slider2interact2stretch.value()
        self.sliderinteract2label2box.setText(str(self.slider2interact2stretchcurrentvalue))
        self.playspeed_morph = self.slider2interact2stretchcurrentvalue

        if self.playspeed_morph == 0:
            self.pl_stretch_morph = 1.0
        elif self.playspeed_morph == -1:
            self.pl_stretch_morph = 2.0
        elif self.playspeed_morph == 1:
            self.pl_stretch_morph = 0.5

        SONM.updated_son_morph_values(self.RpeakUpperFreqRange, self.TwaveUpperFreqRange, self.SoundEventsDur,self.sonamp_morph, self.pl_stretch_morph)

    def open_ecg_file(self):

        self.filename, file_extension = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',".","(*.csv)") #Self and title
        self.data=np.loadtxt(self.filename, delimiter=' ')  # Store Data

        if np.shape(self.data)[1]>12: #Just select the first 12 channels
            self.data=self.data[:,0:12]

        self.samples = np.shape(self.data)[0]
        self.num_leads = np.shape(self.data)[1]

        self.filedur= np.shape(self.data)[0]/self.SampleRate
        # self.sec10_cycles_infile= self.filedur/10

        print('File duration in seconds:')
        print(self.filedur)


    def plot_ecg(self):
        plt.ion()
        plt.cla()
        fig_size = plt.rcParams["figure.figsize"];
        fig_size[0] = 15;
        fig_size[1] = np.shape(self.data)[1] * 1.4
        plt.rcParams["figure.figsize"] = fig_size
        plt.ylabel('Amplitude (mV)')
        plt.xlabel('Time (s)')
        plt.title('ECG')
        #Basic data for plot
        SR = float(self.SampleRate)
        #Array for plot
        array_plot = np.tile(1.5 * np.arange(0, len(self.lead)), (np.shape(self.data)[0], 1))
        #Plot data (Plot len of leads in self.leads)
        for nleads in range(len(self.lead)):
            N = len(self.scaleddata[(self.lead[nleads])]);
            t = np.linspace(0, N / SR, N, endpoint=False)
            toplot = self.scaleddata[(self.lead[nleads])]
            self.ax.plot(t,toplot+array_plot[:N,nleads]) #, label='Lead'
            self.ax.annotate(self.labels[nleads], xy=(0.5, array_plot[0, nleads]), xytext=(0.5, array_plot[0, nleads]+0.2), fontsize=12)
            self.plot_checkboxstate_peaks = self.plot_peaks.checkState()
            if self.plot_checkboxstate_peaks==2: #Peaks
                for idx, peakinfo in enumerate(self.ecgpeaks[self.lead[nleads]]):
                    self.ax.plot(peakinfo[0], peakinfo[1] + nleads*1.5, 'md')  # Plot peaks label=self.labels[self.lead]

                plt.legend(bbox_to_anchor=(0.3, 1.02, 0.7, .102), loc=1, ncol=1, mode="None", markerscale=0.7, fontsize=8)

            #Anotate ST Elevation values
            self.ax.annotate(self.st_amp_lead[self.lead[nleads]], xy=(1.5, array_plot[0, nleads]),xytext=(1.5, array_plot[0, nleads] + 0.2), fontsize=12)

                #Plot as ECG
        spacingmayor = np.arange(0, (N / SR), 1)  # Every second
        #spacingminor = np.arange(0, (N / self.SampleRate), 0.2)  # Every 0,2 seconds
        self.ax.set_xticks(spacingmayor)
        #self.ax.set_xticks(spacingminor, minor=True)
        self.ax.grid(which='both')
        #self.ax.grid(which='minor', alpha=0.5, lw=1)
        self.ax.grid(which='major', alpha=0.8, lw=2)
        #Plot reference line
        self.line,=plt.plot([0.1, 0.1], [-1.0, len(self.lead)*1.5], color='k', linestyle='-', linewidth=2)

        self.canvas.draw()

    def sr_dropmenu_select(self, index): #Index is the name of index 0 in de dropdown menu
        if index == '500.0':
            self.selectedsr = index
            self.SampleRate = index
            self.SampleRate= float(self.SampleRate)
        if index == '1000.0':
            self.selectedsr = index
            self.SampleRate = index
            self.SampleRate = float(self.SampleRate)

    def leads_dropmenu_select(self, index):
        #print 'leads dropdown'
        if index == 'All leads':
            self.lead = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
            self.labels = ["I", "II", "III", "AVR", "AVL", "AVF","V1", "V2", "V3", "V4", "V5", "V6"]
            self.plot_ecg()
        if index == 'Frontal plane':
            self.lead=[0,1,2,3,4,5]
            self.labels = ["I", "II", "III", "AVR", "AVL", "AVF"]
            self.plot_ecg()
        if index == 'Horizontal plane':
            self.lead = [6, 7, 8, 9, 10, 11]
            self.labels = ["V1", "V2", "V3", "V4", "V5", "V6"]
            self.plot_ecg()
        if index == 'Lateral leads':
            self.lead = [0,4,10,11]
            self.labels = ["I", "aVL", "V5", "V6"]
            self.plot_ecg()
        if index == 'Inferior leads':
            self.lead = [1,2,5]
            self.labels = ["II", "III", "aVF"]
            self.plot_ecg()
        if index == 'Anterior leads':
            self.lead = [8,9]
            self.labels = ["V3", "V4"]
            self.plot_ecg()
        if index == 'Septal leads':
            self.lead = [6,7]
            self.labels = ["V1", "V2"]
            self.plot_ecg()
        if index == 'I':
            self.lead = [0]
            self.labels=["I"]
            self.plot_ecg()
        if index == 'II':
            self.lead = [1]
            self.labels = ["II"]
            self.plot_ecg()
        if index == 'III':
            self.lead = [2]
            self.labels = ["III"]
            self.plot_ecg()
        if index == 'AVR':
            self.lead = [3]
            self.labels = ["AVR"]
            self.plot_ecg()
        if index == 'AVL':
            self.lead = [4]
            self.labels = ["AVL"]
            self.plot_ecg()
        if index == 'AVF':
            self.lead = [5]
            self.labels = ["AVF"]
            self.plot_ecg()
        if index == 'V1':
            self.lead = [6]
            self.labels = ["V1"]
            self.plot_ecg()
        if index == 'V2':
            self.lead = [7]
            self.labels = ["V2"]
            self.plot_ecg()
        if index == 'V3':
            self.lead = [8]
            self.labels = ["V3"]
            self.plot_ecg()
        if index == 'V4':
            self.lead = [9]
            self.labels = ["V4"]
            self.plot_ecg()
        if index == 'V5':
            self.lead = [10]
            self.labels = ["V5"]
            self.plot_ecg()
        if index == 'V6':
            self.lead = [11]
            self.labels = ["V6"]
            self.plot_ecg()

    def db_dropmenu_select(self, index):
        if index == 'Mac2000':
            self.selecteddb = index
            self.db = 'm'
        if index == 'Physionet':
            self.selecteddb = index
            self.db = 'p'

    def son_dropmenu_select(self, index):
        if index == 'Water':
            self.selectedson = 'Water'
            self.interaction_layout_1()
        if index == 'Morph':
            self.selectedson = 'Morph'
            self.interaction_layout_2()

    def analyze_ecg(self): #data, samplerate, db

        if len(self.data) == 0:
            print("Upload an ECG file")

        else:

            SR= float(self.SampleRate)
            db= str(self.db)

            # Select only the first 10 seconds of data
            if self.filedur > 10.0:
                datatrimmed = self.data[:int(self.SampleRate * 10)]  # Cuts data to only 10 seconds from the start

                #after selecting only 10 seconds of data
                self.filedur = np.shape(datatrimmed)[0] / self.SampleRate
                self.data = datatrimmed

            # Cut files to 10 seconds
            self.filedur = np.shape(self.data)[0] / self.SampleRate


            self.ecgpeaks = [None] * (self.num_leads)
            self.endvalues = [None] * (self.num_leads)
            self.isomeans = [None] * (self.num_leads)
            RR = [None] * (self.num_leads)
            minRR = [None] * (self.num_leads)
            self.maxstduration = [None] * (self.num_leads)
            self.stsegmentdur = [None] * (self.num_leads)
            self.minstduration = [None] * (self.num_leads)
            self.scaleddata = [None] * (self.num_leads)
            self.st_amp_qrs = [None] * (self.num_leads)
            self.stcalcrange = [None] * (self.num_leads)
            self.stselection = [None] * (self.num_leads)
            self.st_amp_all_data = [None] * (self.num_leads)  # Average amp value of st in lead
            self.st_amp_lead = [None] * (self.num_leads) # Average amp value of st in lead
            self.min_amp = [None] * (self.num_leads)  # Min amp value of ST in lead
            self.max_amp = [None] *(self.num_leads) # Max amp value of ST in lead
            self.dt = [None] * (self.num_leads)
            self.amp_R_peak = [None] * (self.num_leads)
            self.st_stats = [None] * (self.num_leads) # Max value (T wave amp) and variance
            self.st_extracted = [None] * (self.num_leads)
            self.hr =  [None] * (self.num_leads)


            for i in range(self.num_leads):
                self.scaleddata[i] = ecgpro.amplitude_scaling(self.data[:,i], SR, db)
                self.ecgpeaks[i] = ecgpro.find_R_peaks_onechannel(self.scaleddata[i], SR, fc1=0.5, fc2=70.0)
                self.st_amp_all_data[i], self.hr[i] = ecgpro.st_amplitude_one_lead(self.scaleddata[i], SR, fc1=0.5, fc2= 100)
                self.st_amp_lead[i] = np.mean(self.st_amp_all_data[i]) #ST amp in lead


            #Check how many contiguous leads are elevated
            self.contiguous_leads(self.st_amp_lead)
            #Plot ECG graph
            self.plot_ecg()


    def contiguous_leads(self, ovampleads):

        self.wind_state = 0 #Initial state for ambient sounds
        self.thund_state = 0
        self.rain_state = 0

        inf_pln= [1,2,5]; inf_pln_bin=[]; inf_pln_cnt=0
        for idx, val in enumerate(inf_pln):
            if (self.st_amp_lead[val] >0.1):
                inf_pln_bin.append(1)
                inf_pln_cnt=inf_pln_cnt+1
            else:
                inf_pln_bin.append(0)

        ant_pln = [6, 7, 8,9]; ant_pln_bin = []; ant_pln_cnt=0
        for idx, val in enumerate(ant_pln):
            if (self.st_amp_lead[val] > 0.1):
                ant_pln_bin.append(1)
                ant_pln_cnt = ant_pln_cnt+1
            else:
                ant_pln_bin.append(0)

        ltl_pln=[0,4,10,11];ltl_pln_bin=[];ltl_pln_cnt=0
        for idx, val in enumerate(ltl_pln):
            if (self.st_amp_lead[val] > 0.1):
                ltl_pln_bin.append(1)
                ltl_pln_cnt=ltl_pln_cnt+1
            else:
                ltl_pln_bin.append(0)

        if (inf_pln_cnt>=2): #Inf leads + River sound
            self.rain_state = 1
        if (ant_pln_cnt>=2): #Anterior leads = wind sound
            self.wind_state = 1
        if (ltl_pln_cnt>=2): #ltl leads = thunder sound
            self.thund_state = 1

        self.total_pln_cnt = 0
        self.total_pln_cnt = ltl_pln_cnt+ant_pln_cnt+inf_pln_cnt

        ## To check number of leads elevated in each group of leads:
        # print ('Result of contiguity in inferior, anterior, lateral leads')
        # print (inf_pln_bin)
        # print (ant_pln_bin)
        # print (ltl_pln_bin)


    def play_sonification(self):

        if len(self.data) == 0:
            print("First upload an ECG file")

        else:

            self.playing = True
            self.vsstate=0
            self.son_morph_state= 0
            self.son_water_state = 0
            SR = float(self.SampleRate)
            db = str(self.db)
            numofleads= len(self.lead[0:])


            if self.selectedson == 'Water':
                #Create sonification thread: Water ambience
                self.son_thr = rson(self.selectedson, self.ecgpeaks,self.st_amp_lead,self.st_amp_all_data,numofleads,self.pl_stretch_water,self.wind_state, self.thund_state, self.rain_state, self, self.RpeakUpperFreqRange, self.TwaveUpperFreqRange,self.total_pln_cnt, self.pl_stretch_morph, self.SoundEventsDur)
                # Start thread
                self.son_thr.start()

            elif self.selectedson == 'Morph':

                # Create sonification thread: Morph
                self.son_thr = rson(self.selectedson, self.ecgpeaks,self.st_amp_lead,self.st_amp_all_data,numofleads,self.pl_stretch_water,self.wind_state, self.thund_state, self.rain_state, self, self.RpeakUpperFreqRange, self.TwaveUpperFreqRange,self.total_pln_cnt, self.pl_stretch_morph, self.SoundEventsDur)
                # Start thread
                self.son_thr.start()

    def stop_sonification(self):

        if len(self.data) == 0:
            print("First upload an ECG file")

        else:

            self.playing = False
            self.son_thr.stop()
            self.vsstate = 1
            self.son_morph_state = 1
            self.son_water_state = 1

    def plot_update(self, currentpeak, waitingtime):
        self.plotted_peak=currentpeak
        self.line.set_xdata([self.plotted_peak, self.plotted_peak])


if __name__ == '__main__':
    ecgguiapp = QtWidgets.QApplication(sys.argv)

    main = Window()
    SONM.set_gui(main)
    main.show()

    sys.exit(ecgguiapp.exec_())