#!/usr/bin/env python3
"""Alinha o roteiro v5 ao áudio da narração (por pausas) e gera cenas.py."""
import subprocess, re, json, sys, os
AUDIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio", "narracao-v5.mp3")

# (cena, [textos na tela: '|' quebra linha, *amarelo*, _vermelho_]) – um item por frase falada
ROT = [
 ("calmar",  ["Março de | *2024*"]),
 ("login",   ["Um engenheiro percebe | que o login no computador", "dele está *meio segundo* | mais lento", "Só isso."]),
 ("ataque",  ["E essa pequena lentidão | evitou o que poderia", "ter sido um dos | *maiores ataques*", "da história da internet"]),
 ("engenh",  ["O engenheiro se chamava | *Andres Freund*", "e trabalhava | na *Microsoft*"]),
 ("cpu",     ["Ele testava um sistema Linux", "quando notou que o *SSH* | gastava mais processador"]),
 ("lupa",    ["Foi puxando o fio...", "e encontrou *código escondido*", "num programa que quase | ninguém conhece: o *XZ Utils*"]),
 ("compacta",["O XZ é uma ferramenta | simples", "de *compactar* arquivos"]),
 ("servidor",["Mas está dentro de boa | parte dos sistemas *Linux*", "inclusive nos servidores | que sustentam *bancos*", "empresas e *governos*"]),
 ("porta",   ["E o código criava | uma _porta dos fundos_", "quem tivesse | a *chave certa*", "entraria sem | precisar de senha"]),
 ("ampulh",  ["Só que ninguém invadiu nada.", "Quem planejou isso | jogou o _jogo longo_"]),
 ("commits", ["Um desenvolvedor | chamado *Jia Tan*", "apareceu no projeto | por volta de *2021*", "ajudando com | pequenas correções"]),
 ("confianca",["Educado, constante, | sempre útil", "E durante quase | *dois anos*...", "foi ganhando _confiança_"]),
 ("esgotado",["O criador do XZ, | *Lasse Collin*", "mantinha o projeto sozinho | e estava _esgotado_"]),
 ("pressao", ["Contas estranhas | começaram a pressioná-lo", "cobrando atualizações", "e pedindo um | *novo responsável*"]),
 ("chave",   ["Ele cedeu.", "E deu a *Jia Tan* | o poder de *publicar*", "novas versões | do programa"]),
 ("testes",  ["Foi aí que | o plano andou.", "O código foi escondido | em *arquivos de teste*", "e entrou nas versões | *5.6.0* e *5.6.1*", "Alguns sistemas Linux | já tinham começado a usar"]),
 ("mapa",    ["Se ninguém tivesse notado...", "a porta dos fundos chegaria | a _milhões de servidores_"]),
 ("relogio2",["Mas os atacantes erraram | em um detalhe", "o código era pesado demais. | Por *meio segundo*"]),
 ("misterio",["Até hoje, ninguém sabe | quem é *Jia Tan*", "O nome provavelmente | é falso", "Alguns suspeitam de um | grupo apoiado por governo", "Mas _nada_ foi provado"]),
 ("pastas",  ["Esse é só um dos | muitos *arquivos*", "que abrimos por aqui"]),
 ("cta",     ["Se você gosta | desse conteúdo", "*segue o Operação Sigilo*", "e vem ver os *mistérios*, | as *operações secretas*", "e casos reais que | tentaram _esconder_"]),
]
def clean(t): return re.sub(r"[*_|]", "", t).replace("  ", " ").strip()

def silences():
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", AUDIO, "-af", "silencedetect=noise=-33dB:d=0.3", "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", AUDIO]))
    return list(zip(st, en[:len(st)])), dur

def main():
    sil, dur = silences()
    sil = [s for s in sil if s[0] > .3 and s[1] < dur - .1]
    # tempo de fala acumulado (sem pausas)
    speech = []; prev = 0.0
    for a, b in sil: speech.append((prev, a)); prev = b
    speech.append((prev, dur))
    total_speech = sum(b - a for a, b in speech)
    def abs_from_speech(x):  # x = segundos de fala acumulados
        for a, b in speech:
            if x <= b - a: return a + x
            x -= b - a
        return dur
    chars = [sum(len(clean(t)) for t in ch) for _, ch in ROT]
    cum = [sum(chars[:i + 1]) for i in range(len(chars))]
    pred = [abs_from_speech(c / cum[-1] * total_speech) for c in cum[:-1]]  # fim previsto de cada cena (exceto a última)
    mids = [(a + b) / 2 for a, b in sil]
    n, m = len(pred), len(mids)
    INF = 1e9
    dp = [[INF] * (m + 1) for _ in range(n + 1)]; bp = [[0] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        for j in range(i, m + 1):
            best, arg = INF, 0
            for k in range(i - 1, j):
                if dp[i - 1][k] < best: best, arg = dp[i - 1][k], k
            dp[i][j] = best + abs(pred[i - 1] - mids[j - 1]) ** 1.5; bp[i][j] = arg
    j = min(range(n, m + 1), key=lambda j: dp[n][j]); cuts = []
    for i in range(n, 0, -1):
        cuts.append(mids[j - 1]); j = bp[i][j]
    cuts = cuts[::-1]
    bounds = [0.0] + cuts + [dur]
    cenas = []
    for idx, (kind, chunks) in enumerate(ROT):
        s, e = bounds[idx], bounds[idx + 1]
        cc = [len(clean(t)) for t in chunks]; tot = sum(cc); acc = 0; chs = []
        for t, c in zip(chunks, cc):
            chs.append(dict(start=round(s + (e - s) * acc / tot, 2), text=t)); acc += c
        cenas.append(dict(kind=kind, start=round(s, 2), dur=round(e - s, 2), chunks=chs))
        print(f"{idx+1:2d} {kind:9s} {s:6.1f}-{e:6.1f} ({e-s:4.1f}s) pred_end={pred[idx] if idx < n else dur:6.1f}  {clean(chunks[0])[:40]}")
    json.dump(cenas, open(os.path.join(os.path.dirname(AUDIO), "..", "cenas.json"), "w"), ensure_ascii=False, indent=1)
if __name__ == "__main__": main()
