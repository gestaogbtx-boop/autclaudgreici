#!/bin/bash
# Uso: bash finish.sh nome-do-video   (precisa de frames/ e mix.wav)
set -e; mkdir -p out
L=$(ffmpeg -hide_banner -i mix.wav -af ebur128 -f null - 2>&1 | grep -A1 "Integrated loudness" | grep -o "I: *-[0-9.]*" | grep -o "\-[0-9.]*")
G=$(python3 -c "print(round(-14-($L),2))")
ffmpeg -y -v error -framerate 30 -i frames/f%04d.jpg -i mix.wav -af "volume=${G}dB,alimiter=limit=0.89:level=false" -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "out/$1.mp4"
ffmpeg -hide_banner -i "out/$1.mp4" -vf "freezedetect=n=0.001:d=0.4,blackdetect=d=0.2" -f null - 2>&1 | grep -E "freeze_start|black_start" || echo "sem quadros congelados nem telas pretas"
