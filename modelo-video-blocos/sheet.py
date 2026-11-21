import sys,glob,os
from PIL import Image,ImageDraw
src,out=sys.argv[1],sys.argv[2]; cols=int(sys.argv[3]) if len(sys.argv)>3 else 6
fs=sorted(glob.glob(src+'/*.jpg')); w,h=270,480
rows=(len(fs)+cols-1)//cols; S=Image.new('RGB',(cols*w,rows*h),'black'); d=ImageDraw.Draw(S)
for i,f in enumerate(fs):
    im=Image.open(f).resize((w,h)); S.paste(im,((i%cols)*w,(i//cols)*h)); d.text(((i%cols)*w+6,(i//cols)*h+4),os.path.basename(f)[1:5],fill='yellow')
S.save(out,quality=88)
