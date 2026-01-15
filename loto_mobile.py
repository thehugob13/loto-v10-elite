import streamlit as st
import pandas as pd
import requests
import random
import itertools
from fpdf import FPDF
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LotoElite V13 ANTISSISTEMA", page_icon="🛡️", layout="centered")

# --- LÓGICA DE INTELIGÊNCIA V13 ---
def buscar_dados():
    url = "https://loteriascaixa-api.herokuapp.com/api/lotofacil"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            df = pd.DataFrame(dados)
            historico = [list(map(int, d)) for d in df['dezenas'].tolist()]
            return historico, historico[0], df.iloc[0]['concurso']
    except: return None, None, None

def obter_tendencia(historico):
    frequencia = {}
    for jogo in historico[:10]: # Analisa os últimos 10 concursos
        for num in jogo:
            frequencia[num] = frequencia.get(num, 0) + 1
    # Pega as 18 dezenas que mais saíram (Tendência Quente)
    quentes = sorted(frequencia, key=frequencia.get, reverse=True)
    return quentes[:18]

def validar_antissistema(jogo):
    # 1. Evita sequências longas (mais de 4 números seguidos)
    sequencia_max = 0
    atual = 1
    for i in range(len(jogo)-1):
        if jogo[i+1] == jogo[i] + 1:
            atual += 1
        else:
            sequencia_max = max(sequencia_max, atual)
            atual = 1
    if max(sequencia_max, atual) > 4: return False

    # 2. Filtro de Moldura (Evita o desenho clássico das bordas do volante)
    # Pessoas tendem a marcar muito as bordas. Vamos manter equilíbrio (7 a 10 na borda)
    moldura = [1,2,3,4,5,6,10,11,15,16,20,21,22,23,24,25]
    cont_moldura = len(set(jogo) & set(moldura))
    if cont_moldura > 10 or cont_moldura < 7: return False

    # 3. Soma Equilibrada (Padrão ouro: 160 a 220)
    if not (160 <= sum(jogo) <= 220): return False

    return True

def validar_v13(jogo, ultimo_res):
    # Filtro de Ímpares (7, 8 ou 9)
    impares = len([n for n in jogo if n % 2 != 0])
    if impares not in [7, 8, 9]: return False
    
    # Repetição do Anterior (8, 9 ou 10)
    repetidas = len(set(jogo) & set(ultimo_res))
    if repetidas not in [8, 9, 10]: return False
    
    # Chama as novas regras Antissistema
    if not validar_antissistema(jogo): return False
    
    return True

def simular_lucro(jogo, historico):
    c = {11:0, 12:0, 13:0, 14:0, 15:0}
    for res in historico[:100]:
        acertos = len(set(jogo) & set(res))
        if acertos >= 11: c[acertos] += 1
    return c

# --- INTERFACE ---
st.title("🛡️ LotoElite V13 PRO - Antissistema")
st.markdown("---")

if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()

hist, ultimo, conc = st.session_state.dados if st.session_state.dados else (None, None, None)

if hist:
    st.success(f"🔍 Sistema Ativo: Filtrando jogos de baixa ocupação para o Concurso {conc+1}")
    dezenas_quentes = obter_tendencia(hist)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("🚀 COMBO 50", use_container_width=True):
            jogos = []
            while len(jogos) < 50:
                comb = sorted(random.sample(dezenas_quentes, 15))
                if validar_v13(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    jogos.append({'jogo': comb, 'counts': counts})
            st.session_state.jogos = jogos

    with c2:
        if st.button("🎯 COMBO 10", use_container_width=True):
            jogos = []
            while len(jogos) < 10:
                comb = sorted(random.sample(dezenas_quentes, 15))
                if validar_v13(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    # Critério: Jogos com histórico forte
                    if counts[13] > 0 or counts[14] > 0:
                        jogos.append({'jogo': comb, 'counts': counts})
            st.session_state.jogos = jogos

    with c3:
        if st.button("💎 BUSCA 15", use_container_width=True):
            st.toast("Iniciando varredura profunda...", icon="🕵️")
            for _ in range(10000):
                comb = sorted(random.sample(range(1, 26), 15))
                if validar_v13(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    if counts[15] > 0:
                        st.session_state.jogos = [{'jogo': comb, 'counts': counts}]
                        st.balloons()
                        break

    # EXIBIÇÃO COM HIERARQUIA DE EMOJIS
    if 'jogos' in st.session_state:
        for i, item in enumerate(st.session_state.jogos, 1):
            emoji_str = ""
            if item['counts'][13] > 0: emoji_str = "💰"
            if item['counts'][14] > 0: emoji_str = "💰🔥"
            if item['counts'][15] > 0: emoji_str = "💰🔥💵"
            
            with st.expander(f"Jogo {i:02d} | {emoji_str}"):
                st.code(" ".join(f"{n:02d}" for n in item['jogo']))
                st.write(f"13p: {item['counts'][13]} | 14p: {item['counts'][14]} | 15p: {item['counts'][15]}")

        # BOTÃO PDF
        if st.button("📄 BAIXAR PDF ANTISSISTEMA", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"LotoElite V13 PRO - Jogos Unicos", ln=True, align='C')
            pdf.set_font("Courier", '', 10)
            for i, j in enumerate(st.session_state.jogos, 1):
                pdf.cell(0, 8, f"{i:02d}: {' '.join(f'{n:02d}' for n in j['jogo'])}", ln=True)
            b64 = base64.b64encode(pdf.output(dest="S").encode("latin-1")).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="v13_elite.pdf">Baixar PDF</a>', unsafe_allow_html=True)
else:
    st.error("Conexão falhou.")
