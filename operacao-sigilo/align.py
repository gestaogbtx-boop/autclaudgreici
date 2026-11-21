#!/usr/bin/env python3
"""Alinha o roteiro v5 ao áudio da narração (por pausas) e gera cenas.py."""
import subprocess, re, json, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.environ.get("VOICE", os.path.join(HERE, "audio", "narracao-v5.mp3"))
CENAS_OUT = os.environ.get("CENAS", "cenas.json")

# (cena, [textos na tela: '|' quebra linha, *amarelo*, _vermelho_]) – um item por frase falada
ROT_V5 = [
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
ROT_ATAQUE = [  # "~" no início = o trecho começa logo depois de uma pausa real da voz
 ("contador5",["Cinco ataques *hackers*", "~Em um único mês", "~E todos contra | alvos do *Brasil*"]),
 ("calnov",   ["Em *novembro* de *2026*", "~o país viu uma sequência | que ninguém esperava"]),
 ("mapabr",   ["*Tesouro Nacional*, | Caixa Vida e Previdência", "~*Petrobras*, *Inep* | e o *Porto de Santos*"]),
 ("mira",     ["Dinheiro público, | previdência, energia", "educação e comércio exterior...", "todos _na mira_"]),
 ("videos",   ["Se você acompanhou | os vídeos da *Caixa*", "e do *Porto* aqui no canal", "~já sabe como isso começa"]),
 ("padrao",   ["Mas agora não é | mais um caso isolado", "~É um _padrão_"]),
 ("tesouro",  ["O ataque ao *Tesouro Nacional* | foi um dos mais graves", "~A invasão atingiu | *30 mil* cadastros"]),
 ("pix",      ["~e *4 mil* chaves Pix", "~E uma chave Pix é | o *caminho direto*", "até o *dinheiro* de alguém"]),
 ("caixa",    ["A *Caixa Vida e Previdência* | também entrou na lista"]),
 ("petrobras",["E a *Petrobras*, uma das", "maiores empresas do país", "~foi outro _alvo_"]),
 ("enem",     ["Teve ainda o *Inep*, | o órgão responsável pelo *Enem*", "~Houve *tentativas de ataque* | no segundo dia de provas", "~Em pleno dia de prova", "~com os candidatos dependendo | de tudo funcionar"]),
 ("porto",    ["E o quinto alvo | foi o *Porto de Santos*", "~por onde passa boa parte | do *comércio* do Brasil", "com o mundo"]),
 ("cinco",    ["*Cinco* alvos.", "~*Cinco* setores diferentes.", "~*Trinta* dias."]),
 ("investig", ["_Coincidência?_", "~O que se sabe é que todos", "aconteceram no mesmo *mês*", "~Se existe uma ligação entre eles", "~isso ainda precisa | ser *investigado*"]),
 ("porta",    ["Mas uma lição se repete:", "~os hackers não precisam | derrubar o país inteiro", "~Basta encontrar | uma *porta aberta*"]),
 ("trio",     ["Uma *senha fraca*", "~Um *sistema* sem atualização", "~Um *funcionário* distraído"]),
 ("pastas",   ["Esse é só um dos | muitos *arquivos*", "que abrimos por aqui"]),
 ("cta",      ["Se você gosta | desse tipo de conteúdo", "~*segue o Operação Sigilo*", "e vem ver os *mistérios*, | as *operações secretas*", "e os casos reais que | tentaram _esconder_"]),
]
ROT_HACKER = [
 ("alvo",    ["Esse é o novo jeito | de um *hacker* invadir"]),
 ("app",     ["Começa com um | _app_ feito na pressa"]),
 ("app2",    ["Publicado em | *minutos* com IA"]),
 ("cadeado", ["E *sem proteção*... | _qualquer um_ entra"]),
 ("entrev",  ["Ou numa _entrevista_ | de emprego *falsa*"]),
 ("entrev2", ["O recrutador pede | que você *instale* algo"]),
 ("malic",   ["Esse programa é o | _vírus_"]),
 ("codigo",  ["Você copia um código | e cola no projeto"]),
 ("arquivos",["Vê seus *arquivos*, | *senhas* e *clientes*"]),
 ("relogio", ["Tudo isso em | _poucos minutos_"]),
 ("calend",  ["A empresa leva | *semanas* pra perceber"]),
 ("escudo",  ["Como se proteger? | *Três regras*"]),
 ("celular", ["Um: verificação | em _duas etapas_"]),
 ("download",["Dois: *nunca instale* | nada de desconhecidos"]),
 ("lupa",    ["Três: *revise* todo | código antes de colar"]),
 ("cta",     ["*Operação Sigilo* | segue e fique _à frente_"]),
]
ROT = {"ataque": ROT_ATAQUE, "hacker": ROT_HACKER}.get(os.environ.get("ROTEIRO"), ROT_V5)
BONUS = float(os.environ.get('BONUS', '0'))
def clean(t): return re.sub(r"[*_|]", "", t).replace("  ", " ").strip()

def silences():
    out = subprocess.run(["ffmpeg", "-v", "info", "-i", AUDIO, "-af", "silencedetect=noise=-33dB:d=" + os.environ.get("SILD", "0.3"), "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", AUDIO]))
    return list(zip(st, en[:len(st)])), dur

