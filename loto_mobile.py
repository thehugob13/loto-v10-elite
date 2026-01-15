import streamlit as st
import pandas as pd
import requests
import random
import itertools
from fpdf import FPDF
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LotoElite V13 ANTISSISTEMA + PROB", page_icon="🛡️", layout="centered")

# --- LÓGICA DE INTELIGÊNCIA ---
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
    for jogo in historico[:15]: # Analisa últimos 15 jogos para maior precisão
        for num in jogo:
            frequencia[num] = frequencia.get(num, 0) + 1
    quentes = sorted(frequencia, key=frequencia.get, reverse=True)
    return quentes[:18]

def validar_v13(jogo, ultimo_res):
    # Filtros Antissistema e Estatísticos
    impares = len([n for n in jogo if n % 2 != 0])
    if impares not in [7, 8, 9]: return False
    
    repetidas = len(set(jogo) & set(ultimo_res))
    if repetidas not in [8, 9, 10]: return False
    
    # Evita sequências longas (>4)
    sequencia = 1; max_seq = 1
    for i in range(len(jogo)-1):
        if jogo[i+1] == jogo[i]+1:
            sequencia += 1
        else:
            max_seq = max(max_seq, sequencia)
            sequencia = 1
    if max(max_seq, sequencia) > 4: return False
    
    if not (160 <= sum(jogo) <= 220): return False
    return True

def simular_lucro(jogo, historico):
    c = {11:0, 12:0, 13:0, 14:0, 15:0}
    for res in historico[:100]:
        acertos = len(set(jogo) & set(res))
        if acertos >= 11: c[acertos] += 1
    return c

# --- INTERFACE ---
st.title("🛡️ LotoElite V13 - Antissistema & Probabilidade")

if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()

hist, ultimo, conc = st.session_state.dados if st.session_state.dados else (None, None, None)

if hist:
    dezenas_quentes = obter_tendencia(hist)
    st.sidebar.header("📈 Tendência Atual")
    st.sidebar.write(f"Dezenas Quentes: {dezenas_quentes}")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("🚀 COMBO 50", use_container_width=True):
            jogos = []
            while len(jogos) < 50:
                comb = sorted(random.sample(dezenas_quentes, 15))
                if validar_v13(comb, ultimo):
                    jogos.append({'jogo': comb, 'counts': simular_lucro(comb, hist)})
            st.session_state.jogos = jogos

    with col2 if 'col2' in locals() else c2: # Ajuste para garantir colunas
        if st.button("🎯 COMBO 10", use_container_width=True):
            jogos = []
            while len(jogos) < 10:
                comb = sorted(random.sample(dezenas_quentes, 15))
                if validar_v13(comb, ultimo):
                    counts = simular_lucro(comb, hist)
                    if counts[13] > 0 or counts[14] > 0:
                        jogos.append({'jogo': comb, 'counts': counts})
            st.session_state.jogos = jogos

    with c3:
        if st.button("💎 BUSCA 15", use_container_width=True):
            with st.spinner("Varrendo buracos no sistema..."):
                for _ in range(20000):
                    comb = sorted(random.sample(range(1, 26), 15))
                    if validar_v13(comb, ultimo):
                        counts = simular_lucro(comb, hist)
                        if counts[15] > 0:
                            st.session_state.jogos = [{'jogo': comb, 'counts': counts}]
                            st.balloons()
                            break

    # --- NOVO: CALCULADORA DE PROBABILIDADE ---
    if 'jogos' in st.session_state:
        # Cálculo de Cobertura
        todos_numeros_jogados = set()
        for j in st.session_state.jogos:
            todos_numeros_jogados.update(j['jogo'])
        
        cobertura = len(todos_numeros_jogados)
        # Probabilidade baseada no cerco das quentes
        quentes_cobertas = len(set(dezenas_quentes) & todos_numeros_jogados)
        eficiencia = (quentes_cobertas / 18) * 100

        st.markdown("---")
        col_p1, col_p2 = st.columns(2)
        col_p1.metric("Cobertura de Volante", f"{cobertura}/25 dezenas")
        col_p2.metric("Eficiência de Tendência", f"{eficiencia:.1f}%")
        
        if eficiencia > 80:
            st.success("✅ Alta Probabilidade: Se a tendência se mantiver, o prêmio está neste grupo!")

        # Exibição dos Jogos
        for i, item in enumerate(st.session_state.jogos, 1):
            emoji_str = ""
            if item['counts'][13] > 0: emoji_str = "💰"
            if item['counts'][14] > 0: emoji_str = "💰🔥"
            if item['counts'][15] > 0: emoji_str = "💰🔥💵 JOGADA MILIONÁRIA"
            
            with st.expander(f"Jogo {i:02d} | {emoji_str}"):
                st.code(" ".join(f"{n:02d}" for n in item['jogo']))
                st.write(f"Histórico: 13p: {item['counts'][13]} | 14p: {item['counts'][14]} | 15p: {item['counts'][15]}")

        # PDF
        if st.button("📄 GERAR PDF V13"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"LotoElite V13 - Eficiencia: {eficiencia:.1f}%", ln=True, align='C')
            pdf.set_font("Courier", '', 10)
            for i, j in enumerate(st.session_state.jogos, 1):
                pdf.cell(0, 8, f"{i:02d}: {' '.join(f'{n:02d}' for n in j['jogo'])}", ln=True)
            b64 = base64.b64encode(pdf.output(dest="S").encode("latin-1")).decode()
            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="v13_pro.pdf">Baixar PDF</a>', unsafe_allow_html=True)
else:
    st.error("Erro ao carregar dados da API.")
