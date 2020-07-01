// First step: boot the server
s.boot;
//s.reboot; // To rebook the server
//s.freeAll; // To free used nodes


//Load audio files -- Load audio files -- Load audio files -- Load audio files
(
(
~dirpath = Document.current.dir;
~bf1 = Buffer.readChannel(s,~dirpath++"/sounds/Drop_Main.wav",channels:[0], bufnum:0);
~bf10 = Buffer.read(s,~dirpath++"/sounds/Wind_Main_02.wav",bufnum:10);
~bf11 = Buffer.read(s,~dirpath++"/sounds/Thunder_Main_02.wav",bufnum:11);
~bf12 = Buffer.read(s,~dirpath++"/sounds/Rain_Main_02.wav",bufnum:12);
);
)
//Define Water ambience and ambience sounds synths -- Define Water ambience and ambience sounds synths
(
(
SynthDef(\play_water_sound, {
	arg amp=1, out=0, rate=1, pan=0, envc=50, buf;
	var signal;
	signal= PlayBuf.ar(1,buf, BufRateScale.kr(buf) * rate* //monobuffer
	EnvGen.kr(Env.perc(0.02, (~bf1.duration-0.05), 1, curve:envc)), doneAction:2);  //8//10
	signal=Pan2.ar(signal * amp, pan);
	OffsetOut.ar(out,signal);
}).send(s);
);

(//AmbienceSounds synth
SynthDef(\ambience_synth_wind, {
	arg amp=1,out=0, rate=1, envc=50, bufamb=10;
	var signal, env;
	signal = PlayBuf.ar(2, 10, BufRateScale.kr(bufamb));
	env= EnvGen.kr(Env.perc(0.02, (~bf12.duration-0.05), 1, curve:envc), doneAction:2);
	signal=(signal * env * amp);
	OffsetOut.ar(out,signal);
}).send(s);
);
(//AmbienceSounds synth
SynthDef(\ambience_synth_thund, {
	arg amp=1,out=0, rate=1, envc=50, bufamb=11;
	var signal, env;
	signal = PlayBuf.ar(2, 11, BufRateScale.kr(bufamb));
	env= EnvGen.kr(Env.perc(0.02, (~bf12.duration-0.05), 1, curve:envc), doneAction:2);
	signal=(signal * env * amp);
	OffsetOut.ar(out,signal);
}).send(s);
);
(//AmbienceSounds synth
SynthDef(\ambience_synth_rain, {
	arg amp=1,out=0, rate=1, envc=50, bufamb=12;
	var signal, env;
	signal = PlayBuf.ar(2, 12, BufRateScale.kr(bufamb));
	env= EnvGen.kr(Env.perc(0.02, (~bf12.duration-0.05), 1, curve:envc), doneAction:2);
	signal=(signal * env * amp);
	OffsetOut.ar(out,signal);
}).send(s);
);
)
//Test water ambience and ambience sounds synths:
Synth.new("\play_water_sound")
Synth.new("\ambience_synth_wind")



//Define morph synth -- Define morph synth -- Define morph synth

(
(//Main morphing synth
SynthDef(\morph_synth, {
	arg  vf=200, vrate=1, vdepth=1, smul=0.5, out=0, morphf=0.5, strfactor=1, soundeventdur=0.6;
	var signalA, signalB, envA, envB, mix;

	signalA=LFPulse.ar(freq:Vibrato.kr(freq:vf, rate:vrate,depth:vdepth), width:0.5,mul:smul);
	//envA=EnvGen.kr(Env.perc(attackTime: 0.2*strfactor, releaseTime: 0.4*strfactor, level: 0.7, curve: -7), doneAction:2);
	envA=EnvGen.kr(Env.perc(attackTime: (soundeventdur*0.35)*strfactor, releaseTime: (soundeventdur*0.65)*strfactor, level: 0.7, curve: -7), doneAction:2);

	signalA=signalA * envA;

    signalB= SinOsc.ar(freq:Vibrato.kr(freq:vf, rate:vrate,depth:vdepth) , mul:smul);
	//envB=EnvGen.kr(Env.perc(attackTime: 0.2*strfactor, releaseTime: 0.4*strfactor, level: 0.7, curve: -7), doneAction:2);
	envB=EnvGen.kr(Env.perc(attackTime: (soundeventdur*0.35)*strfactor, releaseTime:  (soundeventdur*0.65)*strfactor, level: 0.7, curve: -7), doneAction:2);
	signalB=signalB * envB;


	mix = (signalA*morphf) + ((1-morphf)*signalB);
	OffsetOut.ar(out,mix!2
	);
}).send(s);
);
)
//Test Morph synth
Synth.new(\morph_synth,[\vf,400,\morphf,0.5,\vrate,1.0, \vdepth,1])




