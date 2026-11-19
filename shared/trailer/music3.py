# Trailer score, synthesised. 100 bpm (mid tempo), D minor, serious. 36 s, stereo 44.1 kHz.
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR=44100; BT=0.6; N=int(76.8*SR); rng=np.random.default_rng(3)
L=np.zeros(N); R=np.zeros(N)
def hz(m): return 440*2**((m-69)/12)
def lp(x,f,o=4): return sosfilt(butter(o,f,fs=SR,output='sos'),x)
def hp(x,f,o=2): return sosfilt(butter(o,f,btype='high',fs=SR,output='sos'),x)
def add(x,at,pan=0.0,g=1.0):
    i=int(at*SR); x=x[:max(0,N-i)]
    if i<0 or len(x)==0: return
    L[i:i+len(x)]+=x*g*(1-max(0,pan)); R[i:i+len(x)]+=x*g*(1+min(0,pan))
def saw(f,d,det=(0,)):
    t=np.arange(int(d*SR))/SR; o=np.zeros(len(t))
    for c in det: ff=f*2**(c/1200); o+=2*((t*ff)%1)-1
    return o/len(det)
def env(n,a,r):
    t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-np.maximum(0,t-a)/r)
def braam(at,g=1.0,d=4.5):
    x=sum(saw(hz(m),d,(-14,-5,0,6,13)) for m in (26,38,45))    # D1 D2 A2
    x=np.tanh(lp(x,650)*2.2)*env(len(x),0.03,1.5); add(x,at,0,0.33*g)
def boom(at,g=1.0):
    t=np.arange(int(2.2*SR))/SR; f=38+85*np.exp(-t*20)
    x=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*2.6)
    n=lp(rng.normal(0,1,len(t)),1800)*np.exp(-t*16)*0.6
    add(np.tanh((x+n)*1.5),at,0,0.6*g)
def hit(at,g=1.0,pan=0.0):   # taiko-like
    t=np.arange(int(0.7*SR))/SR; f=70+70*np.exp(-t*35)
    x=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*8)+lp(rng.normal(0,1,len(t)),900)*np.exp(-t*30)*0.5
    add(x,at,pan,0.42*g)
def pluck(m,at,g=1.0,cut=900,pan=0.0):
    x=lp(saw(hz(m),0.5,(-7,0,7)),cut)*env(int(0.5*SR),0.004,0.11); add(x,at,pan,0.22*g)
def pad(ms,at,d,g=1.0):
    x=sum(saw(hz(m),d,(-9,0,8)) for m in ms)/len(ms)
    n=len(x); e=np.minimum(1,np.arange(n)/SR/0.5)*np.minimum(1,(n-np.arange(n))/SR/0.6)
    x=lp(x,1500)*e; add(x,at,-0.25,0.20*g); add(np.roll(x,400),at,0.25,0.20*g)
def riser(at,d,g=1.0):
    t=np.arange(int(d*SR))/SR; u=t/d
    n=hp(rng.normal(0,1,len(t)),400)*u**2
    s=np.sin(2*np.pi*np.cumsum(hz(50)*2**(u*2.2))/SR)*u**1.5*0.5
    add(lp(n,9000)*0.5+s,at,0,0.33*g)
def whoosh(at,g=1.0):
    t=np.arange(int(0.5*SR))/SR; x=hp(rng.normal(0,1,len(t)),1500)*np.sin(np.pi*t/0.5)**3; add(x,at-0.3,0,0.13*g)


TOT=76.8
def hat(at,g=1.0,pan=0.0):
    t=np.arange(int(0.05*SR))/SR; add(hp(rng.normal(0,1,len(t)),7000)*np.exp(-t*90),at,pan,0.09*g)
def snare(at,g=1.0):
    t=np.arange(int(0.25*SR))/SR
    x=hp(rng.normal(0,1,len(t)),1200)*np.exp(-t*22)+0.5*np.sin(2*np.pi*190*t)*np.exp(-t*30); add(x,at,0,0.22*g)