def syl(text):
    t = clean(text).lower(); n = 0
    for tok in t.split():
        tok = tok.strip(".,:;!?…")
        if tok.isdigit(): n += {"2026": 7, "2021": 7, "30": 2, "4": 2, "5": 2}.get(tok, 3); continue
        n += max(1, len(re.findall(r"[aeiouáéíóúâêôãõà]+", tok)))
    return max(1, n)

def envelope():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", AUDIO, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    import numpy as np
    a = np.frombuffer(raw, dtype=np.int16).astype(float); n = 160
    e = np.sqrt((a[:len(a) // n * n].reshape(-1, n) ** 2).mean(1)); db = 20 * np.log10(e + 1)
    k = np.ones(3) / 3; db = np.convolve(db, k, mode="same")
    vs = []
    for i in range(8, len(db) - 8):
        win = db[i - 15:i + 16]
        if db[i] == db[i - 6:i + 7].min() and win.max() - db[i] > 7: vs.append(i / 100)
    return vs

def main():
    sil, dur = silences()
    sil = [s for s in sil if s[0] > .3 and s[1] < dur - .1]
    vs = envelope()
    cuts = [float(x) for x in os.environ["CUTS"].split(",")]
    assert len(cuts) == len(ROT) - 1, (len(cuts), len(ROT) - 1)
    bounds = [0.0] + cuts + [dur]
    speech = []; prev = 0.0
    for a_, b_ in sil: speech.append((prev, a_)); prev = b_
    speech.append((prev, dur))
    cenas = []
    for idx, (kind, chunks) in enumerate(ROT):
        s_, e_ = bounds[idx], bounds[idx + 1]
        segs = [(max(a_, s_), min(b_, e_)) for a_, b_ in speech if b_ > s_ and a_ < e_ and min(b_, e_) - max(a_, s_) > .08]
        if not segs: segs = [(s_, e_)]
        T = sum(b_ - a_ for a_, b_ in segs); on, off = segs[0][0], segs[-1][1]
        def at(x):
            for a_, b_ in segs:
                if x <= b_ - a_: return a_ + x
                x -= b_ - a_
            return off
        chunks = [c.lstrip('~') if False else c for c in chunks]
        sy = [syl(t.lstrip('~')) for t in chunks]; tot = sum(sy); acc = 0; ws = []
        for i, c in enumerate(sy):
            if i == 0: ws.append(on)
            else:
                p = at(acc / tot * T); prev_t = ws[-1] + .35; pause = chunks[i].startswith("~")
                if pause:  # início depois de pausa real: usa o fim de uma pausa de fala
                    cand = [(abs(b_ - p), b_) for a2, b_ in sil if b_ - a2 >= .28 and abs(b_ - p) < 1.7 and prev_t < b_ < off - .2]
                else:      # no meio da frase: usa o vale de energia mais próximo
                    cand = [(abs(v - p), v) for v in vs + [b2 for a2, b2 in sil] if abs(v - p) < .45 and prev_t < v < off - .2]
                ws.append(min(cand)[1] if cand else max(p, prev_t))
            acc += c
        chs = []
        for i, t in enumerate(chunks):
            end = ws[i + 1] if i + 1 < len(ws) else off
            chs.append(dict(start=round(s_ if i == 0 else ws[i] - .06, 2), wstart=round(ws[i], 2), wdur=round(max(.3, end - ws[i] - .05), 2), text=t.lstrip('~')))
        cenas.append(dict(kind=kind, start=round(s_, 2), dur=round(e_ - s_, 2), chunks=chs))
        print(f"{idx+1:2d} {kind:9s} {s_:6.1f}-{e_:6.1f} on={on:5.1f} " + " ".join(f"{c['wstart']:.1f}" for c in chs) + "  " + clean(chunks[0].lstrip("~"))[:30])
    json.dump(cenas, open(os.path.join(HERE, CENAS_OUT), "w"), ensure_ascii=False, indent=1)
if __name__ == "__main__": main()
