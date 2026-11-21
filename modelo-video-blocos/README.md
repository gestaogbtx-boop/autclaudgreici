# Modelo de vídeo: histórias em blocos (vertical 9:16)

Modelo usado em "Jonas e o Peixe Gigante": personagens cartoon 2D (cartões desenhados em canvas)
num mundo 3D de blocos com contorno de tinta. Saída 1080x1920, 30 fps, com a duração exata da narração.
Música e efeitos são sintetizados e ficam a 50% do volume da voz.

## Arquivos
- `web/engine.js` – motor: materiais toon, contorno por profundidade, céu/estrelas, cartões (`Actor`), câmera por quadros-chave (`K`, `setCam`), luz (`look`).
- `web/chars.js` – elenco: `drawPerson`, `drawDog` e a tabela `CAST` (menina, menino, vovó, cachorro, Jonas, marinheiros, povo).
- `web/scenes.js` – a história: cenários, ações e a linha do tempo `SC` (quadro inicial de cada cena). **É o arquivo que muda a cada história.**
- `audio.py` – trilha e tabela de deixas dos efeitos (muda a cada história). `mix.py` – mixagem travada em −6 dB.
- `render.mjs` – renderiza quadros (aceita lista, intervalo e divisão em workers). `sheet.py` – folha de contato. `finish.sh` – MP4 final + checagem.
- `exemplos/jonas/` – cenas, áudio e narração da história de Jonas.

## Como fazer uma nova história
1. `npm install` e deixar o Playwright com Chromium acessível (`node_modules/playwright`).
2. Salvar a narração como `voice.mp3`. Listar as pausas: `ffmpeg -i voice.mp3 -af silencedetect=noise=-35dB:d=0.25 -f null -`
   e casar cada trecho de fala com as frases do roteiro para achar o segundo em que cada cena começa.
3. Reescrever `web/scenes.js` (um bloco `mk('nome')` por cenário, com `s.update(f, T)`) e a tabela `SC`/`TOTAL` (segundos × 30).
   Reaproveitar: `makeSea`, `makeBoat`, `makeFish`, `Burst`, `Confetti`, `glow`, `palm`, `house`, o quarto e o quintal.
4. Testar: `node render.mjs stills/a "60,200,400"` e `python3 sheet.py stills/a stills/sheet.jpg 9`.
5. Render completo em 3 workers: `for i in 0 1 2; do node render.mjs frames "0-<N-1>" $i/3 & done; wait` (cerca de 0,3 s por quadro).
6. Som: ajustar as deixas em `audio.py`, depois `python3 audio.py && python3 mix.py voice.mp3 music.wav sfx.wav`.
7. `bash finish.sh nome-do-video`.

## Padrões do elenco
Crianças 1,10 m; vovó 1,50 m; adultos 1,65 m; cachorro na cintura das crianças. Barco de 4,6 m; peixe de 28 m.

## Exemplo 2: A Arca de Noé (`exemplos/noe/`)
`web/chars.js` agora também tem Noé e família, o povo, animais (`drawAnimal`: leão, girafa, elefante, coelho, zebra, ovelha, pomba),
paleta do cachorro (`pal`) e piscadinha (`eyes: 'wink'`). As cenas de Noé trazem `makeArk`, `makeRainbow`, `makeRain`, `Crit` (animais) e a sala da vovó.
Para rodar um exemplo, copie o `scenes.js` e o `audio.py` dele para `web/scenes.js` e `audio.py`, e use o `voice.mp3` da mesma pasta.

## Regras para não ter objetos atravessando (aprendidas na Arca de Noé)
- Personagem sentado: o cartão fica **na frente** da face frontal do assento, nunca dentro da caixa do móvel.
- Caminhos de personagens contornam os móveis (andar pela frente, depois sentar); nunca interpolar em linha reta por dentro de sofá, bancada ou rampa.
- Objeto empurrado ou segurado não ocupa o mesmo x/z do personagem; ferramentas ficam presas à mão com `actor.hand(cx, cy)`.
- Animais largos entrando/saindo de portas usam `yaw: 0` e `alpha` (somem no escuro da porta) em vez de cruzar a parede.
- Partículas (`Burst`) só são atualizadas na cena em que aparecem; esconder nas demais.
- Conferir sempre uma folha densa de quadros (1 a cada ~1,5 s) antes de entregar.
