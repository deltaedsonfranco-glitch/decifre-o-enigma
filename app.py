import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import plotly.express as px

# 1. CONFIGURAÇÃO DE IDENTIDADE E ESTILO
st.set_page_config(page_title="ESTRATÉGIA GABARITO - Oficial", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    button, .stButton>button, .streamlit-expanderHeader, [data-baseweb="select"], .stRadio label { cursor: pointer !important; }
    .question-box { background: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 15px; }
    .status-badge { font-weight: bold; font-size: 0.8em; padding: 3px 8px; border-radius: 5px; }
    .concluido { color: #28a745; border: 1px solid #28a745; }
    .pendente { color: #888; border: 1px solid #888; }
    .check-assunto { background-color: #e8f5e9; padding: 15px; border-radius: 10px; border-left: 6px solid #2e7d32; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# CONFIGURAÇÕES TÉCNICAS
MINHA_URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1bV86Twi_Mm4mgMOzoyZFdncEmgud4rAzP9lSvmnCYUM/edit"
URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bras%C3%A3o_da_PMMG.svg/1200px-Bras%C3%A3o_da_PMMG.svg.png"

# CONEXÃO SEGURA
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ Falha nos Secrets. Verifique se o JSON da Service Account está configurado no painel do Streamlit.")
    st.stop()

# --- FUNÇÕES DE BANCO DE DADOS (LOGS) ---
def registrar_log(aba, dados):
    try:
        df_atual = conn.read(spreadsheet=MINHA_URL_PLANILHA, worksheet=aba, ttl=0)
        df_novo = pd.concat([df_atual, pd.DataFrame([dados])], ignore_index=True)
        conn.update(spreadsheet=MINHA_URL_PLANILHA, worksheet=aba, data=df_novo)
        st.toast("Progresso sincronizado! ☁️")
    except Exception as e:
        st.error(f"Erro ao salvar na aba {aba}. Verifique se ela existe e se o robô é Editor.")

# --- INICIALIZAÇÃO DE SESSÃO ---
if 'autenticado' not in st.session_state: st.session_state.autenticado = False

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;">', unsafe_allow_html=True)
    st.image(URL_BRASAO, width=100)
    st.title("ESTRATÉGIA GABARITO")
    u_input = st.text_input("Usuário PM:").strip().lower()
    p_input = st.text_input("Senha:", type="password").strip()
    if st.button("INICIAR MISSÃO"):
        try:
            df_u = conn.read(spreadsheet=MINHA_URL_PLANILHA, worksheet="Usuarios", ttl="1m")
            if not df_u.empty:
                valido = False
                for i, r in df_u.iterrows():
                    if str(r.iloc[0]).strip().lower() == u_input and str(r.iloc[1]).strip() == p_input:
                        valido = True; break
                if valido:
                    st.session_state.autenticado = True
                    st.session_state.usuario = u_input
                    st.rerun()
                else: st.error("❌ Credenciais inválidas.")
        except: st.error("⚠️ Erro: Adicione o e-mail do robô como EDITOR na planilha.")
    st.stop()

# --- CARREGAR HISTÓRICOS ---
try:
    df_hist_q = conn.read(spreadsheet=MINHA_URL_PLANILHA, worksheet="Log_Progresso", ttl=0)
    df_hist_a = conn.read(spreadsheet=MINHA_URL_PLANILHA, worksheet="Assuntos_Estudados", ttl=0)
except:
    df_hist_q = pd.DataFrame()
    df_hist_a = pd.DataFrame()
    st.warning("⚠️ Abas de Log não encontradas. Crie 'Log_Progresso' e 'Assuntos_Estudados' na planilha.")

# --- SIDEBAR ---
st.sidebar.image(URL_BRASAO, width=60)
st.sidebar.title(f"Sgt {st.session_state.usuario.upper()}")
menu = st.sidebar.radio("Navegação:", ["📝 Simulado", "📊 Performance", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.autenticado = False
    st.rerun()

# --- MODO SIMULADO ---
if menu == "📝 Simulado":
    area = st.sidebar.selectbox("Área do Edital:", ["Legislacao_Institucional", "Doutrina_Operacional", "Legislacao_Juridica"])
    df_q = conn.read(spreadsheet=MINHA_URL_PLANILHA, worksheet=area, ttl="2m")
    
    if not df_q.empty:
        # Colunas L(11) e M(12) - Lógica de filtro robusta
        lista_leis = sorted([x for x in df_q.iloc[:, 11].unique() if str(x) != 'nan' and str(x).strip() != ''])
        sel_lei = st.selectbox("🎯 1. Selecione a Lei ou Manual:", lista_leis)
        
        df_f_lei = df_q[df_q.iloc[:, 11] == sel_lei]
        lista_titulos = sorted([x for x in df_f_lei.iloc[:, 12].unique() if str(x) != 'nan' and str(x).strip() != ''])
        sel_titulo = st.selectbox(f"📖 2. Tópico de {sel_lei}:", ["VER TODOS"] + lista_titulos)

        # MARCAÇÃO DE TÓPICO COMO ESTUDADO
        if sel_titulo != "VER TODOS":
            identificador = f"{sel_lei} - {sel_titulo}"
            # Verifica no histórico
            ja_estudou = False
            if not df_hist_a.empty:
                ja_estudou = not df_hist_a[(df_hist_a['Usuario'] == st.session_state.usuario) & (df_hist_a['Topico'] == identificador)].empty
            
            if ja_estudou:
                st.markdown(f'<div class="check-assunto">✅ Este tópico já consta como estudado em seu prontuário.</div>', unsafe_allow_html=True)
            else:
                if st.button(f"Marcar '{sel_titulo}' como Estudado"):
                    registrar_log("Assuntos_Estudados", {
                        "Usuario": st.session_state.usuario, "Materia": sel_lei, 
                        "Topico": identificador, "Status": "Concluído", "Data": datetime.datetime.now().strftime("%d/%m/%Y")
                    })
                    st.rerun()

        st.divider()

        # EXIBIÇÃO DAS QUESTÕES
        df_exibir = df_f_lei if sel_titulo == "VER TODOS" else df_f_lei[df_f_lei.iloc[:, 12] == sel_titulo]
        
        # Lista de questões já feitas pelo usuário
        minhas_questoes = []
        if not df_hist_q.empty:
            minhas_questoes = df_hist_q[df_hist_q['Usuario'] == st.session_state.usuario]['Questao'].tolist()

        for i, row in df_exibir.iterrows():
            q_id = str(row.iloc[0])
            fez_q = q_id in minhas_questoes
            badge = '<span class="status-badge concluido">RESOLVIDA</span>' if fez_q else '<span class="status-badge pendente">PENDENTE</span>'
            
            with st.container():
                st.markdown(f'<div class="question-box"><b>QUESTÃO {q_id}</b> {badge}<br><br>{row.iloc[3]}</div>', unsafe_allow_html=True)
                
                # Alternativas A(4), B(5), C(6), D(7)
                ops = {"A": row.iloc[4], "B": row.iloc[5], "C": row.iloc[6], "D": row.iloc[7]}
                ops_v = {k: v for k, v in ops.items() if str(v).strip() != '' and str(v).lower() != 'nan'}
                
                escolha = st.radio(f"Selecione (Q{q_id}):", list(ops_v.values()), key=f"r_{q_id}")
                
                if st.button(f"Validar Questão {q_id}", key=f"b_{q_id}"):
                    letra = [l for l, t in ops_v.items() if t == escolha][0]
                    gab = str(row.iloc[8]).strip().upper()
                    status = "Acerto" if letra == gab else "Erro"
                    
                    registrar_log("Log_Progresso", {
                        "Usuario": st.session_state.usuario, "Materia": sel_lei, "Titulo": sel_titulo,
                        "Questao": q_id, "Status": status, "Data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    })
                    
                    if status == "Acerto": st.success("🎯 Correto!")
                    else: st.error(f"❌ Incorreto. Gabarito: {gab}")
                    st.info(f"💡 Base: {row.iloc[9]}")

# --- MODO PERFORMANCE ---
elif menu == "📊 Performance":
    st.header("📊 Inteligência de Desempenho")
    if not df_hist_q.empty:
        meu_h = df_hist_q[df_hist_q['Usuario'] == st.session_state.usuario]
        if not meu_h.empty:
            total = len(meu_h)
            acertos = len(meu_h[meu_h['Status'] == 'Acerto'])
            st.metric("Aproveitamento Geral", f"{(acertos/total*100):.1f}%", f"{total} questões feitas")
            fig = px.pie(names=['Acertos', 'Erros'], values=[acertos, total-acertos], color_discrete_sequence=['#28a745', '#dc3545'], hole=.4)
            st.plotly_chart(fig)
        else: st.info("Resolva questões para gerar dados.")
    else: st.info("Sem histórico registrado.")
