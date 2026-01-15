import streamlit as st
import pandas as pd
import requests
import random
import itertools
from fpdf import FPDF
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LotoElite V12 - TENDÊNCIA", page_icon="🔥", layout="centered")

# --- LÓGICA DE INTELIGÊNCIA V12 ---
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
    # Analisa as dezenas mais frequentes nos últimos 10 jogos
    frequencia = {}
    for jogo in historico[:10:
        for num in jogo:
            frequencia[num] = frequencia.get(num, 0) + 1
    # Ordena dezenas por frequência (as "Quentes")
    quentes = sorted(frequencia, key=frequencia.get, reverse=True)
    return quentes[:18] # Retorna as 18 melhores tendências

def validar_v12(jogo, ultimo_res):
    # Filtro de Equilíbrio Pro (Padrão 8-7 ou 7-8)
    impares = len([n for n in jogo if n % 2 != 0])
    if impares not in [7, 8, 9]: return False
    
    # Filtro de Repetição do Anterior (Padrão 8 a 10 repetidas)
    repetidas = len(set(jogo) & set(ultimo_res))
    if repetidas not in [8, 9, 10]: return False
    
    # Soma das dezenas (Padrão entre 160 e 220)
    if not (160 <= sum(jogo) <= 220): return False
    
    return True

def simular_lucro(jogo, historico):
    c = {11:0, 12:0, 13:0, 14:0, 15:0}
    for res in historico[:100]:
        acertos = len(set(jogo) & set(res))
        if acertos >= 11: c[acertos] += 1
    return c

# --- INTERFACE ---
st.title("🔥 LotoElite V12 PRO - Inteligência de Tendência")
st.markdown("---")

if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()

hist, ultimo, conc = st.session_state.dados if st.session_state.dados else (None, None, None)

if hist:
    st.info(f"📊 Analisando tendências para o Concurso {conc+1}...")
    dezenas_quentes = obter_tendencia(hist)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 COMBO 50", use_container_width=True):
            jogos = []
            while len(jogos) < 50:
                # Usa as 18 quentes como base para maior chance
                comb = sorted(random.sample(dezenas_quentes, 15))
                if validar_v12(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    jogos.append({'jogo': comb, 'counts': counts})
            st.session_state.jogos = jogos

    with col2:
        if st.button("🎯 COMBO 10", use_container_width=True):
            jogos = []
            tentativas = 0
            while len(jogos) < 10 and tentativas < 2000:
                tentativas += 1
                comb = sorted(random.sample(dezenas_quentes, 15))
                if validar_v12(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    if counts[13] > 0 or counts[14] > 0 or counts[15] > 0:
                        jogos.append({'jogo': comb, 'counts': counts})
            st.session_state.jogos = jogos

    with col3:
        if st.button("💎 MILIONÁRIA", use_container_width=True):
            status = st.empty()
            for t in range(5000):
                status.text(f"Buscando nos filtros... {t}")
                comb = sorted(random.sample(range(1, 26), 15))
                if validar_v12(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    if counts[15] > 0:
                        st.session_state.jogos = [{'jogo': comb, 'counts': counts}]
                        st.balloons()
                        break

    # EXIBIÇÃO
    if 'jogos' in st.session_state:
        for i, item in enumerate(st.session_state.jogos, 1):
            emoji_str = ""
            if item['counts'][13] > 0: emoji_str = "💰"
            if item['counts'][14] > 0: emoji_str = "💰🔥"
            if item['counts'][15] > 0: emoji_str = "💰🔥💵"
            
            with st.expander(f"Jogo {i:02d} | {emoji_str}"):
                st.code(" ".join(f"{n:02d}" for n in item['jogo']))
                st.write(f"13p: {item['counts'][13]} | 14p: {item['counts'][14]} | 15p: {item['counts'][15]}")

        # PDF
        if st.button("📄 BAIXAR PDF", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"LotoElite V12 - Concurso {conc+1}", ln=True, align='C')
            pdf.set_font("Courier", '', 10)
            for i, j in enumerate(st.session_state.jogos, 1):
                pdf.cell(0, 8, f"{i:02d}: {' '.join(f'{n:02d}' for n in j['jogo'])}", ln=True)
            b64 = base64.b64encode(pdf.output(dest="S").encode("latin-1")).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="elite_v12.pdf">Baixar PDF</a>', unsafe_allow_html=True)

else:
    st.error("Sem conexão com os resultados.")
