# Trailer score, synthesised. 100 bpm (mid tempo), D minor, serious. 36 s, stereo 44.1 kHz.
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile
SR=44100; BT=0.6; N=int(36*SR); rng=np.random.default_rng(3)
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

# low drone all the way
t=np.arange(N)/SR
dr=lp(saw(hz(26),36,(-6,0,5))+0.6*saw(hz(38),36,(-4,3)),170)*(0.55+0.25*np.sin(2*np.pi*t/7.2))
dr*=np.minimum(1,t/2.5)*np.minimum(1,(36-t)/3); add(dr,0,0,0.5)
# act 1: sparse and serious
braam(0,0.8); pad((50,57,62),0.6,4.2,0.5); boom(5*BT,0.7); braam(5*BT,0.55,3)
# act 2: the sphere
boom(8*BT); braam(8*BT,1.0); pad((50,57,62,65),8*BT,4.8,0.9); pad((46,53,58,65),12*BT,4.8*0.5+2.4,0.9)
# pulse: steady eighth notes from beat 8, opening up as it builds
for b in np.arange(8,32,0.5):
    k=(b-8)/24; m=38 if int(b*2)%8 not in (6,7) else 36
    pluck(m,b*BT,0.6+0.6*k,500+2200*k); 
    if b>=16: pluck(m+12,b*BT,0.35+0.4*k,700+2500*k,0.4 if int(b*2)%2 else -0.4)
boom(16*BT,0.8); hit(16*BT)
for b in (17.5,18,19,19.5): hit(b*BT,0.6,0.3)
# act 3: flash cuts
chords=[(50,57,62),(46,53,58),(53,57,60),(48,55,60),(50,57,62),(45,52,57)]
for i in range(6):
    b=20+2*i; boom(b*BT,0.95); braam(b*BT,0.5+0.07*i,1.6); whoosh(b*BT); pad(tuple(m+12 for m in chords[i]),b*BT,1.3,0.6+0.08*i)
    hit((b+1)*BT,0.7,-0.3); hit((b+1.5)*BT,0.55,0.3)
    if i>=3: hit((b+0.5)*BT,0.5); hit((b+1.75)*BT,0.5,0.2)
# breath, riser, then silence just before the title
riser(32*BT,4*BT-0.13,1.0)
for j,b in enumerate(np.arange(34,36,0.25)): hit(b*BT,0.3+0.08*j)
i0=int((36*BT-0.13)*SR); i1=int(36*BT*SR); L[i0:i1]*=0.0; R[i0:i1]*=0.0
# title: the big chord, Dm - Bb - F - C, then home
boom(36*BT,1.2); braam(36*BT,1.2,6)
prog=[(50,57,62,65,69),(46,53,58,62,65),(53,57,60,65,69),(48,55,60,64,67)]
for i,c in enumerate(prog):
    b=36+i*3.5; pad(c,b*BT,3.5*BT+0.5,1.15); pad(tuple(m+12 for m in c[:3]),b*BT,3.5*BT+0.5,0.5); hit(b*BT,0.9)
    for e in np.arange(0,3.5,0.5): pluck(c[0]-12,(b+e)*BT,0.8,1500)
    for e in (1.5,2.5,3.0): hit((b+e)*BT,0.5,0.3)
# end card
boom(50*BT,1.0); braam(50*BT,0.9,6); pad((50,57,62,65,69),50*BT,5.5,1.0); pad((62,69,74),50*BT,5.5,0.4)
for e in (0,2,4): pluck(38,(50+e)*BT,0.6,900)
# space: simple hall reverb
def verb(x):
    n=int(2.6*SR); ir=rng.normal(0,1,n)*np.exp(-np.arange(n)/SR*2.4); ir=lp(ir,5000); ir/=np.sqrt((ir**2).sum())
    return fftconvolve(x,ir)[:N]
L2=L+0.30*verb(L); R2=R+0.30*verb(R)
mix=np.stack([L2,R2],1); mix=np.tanh(mix*1.25)
mix/=np.abs(mix).max()/0.97
fo=np.minimum(1,(36-t)/2.0)[:,None]; mix*=fo
wavfile.write('score.wav',SR,(mix*32767).astype(np.int16)); print('ok',mix.shape)
