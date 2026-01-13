import streamlit as st
import pandas as pd
import requests
import random
import itertools
from fpdf import FPDF
import base64
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="LotoElite V10 PRO", page_icon="💰", layout="centered")

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
    faltantes = set()
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
        elif acertos == 15: total += 1000000; c[15]+=1
    return total, c

# --- INTERFACE ---
st.title("💰 LotoElite V10 PRO")
st.markdown("---")

if 'dados' not in st.session_state:
    st.session_state.dados = buscar_dados()

hist, ultimo, conc, premio = st.session_state.dados if st.session_state.dados else (None, None, None, None)

if hist:
    faltantes = analisar_ciclo(hist)
    st.warning(f"🎯 Próximo Concurso: {conc+1} | Faltam no Ciclo: {faltantes}")
    
    col1, col2 = st.columns(2)
    
    # BOTÃO MANUAL (50 JOGOS)
    with col1:
        if st.button("🚀 GERAR 50 JOGOS", use_container_width=True):
            base = list(set(faltantes + random.sample(ultimo, 9)))
            outros = [n for n in range(1, 26) if n not in base]
            random.shuffle(outros)
            dezenas_18 = sorted(base + outros[:max(0, 18-len(base))])
            pool = list(itertools.combinations(dezenas_18, 15))
            random.shuffle(pool)
            
            novos_jogos = []
            for comb in pool:
                jogo = sorted(list(comb))
                if validar_v10(jogo, ultimo, faltantes):
                    lucro, counts = simular_lucro(jogo, hist)
                    if lucro >= 65:
                        novos_jogos.append({'jogo': jogo, 'lucro': lucro, 'counts': counts})
                if len(novos_jogos) >= 50: break
            st.session_state.jogos = novos_jogos

    # NOVO BOTÃO: BUSCA AUTOMÁTICA
    with col2:
        if st.button("🔍 BUSCA MILIONÁRIA", use_container_width=True):
            encontrou = False
            placeholder = st.empty()
            tentativas = 0
            
            while not encontrou:
                tentativas += 1
                placeholder.info(f"Analisando combinações... Tentativa {tentativas}")
                
                # Gera novo set de dezenas para testar
                base = list(set(faltantes + random.sample(ultimo, 9)))
                outros = [n for n in range(1, 26) if n not in base]
                random.shuffle(outros)
                dezenas_18 = sorted(base + outros[:max(0, 18-len(base))])
                
                pool = list(itertools.combinations(dezenas_18, 15))
                random.shuffle(pool)
                
                for comb in pool[:50]: # Testa 50 de cada vez para ser rápido
                    jogo = sorted(list(comb))
                    lucro, counts = simular_lucro(jogo, hist)
                    
                    if counts[15] > 0: # CRITÉRIO MILIONÁRIO
                        st.session_state.jogos = [{'jogo': jogo, 'lucro': lucro, 'counts': counts}]
                        encontrou = True
                        st.balloons()
                        st.success("🎉 JOGADA MILIONÁRIA ENCONTRADA!")
                        break
                
                if tentativas > 1000: # Limite de segurança para não travar
                    st.error("Muitas tentativas sem sucesso. Tente novamente.")
                    break

    # EXIBIÇÃO DOS RESULTADOS
    if 'jogos' in st.session_state:
        for i, item in enumerate(st.session_state.jogos, 1):
            icones = ""
            if item['counts'][15] > 0: icones += " 💵 JOGADA MILIONÁRIA"
            if item['counts'][14] > 0: icones += " 🔥"
            if item['counts'][13] > 0: icones += " 💰"
            
            with st.expander(f"Resultado {i:02d} | {icones}"):
                st.code(" ".join(f"{n:02d}" for n in item['jogo']))
                st.write(f"Acertos Históricos: 15p: {item['counts'][15]} | 14p: {item['counts'][14]} | 13p: {item['counts'][13]}")

else:
    st.error("Erro na API ou Conexão.")
