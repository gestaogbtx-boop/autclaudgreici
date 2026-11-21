import sys,subprocess,numpy as np,wave
SR=44100
def load(fn):
    raw=subprocess.run(['ffmpeg','-v','error','-i',fn,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(raw,dtype='<f4').astype(np.float64)
def grms(x,win=0.4):
    n=int(win*SR); m=len(x)//n; b=(x[:m*n].reshape(m,n)**2).mean(1); top=b.max(); act=b[b>top*10**(-30/10)]; return np.sqrt(act.mean())
v,m,s=[load(f) for f in sys.argv[1:4]]; N=len(v); m=np.resize(m,N) if len(m)>=N else np.pad(m,(0,N-len(m))); s=s[:N] if len(s)>=N else np.pad(s,(0,N-len(s)))
rv=grms(v); m*=0.5*rv/grms(m); s*=0.5*rv/grms(s)
lim=0.7*np.abs(v).max(); pk=np.abs(s).max()
s=np.tanh(s/lim)*lim if pk>lim else s
if grms(s)>0.5*rv: s*=0.5*rv/grms(s)
db=lambda a:20*np.log10(a)
print(f'voz RMS {db(rv):.1f} dBFS | musica {db(grms(m)/rv):+.1f} dB rel | efeitos {db(grms(s)/rv):+.1f} dB rel | pico efeitos/voz {np.abs(s).max()/np.abs(v).max():.2f}')
x=v+m+s; w=wave.open('mix.wav','wb'); w.setnchannels(1); w.setsampwidth(3 if False else 2); w.setframerate(SR)
x=x/max(1.0,np.abs(x).max()/0.98); w.writeframes((x*32767).astype('<i2').tobytes()); w.close()