def arp(ms,at,beats,g=1.0):
    seq=[ms[0]+12,ms[2]+12,ms[1]+24,ms[2]+12]
    for j in range(int(beats*4)): pluck(seq[j%4]+ (12 if j%8>=4 else 0),at+j*BT/4,0.35*g,3200,0.5 if j%2 else -0.5)
def swell(at,d=1.2,g=1.0):      # reverse breath into a hit
    t=np.arange(int(d*SR))/SR; x=lp(rng.normal(0,1,len(t)),3000)*(t/d)**3; add(x,at-d,0,0.16*g)
def bell(m,at,g=1.0):
    t=np.arange(int(2.5*SR))/SR; f=hz(m)
    x=(np.sin(2*np.pi*f*t)+0.4*np.sin(2*np.pi*f*2.01*t)+0.2*np.sin(2*np.pi*f*3.02*t))*np.exp(-t*2.2); add(x,at,0.2,0.10*g)
t=np.arange(N)/SR
dr=lp(saw(hz(26),TOT,(-6,0,5))+0.6*saw(hz(38),TOT,(-4,3)),160)*(0.5+0.2*np.sin(2*np.pi*t/7.2))
dr*=np.minimum(1,t/2.5)*np.minimum(1,(TOT-t)/3); add(dr,0,0,0.38)
# calm, serious opening
pad((50,57,62,65),0,5.2,0.7); bell(74,0.3,0.8); bell(69,2.7,0.7)
# Meet Nova
swell(8*BT); boom(8*BT,0.9); braam(8*BT,0.75,4); pad((50,57,62,65,69),8*BT,4.9,0.9); pad((62,69,74),8*BT,4.9,0.35); bell(81,8*BT,1.0); bell(77,10*BT,0.8)
# the Mac, the notch: pulse begins
swell(16*BT); boom(16*BT,0.8); hit(16*BT); pad((46,53,58,62),16*BT,4.9,0.85)
swell(24*BT); boom(24*BT,0.85); hit(24*BT); pad((53,57,60,65),24*BT,4.9,0.9); arp((53,57,60),24*BT,8,0.6)
for b in np.arange(16,68,0.5):
    k=min(1,(b-16)/40); m=38 if int(b*2)%8 not in (6,7) else 36
    pluck(m,b*BT,0.55+0.5*k,600+2000*k)
    if b>=24: pluck(m+12,b*BT,0.3+0.4*k,800+2400*k,0.4 if int(b*2)%2 else -0.4)
for b in np.arange(24,32,1): hit((b+0.5)*BT,0.35,0.3)
# six features
chords=[(50,57,62,65),(46,53,58,62),(53,57,60,65),(48,55,60,64),(50,57,62,65),(45,52,57,61)]
for i in range(6):
    b=32+6*i; swell(b*BT,0.8,0.8); boom(b*BT,0.9); braam(b*BT,0.45+0.06*i,2.0); whoosh(b*BT)
    pad(chords[i],b*BT,6*BT+0.3,0.75+0.05*i); pad(tuple(m+12 for m in chords[i][:3]),b*BT,6*BT+0.3,0.35+0.05*i)
    arp(chords[i],b*BT,6,0.5+0.08*i)
    for e in (1,2,3,4,5): hit((b+e)*BT,0.45+0.04*i,0.3 if e%2 else -0.3)
    for e in np.arange(0,6,0.5): hat((b+e)*BT,0.6+0.1*i,0.3 if int(e*2)%2 else -0.3)
    if i>=3:
        for e in (2.5,4.5,5.5): hit((b+e)*BT,0.4)
        for e in (1,3,5): snare((b+e)*BT,0.7)
