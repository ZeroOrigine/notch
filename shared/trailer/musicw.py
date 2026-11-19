# Calm, premium score for the white ad: piano, warm strings pad, soft pulse. 72 bpm, D major, 108 beats = 90 s.
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR=44100; BT=60/72; TOT=108*BT; N=int(TOT*SR); rng=np.random.default_rng(5)
L=np.zeros(N); R=np.zeros(N)
def hz(m): return 440*2**((m-69)/12)
def lp(x,f,o=4): return sosfilt(butter(o,f,fs=SR,output='sos'),x)
def hp(x,f,o=2): return sosfilt(butter(o,f,btype='high',fs=SR,output='sos'),x)
def add(x,at,pan=0.0,g=1.0):
    i=int(at*SR); x=x[:max(0,N-i)]
    if i<0 or len(x)==0: return
    L[i:i+len(x)]+=x*g*(1-max(0,pan)); R[i:i+len(x)]+=x*g*(1+min(0,pan))
def piano(m,at,vel=0.6,dur=3.5):
    f=hz(m); t=np.arange(int(dur*SR))/SR; x=np.zeros(len(t)); B=0.0004
    for k,a in enumerate([1,0.55,0.30,0.16,0.09,0.05,0.03],1):
        fk=f*k*np.sqrt(1+B*k*k)
        if fk>9000: break
        x+=a*(vel**(0.5+0.25*k))*np.sin(2*np.pi*fk*t+rng.uniform(0,6.28))*np.exp(-t*(0.9+0.5*k)*(1+f/900))
    x+=lp(rng.normal(0,1,len(t)),2500)*np.exp(-t*90)*0.08*vel          # hammer
    x*=np.minimum(1,t/0.004)
    add(x,at,(m-64)/40,0.22*vel)
def pad(ms,at,d,g=1.0):
    t=np.arange(int(d*SR))/SR; x=np.zeros(len(t))
    for m in ms:
        for c in (-7,0,6): x+=2*((t*hz(m)*2**(c/1200))%1)-1
    e=np.minimum(1,t/1.6)*np.minimum(1,(d-t)/1.8)
    x=lp(x/len(ms),900)*e; add(x,at,-0.3,0.055*g); add(np.roll(x,600),at,0.3,0.055*g)
def sub(m,at,d,g=1.0):
    t=np.arange(int(d*SR))/SR; add(np.sin(2*np.pi*hz(m)*t)*np.minimum(1,t/0.05)*np.minimum(1,(d-t)/0.4),at,0,0.16*g)
def tick(at,g=1.0,pan=0.0):
    t=np.arange(int(0.04*SR))/SR; add(hp(rng.normal(0,1,len(t)),6000)*np.exp(-t*120),at,pan,0.03*g)
def swell(at,d,g=1.0):
    t=np.arange(int(d*SR))/SR; add(lp(hp(rng.normal(0,1,len(t)),800),5000)*(t/d)**3,at-d,0,0.05*g)

#           root  chord tones (mid)      colour
PROG=[(38,(62,66,69,76)),(35,(62,66,69,74)),(31,(59,62,66,74)),(33,(61,64,69,76))]     # D, Bm, G, A
MEL=[78,None,76,74, 73,None,74,None, 71,None,74,76, 73,None,69,None]                  # one note per beat over four bars
def level(beat):   # how full the arrangement is
    if beat<8: return 0.0
    if beat<18: return 0.35
    if beat<30: return 0.5
    if beat<78: return 0.6+0.3*(beat-30)/48
    if beat<94: return 0.85
    if beat<102: return 1.0
    return 0.5
# opening: a few single notes in the quiet
for b,m,v in [(0,74,0.5),(2,69,0.42),(4,76,0.5),(5.5,73,0.4),(6.5,69,0.38)]: piano(m,b*BT,v,5)
pad((50,57,62),0,8*BT+1,0.6)
for bar in range(2,27):
    b0=bar*4; root,ch=PROG[bar%4]; lv=level(b0); t0=b0*BT
    pad((root+12,ch[0],ch[1],ch[2]),t0,4*BT+1.2,0.7+0.9*lv)
    piano(root,t0,0.5+0.25*lv,5); piano(root+12,t0,0.35+0.2*lv,4)
    if lv>=0.5: piano(root+7,t0+2*BT,0.35+0.15*lv,3); sub(root,t0,4*BT,0.5+0.5*lv)
    arp=[ch[0],ch[1],ch[2],ch[1],ch[3],ch[2],ch[1],ch[2]]
    for j,m in enumerate(arp):
        if lv<0.4 and j%2: continue
        piano(m,t0+j*BT/2,(0.30+0.22*lv)*(1.1 if j%4==0 else 0.85),2.5)
    if lv>=0.45:
        for j in range(4):
            m=MEL[(bar%4)*4+j]
            if m: piano(m+ (12 if lv>=1.0 else 0),t0+j*BT,0.45+0.25*lv,4)
    if lv>=0.6:
        for j in range(8): tick(t0+j*BT/2,(0.6+lv)*(1.0 if j%2 else 0.6),0.4 if j%2 else -0.4)
# a soft breath into each new chapter, and a fuller chord for the name
for b in (8,18,30,78,86,94,102): swell(b*BT,1.6,1.0 if b!=94 else 2.0)
for m,v in [(26,0.8),(38,0.8),(50,0.7),(62,0.75),(66,0.7),(69,0.7),(74,0.8),(81,0.7),(86,0.6)]: piano(m,94*BT,v,7)
pad((50,57,62,66,69,74),94*BT,8*BT+1,1.6); sub(26,94*BT,6*BT,1.0)
# last chord, left to ring
for m,v in [(26,0.6),(38,0.6),(57,0.5),(62,0.55),(66,0.5),(74,0.55),(78,0.5)]: piano(m,104*BT,v,6)
def verb(x):
    n=int(3.2*SR); ir=rng.normal(0,1,n)*np.exp(-np.arange(n)/SR*1.9); ir=lp(ir,4500); ir/=np.sqrt((ir**2).sum())
    return fftconvolve(x,ir)[:N]
L2=L+0.38*verb(L); R2=R+0.38*verb(R)
mix=np.tanh(np.stack([L2,R2],1)*1.1); mix/=np.abs(mix).max()/0.92
t=np.arange(N)/SR; mix*=(np.minimum(1,t/0.3)*np.minimum(1,(TOT-t)/3.0))[:,None]
wavfile.write('scorew.wav',SR,(mix*32767).astype(np.int16)); print('ok',TOT)
