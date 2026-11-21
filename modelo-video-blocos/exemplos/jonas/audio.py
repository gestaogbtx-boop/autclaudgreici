import numpy as np, wave
SR=44100; DUR=93.47; N=int(SR*DUR); rng=np.random.default_rng(7)
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
section(0,19.2,['C','Am','F','G'],B,'box',pad=True,g=0.9,octv=12)
section(19.2,31.6,['C','G','Am','F'],B,'pluck',bass=True,pad=True,drum='soft')
section(31.6,46.5,['Am','F','Dm','E'],B,'pluck',arp=(0,None,2,None,3,None,2,1),bass=True,pad=True,drum='storm',g=1.1,octv=-12)
section(46.5,49.7,['C','F'],B*2,'box',arp=(1,None,3,None,4,None,3,None),pad=True,g=0.8,octv=12)
# tension: music stops, drone only
n=int(4.0*SR); t=np.arange(n)/SR; put(mus,49.7,(np.sin(2*np.pi*(55+6*t)*t)+0.5*np.sin(2*np.pi*82*t))*np.minimum(t/1.5,1)*np.minimum((4.0-t)/0.4,1),0.5)
section(53.75,63.7,['Am','Em','F','Am'],B*2,'box',arp=(1,None,2,None,3,None,None,None),pad=True,g=0.8)
section(63.7,76.2,['C','G','Am','F'],B,'pluck',bass=True,pad=True,drum='soft')
section(76.2,78.75,['F','G'],B,'pluck',bass=True,pad=True,drum='party',g=1.15,octv=12)
section(78.75,86.1,['C','Am','F','G'],B*2,'box',arp=(1,2,3,2,4,3,2,3),pad=True,g=0.9,octv=12)
section(86.1,93.3,['C','F','G','C'],B,'pluck',bass=True,pad=True,drum='party',g=1.15,octv=12)
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
# bath
for t0 in (2.6,3.4,4.3,5.9,6.4): put(sfx,t0,pop(500+rng.integers(0,400)),0.35)
for t0 in (2.3,4.9,6.0): put(sfx,t0,splash(0.35,0.5,6),0.5)
put(sfx,5.2,squeak(),0.6); put(sfx,5.5,squeak(),0.5); put(sfx,7.25,pop(900),0.4)
# bedroom
put(sfx,13.9,whoosh(0.3),0.5); put(sfx,14.6,noise(0.15,2)*env(int(0.15*SR),0.005,0.05),0.5); put(sfx,17.7,whoosh(1.3),0.9); put(sfx,18.9,chime([1047,1319,1568,2093]),0.5)
# call
put(sfx,19.4,chime([784,988,1175,1568,1976],0.8,0.12),0.5); put(sfx,22.7,whoosh(0.6),0.5); put(sfx,25.1,thud(90,0.1),0.9); put(sfx,25.9,whoosh(0.3,False),0.5)
# port
for i in range(11): put(sfx,26.95+i*0.2,tap(),0.6)
put(sfx,29.1,whoosh(0.4),0.6); put(sfx,29.55,thud(80,0.1),1.0); put(sfx,29.9,whoosh(1.2),0.7); put(sfx,30.2,splash(1.2,0.5,8),0.5)
# storm
n=int(15.6*SR); r=noise(15.6,2); e=np.minimum(np.arange(n)/SR/0.6,1)*np.minimum((15.6-np.arange(n)/SR)/1.2,1); put(sfx,31.6,r*e,0.16)
w=noise(15.6,40)*30; put(sfx,31.6,w*e*(0.6+0.4*np.sin(np.arange(n)/SR*1.9)),0.35)
for t0 in (32.3,34.3,36.7,39.1,41.6,43.9): put(sfx,t0+0.05,thunder(),0.9)
for t0 in (33.2,35.6,37.4,40.2,42.8): put(sfx,t0,creak(),0.7)
for t0 in (33.8,36.0,38.6,41.0,43.2): put(sfx,t0,splash(0.9,0.6,10),0.6)
# splash + fish
put(sfx,44.95,whoosh(0.35),0.6); put(sfx,45.27,splash(1.3,1.0,5),1.2); put(sfx,46.8,chime([659,784,1047],1.0,0.15),0.4)
n=int(1.6*SR); t=np.arange(n)/SR; put(sfx,48.4,np.sin(2*np.pi*48*t)*np.sin(np.pi*t/1.6)**2,1.0)
put(sfx,49.9,whoosh(0.9),1.0); put(sfx,50.25,splash(1.8,1.2,5),1.4); put(sfx,51.38,thud(55,0.2),1.6); put(sfx,51.4,noise(0.08,2)*env(int(0.08*SR),0.001,0.02),0.8); put(sfx,52.6,splash(2.0,1.0,7),1.2)
# belly
for t0 in (54.6,56.2,57.9,59.5,60.9): put(sfx,t0,pop(1200),0.25)
for i in range(6): put(sfx,54.0+i*1.25,thud(50,0.12),0.5)
for i in range(3): put(sfx,54.3+i*2.43,chime([1319,1568],0.5,0.1),0.25)
put(sfx,61.5,whoosh(0.4,False),0.3); put(sfx,62.2,chime([1047,1319,1568,2093,2637],1.0,0.14),0.55)
# beach
n=int(5.6*SR); t=np.arange(n)/SR; put(sfx,63.7,noise(5.6,25)*20*(0.5+0.5*np.sin(t*2.2))*np.minimum(t/0.5,1)*np.minimum((5.6-t)/0.5,1),0.3)
put(sfx,64.2,whoosh(1.3),0.7); put(sfx,65.55,thud(60,0.2),1.0); put(sfx,65.6,creak(),0.8); put(sfx,66.25,pop(300),0.9); put(sfx,66.3,whoosh(0.7,False),0.6); put(sfx,67.1,thud(100,0.08),0.9)
for i in range(5): put(sfx,67.72+i*0.09,noise(0.05,2)*env(int(0.05*SR),0.002,0.02),0.4)
put(sfx,68.3,splash(1.0,0.7,8),0.7)
# nineveh
for i in range(8): put(sfx,69.7+i*0.22,tap(),0.3)
put(sfx,76.25,chime([523,659,784,1047,1319,1568],1.2,0.08),0.7)
for i in range(14): put(sfx,76.4+i*0.16+rng.random()*0.05,pop(400+rng.integers(0,900)),0.3)
n=int(2.2*SR); t=np.arange(n)/SR; put(sfx,76.4,noise(2.2,3)*np.sin(np.pi*t/2.2)*(0.7+0.3*np.sin(t*40)),0.25)
# good night
put(sfx,79.75,thud(140,0.05),0.7); put(sfx,79.8,whoosh(0.4),0.4); put(sfx,80.5,thud(90,0.08),0.6); put(sfx,84.5,chime([1047,784],0.8,0.3),0.3)
# cta
put(sfx,89.2,whoosh(0.2),0.6); put(sfx,89.27,pop(700),1.0); put(sfx,89.3,chime([1319,1760],0.4,0.06),0.5)
put(sfx,90.3,whoosh(0.75,False),0.8); put(sfx,91.05,thud(110,0.08),1.0); put(sfx,91.3,whoosh(0.35),0.5); put(sfx,91.65,pop(450),1.0); put(sfx,91.66,thud(180,0.04),0.7)
for i in range(4): put(sfx,91.82+i*0.17,chime([2093,2637],0.35,0.02),0.5)
for i in range(12): put(sfx,89.4+i*0.3+rng.random()*0.1,pop(500+rng.integers(0,900)),0.2)
def save(fn,x):
    x=x/max(1e-9,np.abs(x).max())*0.9; w=wave.open(fn,'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
save('music.wav',mus); save('sfx.wav',sfx); print('ok')
