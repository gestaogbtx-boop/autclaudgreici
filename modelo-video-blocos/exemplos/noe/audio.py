import numpy as np, wave
SR=44100; DUR=149.71; N=int(SR*DUR); rng=np.random.default_rng(7)
mus=np.zeros(N); sfx=np.zeros(N)
def put(buf,t,x,g=1.0):
    i=int(t*SR)
    if i>=N or i<0: return
    x=x[:N-i]; buf[i:i+len(x)]+=x*g
def env(n,a=0.005,d=1.0):
    t=np.arange(n)/SR; return np.minimum(t/a,1)*np.exp(-t/d)
def note(f,dur,kind='box',d=0.4):
    n=int(dur*SR); t=np.arange(n)/SR
    if kind=='box': x=np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*f*3.01*t)*np.exp(-t*8)+0.2*np.sin(2*np.pi*f*2*t)
    elif kind=='pluck': x=np.sign(np.sin(2*np.pi*f*t))*0.25+np.sin(2*np.pi*f*t)*0.8
    elif kind=='bass': x=np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t)
    else: x=np.sin(2*np.pi*f*t)+0.5*np.sin(2*np.pi*f*1.005*t)+0.3*np.sin(2*np.pi*f*2*t)
    return x*env(n,0.004 if kind!='pad' else 0.4,d)
def lp(x,k):
    y=np.cumsum(x); y[k:]=y[k:]-y[:-k]; return y/k
def noise(dur,k=1): 
    x=rng.standard_normal(int(dur*SR)); return lp(x,k) if k>1 else x