# "and so much more": lift
swell(68*BT); boom(68*BT,1.0); pad((46,53,58,62,65),68*BT,2.6,1.0); arp((46,53,58),68*BT,4,0.8)
for b in np.arange(68,72,0.5): pluck(34,b*BT,1.0,2400); hat(b*BT,0.9)
for j,b in enumerate(np.arange(71,72,0.25)): snare(b*BT,0.5+0.12*j)
# montage: a hit on every beat, driving
mch=[(50,57,62),(50,57,62),(46,53,58),(46,53,58),(53,57,60),(53,57,60),(48,55,60),(48,55,60),(50,57,62),(53,57,60),(46,53,58),(45,52,57)]
for i in range(12):
    b=72+i; boom(b*BT,0.75); hit(b*BT,0.9); whoosh(b*BT,0.8); pad(tuple(m+12 for m in mch[i]),b*BT,BT+0.15,0.9)
    pluck(mch[i][0]-12,b*BT,1.1,2600); pluck(mch[i][0]-12,(b+0.5)*BT,0.9,2600)
    for e in (0,0.25,0.5,0.75): hat((b+e)*BT,1.0,0.3 if int(e*4)%2 else -0.3)
    if i%2: snare(b*BT,0.9)
    hit((b+0.5)*BT,0.5,0.3)
# where it runs, then the whole app
swell(84*BT); boom(84*BT,1.0); braam(84*BT,0.7,3); pad((50,57,62,65,69),84*BT,4.9,1.0); arp((50,57,62),84*BT,8,0.7)
swell(92*BT); boom(92*BT,1.0); hit(92*BT); pad((46,53,58,62,65),92*BT,4.9,1.0); pad((58,65,70),92*BT,4.9,0.5); arp((46,53,58),92*BT,8,0.8)
for b in np.arange(84,100,0.5): pluck(38 if b<92 else 34,b*BT,0.9,2200); hat(b*BT,0.8,0.3 if int(b*2)%2 else -0.3)
for b in np.arange(85,100,2): snare(b*BT,0.6)
# build, then a breath of silence
riser(100*BT,4*BT-0.12,1.0)
for j,b in enumerate(np.arange(102,104,0.25)): hit(b*BT,0.3+0.08*j); snare(b*BT,0.3+0.06*j)
i0=int((104*BT-0.11)*SR); i1=int(104*BT*SR); L[i0:i1]*=0.0; R[i0:i1]*=0.0
# title: Dm - Bb - F - C
boom(104*BT,1.25); braam(104*BT,1.2,6)
prog=[(50,57,62,65,69),(46,53,58,62,65),(53,57,60,65,69),(48,55,60,64,67)]
for i,c in enumerate(prog):
    b=104+i*3; pad(c,b*BT,3*BT+0.5,1.15); pad(tuple(m+12 for m in c[:3]),b*BT,3*BT+0.5,0.55); hit(b*BT,0.95); bell(c[2]+24,b*BT,1.0)
    arp(c,b*BT,3,0.9)
    for e in np.arange(0,3,0.5): pluck(c[0]-12,(b+e)*BT,0.8,1500); hat((b+e)*BT,0.8)
    for e in (1,2): snare((b+e)*BT,0.7)
    for e in (1.5,2.5): hit((b+e)*BT,0.5,0.3)
# end card
boom(116*BT,1.0); braam(116*BT,0.9,6); pad((50,57,62,65,69),116*BT,6.8,1.0); pad((62,69,74),116*BT,6.8,0.4); bell(86,116*BT,1.0); bell(81,118*BT,0.8); bell(74,120*BT,0.7)
for e in (0,2,4,6): pluck(38,(116+e)*BT,0.6,900)
def verb(x):
    n=int(2.6*SR); ir=rng.normal(0,1,n)*np.exp(-np.arange(n)/SR*2.4); ir=lp(ir,5000); ir/=np.sqrt((ir**2).sum())
    return fftconvolve(x,ir)[:N]
L2=L+0.30*verb(L); R2=R+0.30*verb(R)
mix=np.tanh(np.stack([L2,R2],1)*1.15); mix/=np.abs(mix).max()/0.97
mix*=np.minimum(1,(TOT-t)/2.2)[:,None]
wavfile.write('score3.wav',SR,(mix*32767).astype(np.int16)); print('ok',mix.shape)
