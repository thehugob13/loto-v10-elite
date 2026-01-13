import streamlit as st
import pandas as pd
import requests
import random
import itertools
from fpdf import FPDF
from datetime import datetime
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LotoElite V10", page_icon="💰", layout="centered")

# --- LÓGICA DE INTELIGÊNCIA (MESMA DA V10 DESKTOP) ---
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
    ciclo_atual = set(); faltantes = set()
    for jogo in historico:
        ciclo_atual.update(jogo)
        if len(ciclo_atual) == 25: break
        faltantes = todos - ciclo_atual
    return sorted(list(faltantes))

def validar_v10(jogo, ultimo_res, dezenas_ciclo):
    if dezenas_ciclo and len(set(jogo) & set(dezenas_ciclo)) < (len(dezenas_ciclo) * 0.6): return False
    q1=[1,2,3,6,7,8]; q2=[4,5,9,10]; q3=[11,12,13,16,17,18]; q4=[14,15,19,20,21,22,23,24,25]
    for q in [q1,q2,q3,q4]:
        if len(set(jogo) & set(q)) > 6: return False
    if not (5 <= len([n for n in jogo if n in [2,3,5,7,11,13,17,19,23]]) <= 7): return False
    return True

def simular_lucro(jogo, historico):
    total = 0; c = {11:0, 12:0, 13:0, 14:0, 15:0}
    for res in historico[:100]:
        acertos = len(set(jogo) & set(res))
        if acertos == 11: total += 7; c[11]+=1
        elif acertos == 12: total += 12; c[12]+=1
        elif acertos == 13: total += 30; c[13]+=1
        elif acertos == 14: total += 1700; c[14]+=1
    return total, c

# --- INTERFACE MOBILE ---
st.title("💰 LotoElite V10 Mobile")
st.markdown("---")

if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()

hist, ultimo, conc, premio = st.session_state.dados if st.session_state.dados else (None, None, None, None)

if hist:
    faltantes = analisar_ciclo(hist)
    st.warning(f"🎯 Concurso: {conc+1} | Ciclo Faltam: {faltantes}")
    
    if st.button("🚀 GERAR 24 JOGOS DE ELITE", use_container_width=True):
        base = list(set(faltantes + random.sample(ultimo, 9)))
        outros = [n for n in range(1, 26) if n not in base]
        random.shuffle(outros)
        dezenas_18 = sorted(base + outros[:18-len(base)])
        
        pool = list(itertools.combinations(dezenas_18, 15))
        random.shuffle(pool)
        
        jogos_v10 = []
        for c in pool:
            jogo = sorted(list(c))
            if validar_v10(jogo, ultimo, faltantes):
                lucro, counts = simular_lucro(jogo, hist)
                if lucro >= 65:
                    jogos_v10.append({'jogo': jogo, 'lucro': lucro, 'counts': counts})
            if len(jogos_v10) >= 24: break
        
        st.session_state.jogos = jogos_v10

    if 'jogos' in st.session_state:
        for i, item in enumerate(st.session_state.jogos, 1):
            fogo = "🔥" if item['counts'][14] > 0 else ""
            txt_jogo = " ".join(f"{n:02d}" for n in item['jogo'])
            with st.expander(f"Jogo {i:02d} | R$ {item['lucro']} {fogo}"):
                st.code(txt_jogo)
                st.write(f"Acertos (100 conc): 13p: {item['counts'][13]} | 14p: {item['counts'][14]}")

        # --- GERAR PDF NO CELULAR ---
        if st.button("📄 BAIXAR PDF PARA WHATSAPP", use_container_width=True):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, f"Jogos Elite V10 - Concurso {conc+1}", ln=True, align='C')
            pdf.set_font("Courier", '', 10)
            for i, j in enumerate(st.session_state.jogos, 1):
                txt = " ".join(f"{n:02d}" for n in j['jogo'])
                fogo_txt = " (ALTA PROB)" if j['counts'][14] > 0 else ""
                pdf.cell(0, 8, f"{i:02d}: {txt} | Lucro: R${j['lucro']}{fogo_txt}", ln=True)
            
            html = f'<a href="data:application/pdf;base64,{base64.b64encode(pdf.output(dest="S").encode("latin-1")).decode()}" download="jogos_lotofacil.pdf">Clique aqui para baixar o PDF</a>'
            st.markdown(html, unsafe_allow_html=True)

else:
    st.error("Erro de conexão. Verifique sua internet.")

if st.button("🔄 Sincronizar"):
    st.session_state.dados = buscar_dados()
    st.rerun()