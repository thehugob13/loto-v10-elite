import streamlit as st
import pandas as pd
import requests
import random
import itertools
from fpdf import FPDF
import base64
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LotoElite V11 PRO", page_icon="💰", layout="centered")

# --- LÓGICA DE INTELIGÊNCIA ---
def buscar_dados():
    url = "https://loteriascaixa-api.herokuapp.com/api/lotofacil"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            historico = [list(map(int, d)) for d in df['dezenas'].tolist()]
            return historico, historico[0], df.iloc[0]['concurso'], df.iloc[0].get('valorEstimadoProximoConcurso', 0)
    except: return None, None, None, None

def analisar_ciclo(historico):
    todos = set(range(1, 26))
    ciclo_atual = set()
    for jogo in historico:
        ciclo_atual.update(jogo)
        if len(ciclo_atual) == 25: break
    return sorted(list(todos - ciclo_atual))

def validar_v10(jogo, dezenas_ciclo):
    # Filtro de Primos (Média de 5 a 7)
    primos = [2,3,5,7,11,13,17,19,23]
    if not (5 <= len([n for n in jogo if n in primos]) <= 7): return False
    # Filtro de Ciclo (mínimo 60% das faltantes se houver poucas)
    if dezenas_ciclo and len(set(jogo) & set(dezenas_ciclo)) < (len(dezenas_ciclo) * 0.5): return False
    return True

def simular_lucro(jogo, historico):
    total = 0; c = {11:0, 12:0, 13:0, 14:0, 15:0}
    for res in historico[:100]:
        acertos = len(set(jogo) & set(res))
        if acertos >= 11:
            c[acertos] += 1
            if acertos == 11: total += 7
            elif acertos == 12: total += 12
            elif acertos == 13: total += 30
            elif acertos == 14: total += 1700
            elif acertos == 15: total += 1500000
    return total, c

# --- INTERFACE ---
st.title("💰 LotoElite V11 PRO")
st.markdown("---")

if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()

hist, ultimo, conc, premio = st.session_state.dados if st.session_state.dados else (None, None, None, None)

if hist:
    faltantes = analisar_ciclo(hist)
    st.warning(f"🎯 Concurso: {conc+1} | Ciclo Faltam: {faltantes}")
    
    # BOTÕES DE AÇÃO
    c1, c2, c3 = st.columns(3)
    
    with c1:
        btn_manual = st.button("🚀 GERAR 50", use_container_width=True)
    with c2:
        btn_milionaria = st.button("💎 BUSCA 15 pts", use_container_width=True)
    with c3:
        btn_combo = st.button("🎯 COMBO 10", use_container_width=True)

    # LÓGICA DO BOTÃO COMBO 10 (NOVO)
    if btn_combo:
        lista_combo = []
        barra = st.progress(0)
        status = st.empty()
        tentativas = 0
        
        while len(lista_combo) < 10:
            tentativas += 1
            status.text(f"Buscando jogos de Elite... (Tentativa {tentativas})")
            
            base = list(set(faltantes + random.sample(ultimo, 9)))
            outros = [n for n in range(1, 26) if n not in base]
            random.shuffle(outros)
            dezenas_18 = sorted(base + outros[:max(0, 18-len(base))])
            
            comb = sorted(random.sample(dezenas_18, 15))
            if validar_v10(comb, faltantes):
                lucro, counts = simular_lucro(comb, hist)
                # Critério: Tem que ter pelo menos 13 pontos no histórico
                if counts[13] > 0 or counts[14] > 0 or counts[15] > 0:
                    lista_combo.append({'jogo': comb, 'lucro': lucro, 'counts': counts})
                    barra.progress(len(lista_combo) * 10)
            
            if tentativas > 3000: break
        
        st.session_state.jogos = lista_combo
        st.success("🎯 Combo de 10 Jogos de Elite encontrado!")

    # LÓGICA BUSCA MILIONÁRIA (EXISTENTE)
    if btn_milionaria:
        status_m = st.empty()
        for t in range(5000):
            status_m.text(f"Buscando 15 pontos... {t}")
            comb = sorted(random.sample(range(1, 26), 15))
            lucro, counts = simular_lucro(comb, hist)
            if counts[15] > 0:
                st.session_state.jogos = [{'jogo': comb, 'lucro': lucro, 'counts': counts}]
                st.balloons()
                st.success("🎉 JOGADA MILIONÁRIA ENCONTRADA!")
                break

    # LÓGICA GERAR 50 (EXISTENTE)
    if btn_manual:
        # (Sua lógica anterior de gerar 50 jogos aqui)
        base = list(set(faltantes + random.sample(ultimo, 9)))
        outros = [n for n in range(1, 26) if n not in base]
        random.shuffle(outros)
        dezenas_18 = sorted(base + outros[:max(0, 18-len(base))])
        jogos_50 = []
        for _ in range(500):
            comb = sorted(random.sample(dezenas_18, 15))
            if validar_v10(comb, faltantes):
                lucro, counts = simular_lucro(comb, hist)
                if lucro >= 65:
                    jogos_50.append({'jogo': comb, 'lucro': lucro, 'counts': counts})
            if len(jogos_50) >= 50: break
        st.session_state.jogos = jogos_50

    # EXIBIÇÃO COM HIERARQUIA DE EMOJIS
    if 'jogos' in st.session_state:
        for i, item in enumerate(st.session_state.jogos, 1):
            # Definição dos Emojis conforme solicitado
            emoji_str = ""
            if item['counts'][13] > 0: emoji_str = "💰"
            if item['counts'][14] > 0: emoji_str = "💰🔥"
            if item['counts'][15] > 0: emoji_str = "💰🔥💵"
            
            with st.expander(f"Jogo {i:02d} | {emoji_str} (R$ {item['lucro']})"):
                st.code(" ".join(f"{n:02d}" for n in item['jogo']))
                st.write(f"Histórico: 13p: {item['counts'][13]} | 14p: {item['counts'][14]} | 15p: {item['counts'][15]}")

        # BOTÃO PDF
        if st.button("📄 DOWNLOAD PDF", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, "LotoElite V11 PRO", ln=True, align='C')
            pdf.set_font("Courier", '', 10)
            for i, j in enumerate(st.session_state.jogos, 1):
                txt = " ".join(f"{n:02d}" for n in j['jogo'])
                status = "13p" if j['counts'][13]>0 else ""
                if j['counts'][14]>0: status = "14p+"
                if j['counts'][15]>0: status = "MILIONARIA"
                pdf.cell(0, 8, f"{i:02d}: {txt} | {status}", ln=True)
            
            b64_pdf = base64.b64encode(pdf.output(dest="S").encode("latin-1")).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64_pdf}" download="lotoelite.pdf">Clique aqui para baixar</a>', unsafe_allow_html=True)
