import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import unicodedata
import datetime
import plotly.express as px

# 1. CONFIGURAÇÃO DE IDENTIDADE E CURSOR
st.set_page_config(page_title="ESTRATÉGIA GABARITO - Oficial", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    button, .stButton>button, .streamlit-expanderHeader, [data-baseweb="select"], .stRadio label, .stSelectbox {
        cursor: pointer !important;
    }
    .theory-card { background: white; padding: 25px; border-radius: 12px; border-left: 10px solid #1c83e1; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 25px; }
    .question-box { background: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bras%C3%A3o_da_PMMG.svg/1200px-Bras%C3%A3o_da_PMMG.svg.png"

# CONEXÃO COM GOOGLE SHEETS (VIA SECRETS JSON)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNÇÃO PARA SALVAR PROGRESSO REAL NA PLANILHA ---
def registrar_no_banco(usuario, lei, titulo, q_id, status):
    try:
        # Lê os logs atuais para não sobrescrever
        df_atual = conn.read(worksheet="Log_Progresso", ttl=0)
        
        # Cria a nova linha
        nova_linha = pd.DataFrame([{
            "Usuario": usuario,
            "Materia": lei,
            "Titulo": titulo,
            "Questao": str(q_id),
            "Status": status,
            "Data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        }])
        
        # Concatena e faz o upload
        df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
        conn.update(worksheet="Log_Progresso", data=df_final)
        st.toast("Missão registrada no banco de dados! ☁️")
    except Exception as e:
        st.error(f"Erro ao salvar progresso: {e}")

# Inicialização de Memória da Sessão
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'historico_questoes' not in st.session_state: st.session_state.historico_questoes = []

# --- LOGIN ---
if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;">', unsafe_allow_html=True)
    st.image(URL_BRASAO, width=100)
    st.title("ESTRATÉGIA GABARITO")
    st.subheader("🛡️ Missão 3º Sargento")
    
    u_input = st.text_input("Usuário PM:")
    p_input = st.text_input("Senha:", type="password")
    
    if st.button("INICIAR MISSÃO"):
        df_u = conn.read(worksheet="Usuarios", ttl=5)
        if not df_u.empty:
            if u_input in df_u.iloc[:, 0].values:
                linha = df_u[df_u.iloc[:, 0] == u_input]
                if p_input == str(linha.iloc[0, 1]):
                    st.session_state.autenticado = True
                    st.session_state.usuario = u_input
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR ---
st.sidebar.image(URL_BRASAO, width=60)
st.sidebar.title(f"Sgt {st.session_state.usuario}")

# Ranking Privado (Lendo do Histórico Local)
if st.session_state.historico_questoes:
    df_h = pd.DataFrame(st.session_state.historico_questoes)
    acertos = len(df_h[df_h['status'] == 'Acerto'])
    st.sidebar.metric("Aproveitamento Sessão", f"{(acertos/len(df_h)*100):.1f}%")

menu = st.sidebar.radio("Navegação:", ["📝 Simulado", "📖 Teoria", "📊 Performance"])

if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.rerun()

# --- MODO SIMULADO ---
if menu == "📝 Simulado":
    area = st.sidebar.selectbox("Área do Edital:", ["Legislacao_Institucional", "Doutrina_Operacional", "Legislacao_Juridica"])
    df_q = conn.read(worksheet=area, ttl=5)
    
    if not df_q.empty:
        col_lei_idx = 11  # Coluna L
        col_titulo_idx = 12 # Coluna M
        
        lista_leis = sorted(df_q.iloc[:, col_lei_idx].unique())
        sel_lei = st.selectbox("🎯 1. Lei ou Manual:", lista_leis)
        
        df_f_lei = df_q[df_q.iloc[:, col_lei_idx] == sel_lei]
        lista_titulos = sorted(df_f_lei.iloc[:, col_titulo_idx].unique())
        sel_titulo = st.selectbox(f"📖 2. Tópico:", ["VER TODOS"] + lista_titulos)
        
        df_exibir = df_f_lei if sel_titulo == "VER TODOS" else df_f_lei[df_f_lei.iloc[:, col_titulo_idx] == sel_titulo]

        for i, row in df_exibir.iterrows():
            with st.container():
                st.markdown(f'<div class="question-box"><b>QUESTÃO {row.iloc[0]}</b><br><small>{sel_lei} | {row.iloc[col_titulo_idx]}</small><br><br>{row.iloc[3]}</div>', unsafe_allow_html=True)
                
                ops = {"A": row.iloc[4], "B": row.iloc[5], "C": row.iloc[6], "D": row.iloc[7]}
                ops_v = {k: v for k, v in ops.items() if str(v) != "" and str(v).lower() != 'nan'}
                
                escolha = st.radio(f"Resposta Q{i}:", list(ops_v.values()), key=f"r_{i}")
                
                if st.button(f"Validar Questão {row.iloc[0]}", key=f"b_{i}"):
                    letra_sel = [l for l, t in ops_v.items() if t == escolha][0]
                    gab = str(row.iloc[8]).strip().upper()
                    status = "Acerto" if letra_sel == gab else "Erro"
                    
                    # GRAVAÇÃO NO BANCO DE DADOS (GOOGLE SHEETS)
                    registrar_no_banco(st.session_state.usuario, sel_lei, sel_titulo, row.iloc[0], status)
                    
                    st.session_state.historico_questoes.append({'status': status})
                    if status == "Acerto": st.success("🎯 Acertou!")
                    else: st.error(f"❌ Errou! Gabarito: {gab}")
                    st.info(f"💡 Explicação: {row.iloc[9]}")

# --- TEORIA ---
elif menu == "📖 Teoria":
    st.header("📖 Centro de Teoria")
    df_t = conn.read(worksheet="Explicacoes_Teoria", ttl=5)
    if not df_t.empty:
        busca = st.text_input("🔍 Buscar termo:", "").lower()
        for idx, r in df_t.iterrows():
            if busca in str(r).lower():
                with st.expander(f"📌 {r.iloc[0]} | {r.iloc[1]}"):
                    st.markdown(f'<div class="theory-card">{r.iloc[2]}</div>', unsafe_allow_html=True)