MIDI=lambda m:440*2**((m-69)/12)
CH={'C':[48,60,64,67,72],'Am':[45,57,60,64,69],'F':[41,57,60,65,69],'G':[43,59,62,67,71],'Dm':[38,57,62,65,69],'E':[40,56,59,64,68],'Em':[40,59,64,67,71]}
def section(t0,t1,prog,beat,kind,arp=(1,2,3,2,4,3,2,3),bass=False,pad=False,drum=None,g=1.0,octv=0):
    t=t0; b=0
    while t<t1-0.05:
        ch=CH[prog[(b//8)%len(prog)]]; s=b%8
        fade=min(1,(t-t0)/1.0+0.3,(t1-t)/1.2+0.15)
        if arp and arp[s] is not None: put(mus,t,note(MIDI(ch[arp[s]]+octv),1.2,kind,0.35 if kind=='box' else 0.22),0.5*g*fade)
        if s==0:
            if bass: put(mus,t,note(MIDI(ch[0]),beat*8,'bass',1.2),0.7*g*fade)
            if pad:
                for m in ch[1:4]: put(mus,t,note(MIDI(m),beat*8+0.5,'pad',2.5),0.16*g*fade)
        if bass and s==4: put(mus,t,note(MIDI(ch[0]+7),beat*4,'bass',0.8),0.5*g*fade)
        if drum=='soft' and s%4==0: put(mus,t,note(70,0.3,'bass',0.08),0.6*g*fade)
        if drum=='soft' and s%2==1: put(mus,t,noise(0.05)*env(int(0.05*SR),0.001,0.015),0.08*g*fade)
        if drum=='party':
            if s%4==0: put(mus,t,note(60,0.3,'bass',0.09),1.0*g*fade)
            if s%4==2: put(mus,t,noise(0.12)*env(int(0.12*SR),0.001,0.04),0.22*g*fade)
            put(mus,t,noise(0.04)*env(int(0.04*SR),0.001,0.012),0.07*g*fade)
        if drum=='storm' and s in (0,3,6): put(mus,t,note(52,0.5,'bass',0.2),0.9*g*fade)
        t+=beat; b+=1
B=0.3125
section(0,13.5,['Am','F','C','G'],B*2,'box',pad=True,g=0.8,octv=12)
section(13.5,25.6,['C','Am','F','G'],B,'box',pad=True,g=0.9,octv=12)
section(25.6,32.8,['Am','Dm','Am','E'],B*2,'pluck',arp=(0,None,2,None,1,None,2,None),bass=True,pad=True,g=0.9,octv=-12)
section(32.8,40.85,['C','G','Am','F'],B,'pluck',bass=True,pad=True,g=0.9)
section(40.85,52.9,['F','G','C','C'],B*2,'box',arp=(1,2,3,4,3,2,3,4),pad=True,g=0.9,octv=12)
section(52.9,64.7,['C','F','G','C'],B,'pluck',bass=True,pad=True,drum='soft')
section(64.7,84.4,['C','G','Am','F'],B,'pluck',arp=(1,3,2,3,4,3,2,3),bass=True,pad=True,drum='soft',g=1.05)
section(84.4,93.4,['Am','F','Dm','E'],B,'pluck',arp=(0,None,2,None,3,None,2,1),bass=True,pad=True,drum='storm',g=1.1,octv=-12)
section(93.4,99.9,['C','F'],B*2,'box',arp=(1,None,3,None,4,None,3,None),pad=True,g=0.8,octv=12)
section(99.9,114.5,['F','C','G','Am'],B*2,'box',arp=(1,2,3,2,4,3,2,3),pad=True,bass=True,g=0.9,octv=12)
section(114.5,127.1,['C','G','Am','F'],B,'pluck',bass=True,pad=True,drum='party',g=1.1,octv=12)
section(127.1,141.0,['C','Am','F','G'],B*2,'box',pad=True,g=0.9,octv=12)
section(141.0,149.5,['C','F','G','C'],B,'pluck',bass=True,pad=True,drum='party',g=1.15,octv=12)
# ---- sfx ----
def splash(dur=0.9,g=1.0,low=4):
    x=noise(dur,low)*env(int(dur*SR),0.01,dur/3.5); x+=noise(dur)*env(int(dur*SR),0.002,dur/7)*0.25; return x*g
def thud(f=70,d=0.12): n=int(0.4*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*f*t*np.exp(-t*6))*env(n,0.002,d)
def whoosh(dur=0.5,up=True):
    n=int(dur*SR); x=rng.standard_normal(n); t=np.arange(n)/n; out=np.zeros(n); k=0.0; a=0.02+0.25*(t if up else 1-t)
    for i in range(n): k+=a[i]*(x[i]-k); out[i]=k
    return out*np.sin(np.pi*t)**1.5*3
def chime(fs,d=0.6,gap=0.07):
    out=np.zeros(int((len(fs)*gap+d*4)*SR))
    for i,f in enumerate(fs): x=note(f,d*4,'box',d); j=int(i*gap*SR); out[j:j+len(x)]+=x
    return out
def pop(f=600): n=int(0.12*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(f+2500*t)*t)*env(n,0.002,0.03)
def squeak(): n=int(0.22*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(1500+900*np.sin(t*30))*t)*env(n,0.01,0.09)*0.6
def thunder(): n=int(2.2*SR); x=noise(2.2,60)*40; return x*env(n,0.02,0.7)*(1+0.5*np.sin(np.arange(n)/SR*23))
def tap(): return noise(0.06,3)*env(int(0.06*SR),0.001,0.015)*2+thud(160,0.03)[:int(0.06*SR)]*0.6
def creak(): n=int(0.5*SR); t=np.arange(n)/SR; return np.sign(np.sin(2*np.pi*(90+40*t)*t))*np.sin(2*np.pi*7*t)**2*env(n,0.05,0.3)*0.3

def rainbed(t0,dur,g,k=2):
    n=int(dur*SR); t=np.arange(n)/SR; e=np.minimum(t/0.6,1)*np.minimum((dur-t)/1.5,1); put(sfx,t0,noise(dur,k)*np.clip(e,0,1),g)
def yip(f=900): n=int(0.13*SR); t=np.arange(n)/SR; return (np.sign(np.sin(2*np.pi*(f+900*t)*t))*0.3+np.sin(2*np.pi*(f+900*t)*t))*env(n,0.004,0.04)
def trumpet(): n=int(0.9*SR); t=np.arange(n)/SR; f=330+260*np.sin(np.pi*t/0.9)**2; ph=np.cumsum(f)/SR*2*np.pi; return (np.sign(np.sin(ph))*0.4+np.sin(ph))*np.sin(np.pi*t/0.9)**0.6*0.6
def growl(): n=int(0.8*SR); t=np.arange(n)/SR; return lp(rng.standard_normal(n),30)*20*(1+np.sin(2*np.pi*38*t))*np.sin(np.pi*t/0.8)
def flap(): return noise(0.07,6)*8*env(int(0.07*SR),0.01,0.03)
def chirp(): n=int(0.1*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*(2600+1500*np.sin(t*60))*t)*env(n,0.005,0.04)*0.5
# room rain
rainbed(0,13.5,0.14,3); rainbed(13.5,12.1,0.07,5)
for i in range(22): put(sfx,0.3+i*0.6+rng.random()*0.3,tap(),0.18)
put(sfx,7.15,pop(900),0.4); put(sfx,16.0,whoosh(0.5),0.5); put(sfx,16.8,thud(200,0.03),0.4)
for i in range(7): put(sfx,17.65+i*0.24,tap(),0.45)
put(sfx,19.4,thud(90,0.08),0.6); put(sfx,20.7,whoosh(0.3),0.4); put(sfx,21.2,noise(0.15,2)*env(int(0.15*SR),0.005,0.05),0.5); put(sfx,24.0,whoosh(1.4),0.9); put(sfx,25.3,chime([1047,1319,1568,2093]),0.5)
# village
for i in range(8): put(sfx,26.1+i*0.23,tap(),0.4)
put(sfx,27.9,thud(80,0.12),1.2); put(sfx,27.92,noise(0.1,2)*env(int(0.1*SR),0.001,0.03),0.8)
for t0 in (28.3,28.8,29.2,29.7,30.1): put(sfx,t0,growl()[:int(0.35*SR)],0.5)
put(sfx,30.5,whoosh(0.3,False),0.5); put(sfx,30.9,thud(110,0.06),0.8)
# garden
for i in range(9): put(sfx,33.2+i*0.8+rng.random()*0.3,chirp(),0.4); put(sfx,33.5+i*0.8,chirp(),0.3)
for i in range(22): put(sfx,33.4+i*0.3,pop(1300+rng.integers(0,500)),0.12)
put(sfx,35.6,chime([784,988,1175],0.8,0.12),0.4)
put(sfx,41.1,chime([784,988,1175,1568,1976],0.9,0.12),0.5); n=int(2.4*SR); t=np.arange(n)/SR; put(sfx,44.5,np.sin(2*np.pi*55*t)*np.sin(np.pi*t/2.4)**2,0.8)
for i in range(34): put(sfx,47.4+i*0.13,note(MIDI(60+[0,2,4,7,9,12,14,16][i%8]+12*(i//16)),0.3,'box',0.08),0.25)
put(sfx,52.0,chime([1047,1319,1568,2093,2637],1.0,0.1),0.55)
# building
for i in range(16): put(sfx,53.3+i*0.7,noise(0.3,2)*np.sin(np.pi*np.arange(int(0.3*SR))/int(0.3*SR))*(1+np.sin(np.arange(int(0.3*SR))*0.09)),0.22)
for i in range(22): put(sfx,53.5+i*0.449,thud(210,0.03),0.55)
for t0 in (54.4,55.6,57.0,58.2,59.4,63.4,64.2): put(sfx,t0,whoosh(0.35,False),0.4); put(sfx,t0+0.33,thud(120,0.06),0.7)
for i in range(9): put(sfx,60.55+i*0.2,yip(520-i*18),0.35)
for i in range(5): put(sfx,62.85+i*0.3,thud(210,0.03),0.9)
# animals
put(sfx,65.2,creak(),0.9); put(sfx,65.9,creak(),0.7); put(sfx,66.8,thud(70,0.12),1.1); put(sfx,67.6,chime([659,784,1047,1319],0.9,0.12),0.45)
for i in range(52): put(sfx,70.0+i*0.27,thud(95+rng.integers(0,40),0.05),0.3)
put(sfx,72.2,yip(500)*0.6,0.4); put(sfx,72.5,yip(460)*0.6,0.4)
put(sfx,75.6,growl(),0.9); put(sfx,77.1,pop(380),0.7); put(sfx,77.3,whoosh(0.4),0.4); put(sfx,78.5,trumpet(),0.7)
for i in range(5): put(sfx,78.6+i*0.35,thud(55,0.14),0.9)
for i in range(6): put(sfx,80.3+i*0.26,pop(500+i*40),0.55)
for t0 in (82.0,82.35,82.9,83.3): put(sfx,t0,yip(1000+rng.integers(0,200)),0.6)
# flood
put(sfx,84.6,creak(),0.9); put(sfx,85.7,thud(65,0.14),1.2); rainbed(85.0,8.4,0.2,2)
n=int(8.4*SR); t=np.arange(n)/SR; put(sfx,85.0,noise(8.4,40)*30*np.minimum(t/3,1)*np.minimum((8.4-t)/1,1)*(0.6+0.4*np.sin(t*1.9)),0.4)
for t0 in (85.15,87.0,89.4,91.6): put(sfx,t0,thunder(),0.9)
for i in range(40): put(sfx,87.5+i*0.0825,thud(700,0.008)[:int(0.03*SR)],0.3)
for t0 in (88.0,90.0,92.2): put(sfx,t0,splash(1.1,0.6,10),0.6)
# inside
rainbed(93.4,6.5,0.05,10)
for i in range(4): n=int(0.9*SR); t=np.arange(n)/SR; put(sfx,94.0+i*1.5,np.sin(2*np.pi*70*t)*(1+np.sin(2*np.pi*22*t))*np.sin(np.pi*t/0.9)**2,0.35)
put(sfx,96.8,creak(),0.4); put(sfx,98.0,chime([1047,784],0.8,0.3),0.25)
# dove
rainbed(99.9,2.6,0.14,3); put(sfx,100.9,chime([659,784,1047],1.0,0.15),0.45)
n=int(14*SR); t=np.arange(n)/SR; put(sfx,100.3,noise(14,25)*20*(0.5+0.5*np.sin(t*2.0))*np.minimum(t/1,1)*np.minimum((14-t)/1,1),0.22)
put(sfx,103.45,creak(),0.8); put(sfx,104.1,thud(180,0.04),0.5)
for i in range(13): put(sfx,105.0+i*0.11,flap(),0.6*(1-i/16))
put(sfx,105.05,chirp(),0.6)
for i in range(18): put(sfx,107.5+i*0.12,flap(),0.25+0.35*i/18)
put(sfx,109.7,chirp(),0.6); put(sfx,109.9,chirp(),0.5); put(sfx,110.9,chime([1047,1319,1568,2093],1.0,0.1),0.55); put(sfx,112.0,whoosh(1.4),0.4)
# rainbow
put(sfx,114.7,thud(70,0.12),0.9)
for i in range(30): put(sfx,114.9+i*0.11+rng.random()*0.04,thud(90+rng.integers(0,60),0.04),0.4)
put(sfx,115.6,trumpet(),0.6); put(sfx,116.3,yip(1000),0.5); put(sfx,116.55,yip(1100),0.5); put(sfx,116.9,growl()[:int(0.5*SR)],0.5)
for i,m in enumerate([72,74,76,77,79,81,83,84]): put(sfx,117.6+i*0.28,note(MIDI(m),1.4,'box',0.5),0.5)
put(sfx,117.5,whoosh(2.2),0.4); put(sfx,119.9,chime([1047,1319,1568,2093,2637,3136],1.3,0.07),0.6); put(sfx,120.7,chime([1568,2093],1.0,0.2),0.35)
# back home
put(sfx,127.9,thud(140,0.05),0.7); put(sfx,127.95,whoosh(0.3),0.4)
for i in range(7): put(sfx,130.6+i*0.15,tap(),0.5)
put(sfx,131.9,chime([1047,1319,1568,2093],1.0,0.1),0.5)
for t0 in (132.3,132.9,133.4): put(sfx,t0,yip(1000),0.4)
put(sfx,134.8,chime([2093,2637],0.4,0.05),0.5)
# cta
t1,t2,t3=144.7,146.1,147.5
put(sfx,t1-0.07,whoosh(0.2),0.6); put(sfx,t1,pop(700),1.0); put(sfx,t1+0.03,chime([1319,1760],0.4,0.06),0.5)
put(sfx,t2,whoosh(0.75,False),0.8); put(sfx,t2+0.75,thud(110,0.08),1.0); put(sfx,t3-0.35,whoosh(0.35),0.5); put(sfx,t3,pop(450),1.0); put(sfx,t3+0.01,thud(180,0.04),0.7)
for i in range(4): put(sfx,t3+0.17+i*0.17,chime([2093,2637],0.35,0.02),0.5)
for i in range(14): put(sfx,t1+0.15+i*0.3+rng.random()*0.1,pop(500+rng.integers(0,900)),0.2)
def save(fn,x):
    x=x/max(1e-9,np.abs(x).max())*0.9; w=wave.open(fn,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
save('music.wav',mus); save('sfx.wav',sfx); print('ok')
