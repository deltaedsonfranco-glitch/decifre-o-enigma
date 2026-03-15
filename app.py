import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import plotly.express as px

# 1. ESTILO E IDENTIDADE VISUAL DE ELITE (CSS)
st.set_page_config(page_title="QG DO EAP - Estratégia Gabarito", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    
    /* Card de Questão Moderno */
    .question-box {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        border-left: 8px solid #1e3a8a;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        color: #1e293b;
    }
    
    /* Badges de Status */
    .status-badge {
        font-weight: 700;
        font-size: 0.75rem;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .concluido { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .pendente { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    
    /* Banner de Assunto Concluído */
    .check-assunto {
        background: linear-gradient(90deg, #dcfce7 0%, #ffffff 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #bbf7d0;
        margin-bottom: 25px;
        font-weight: 600;
        color: #166534;
    }

    /* Botões */
    .stButton>button { border-radius: 8px !important; font-weight: bold !important; transition: 0.3s; }
    .stButton>button:hover { background-color: #1e3a8a !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bras%C3%A3o_da_PMMG.svg/1200px-Bras%C3%A3o_da_PMMG.svg.png"

# --- CONEXÃO COM O BANCO DE DADOS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Tenta obter a URL dos Secrets
    MINHA_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except Exception as e:
    st.error("⚠️ Falha crítica: Arquivo de configuração (Secrets) não encontrado ou inválido.")
    st.info("Verifique se o seu 'secrets.toml' está na pasta '.streamlit' e se usa o sinal '='.")
    st.stop()

# --- FUNÇÃO DE REGISTRO EM BANCO ---
def registrar_log(aba, dados):
    try:
        df_atual = conn.read(spreadsheet=MINHA_URL, worksheet=aba, ttl=0)
        df_novo = pd.concat([df_atual, pd.DataFrame([dados])], ignore_index=True)
        conn.update(spreadsheet=MINHA_URL, worksheet=aba, data=df_novo)
        st.toast(f"Progresso sincronizado com a nuvem! ✅")
    except Exception as e:
        st.error(f"Erro ao salvar na aba {aba}. Verifique a permissão do robô.")

# --- CONTROLE DE ACESSO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;">', unsafe_allow_html=True)
    st.image(URL_BRASAO, width=120)
    st.title("ESTRATÉGIA GABARITO")
    st.subheader("🛡️ Plataforma de Elite EAP")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            u_input = st.text_input("Usuário PM:").strip().lower()
            p_input = st.text_input("Senha:", type="password").strip()
            submit = st.form_submit_button("INICIAR MISSÃO", use_container_width=True)
            
            if submit:
                try:
                    df_u = conn.read(spreadsheet=MINHA_URL, worksheet="Usuarios", ttl=0)
                    user_row = df_u[df_u.iloc[:, 0].astype(str).str.lower() == u_input]
                    if not user_row.empty:
                        if str(user_row.iloc[0, 1]).strip() == p_input:
                            st.session_state.autenticado = True
                            st.session_state.usuario = u_input
                            st.rerun()
                        else: st.error("❌ Senha incorreta.")
                    else: st.error("❌ Usuário não cadastrado.")
                except Exception as e:
                    st.error("⚠️ Erro de conexão com a aba 'Usuarios'.")
                    st.code(f"Diagnóstico: {e}")
    st.stop()

# --- CARREGAR HISTÓRICOS (PROGRESSO) ---
try:
    df_hist_q = conn.read(spreadsheet=MINHA_URL, worksheet="Log_Progresso", ttl=0)
    df_hist_a = conn.read(spreadsheet=MINHA_URL, worksheet="Assuntos_Estudados", ttl=0)
except:
    df_hist_q = pd.DataFrame(); df_hist_a = pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.image(URL_BRASAO, width=80)
st.sidebar.markdown(f"### 🎖️ Sgt {st.session_state.usuario.upper()}")
st.sidebar.divider()
menu = st.sidebar.radio("Navegação:", ["📝 Simulado", "📊 Performance", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.autenticado = False
    st.rerun()

# --- MODO SIMULADO ---
if menu == "📝 Simulado":
    area = st.sidebar.selectbox("Área do Edital:", ["Legislacao_Institucional", "Doutrina_Operacional", "Legislacao_Juridica"])
    
    try:
        # Tenta ler a aba de questões selecionada
        df_q = conn.read(spreadsheet=MINHA_URL, worksheet=area, ttl="2m")
        
        if not df_q.empty:
            # Filtros dinâmicos baseados nas colunas L(11) e M(12)
            leis = sorted([x for x in df_q.iloc[:, 11].unique() if str(x).strip() != '' and str(x) != 'nan'])
            sel_lei = st.selectbox("🎯 Selecione a Disciplina/Manual:", leis)
            
            df_f_lei = df_q[df_q.iloc[:, 11] == sel_lei]
            titulos = sorted([x for x in df_f_lei.iloc[:, 12].unique() if str(x).strip() != '' and str(x) != 'nan'])
            sel_titulo = st.selectbox(f"📖 Tópico de estudo:", ["EXIBIR TUDO"] + titulos)

            # --- LOGICA DE ASSUNTO ESTUDADO ---
            if sel_titulo != "EXIBIR TUDO":
                id_a = f"{sel_lei} - {sel_titulo}"
                ja = not df_hist_a[(df_hist_a['Usuario'] == st.session_state.usuario) & (df_hist_a['Topico'] == id_a)].empty if not df_hist_a.empty else False
                
                if ja:
                    st.markdown(f'<div class="check-assunto">✅ MISSÃO CUMPRIDA: Você já marcou este tópico como estudado.</div>', unsafe_allow_html=True)
                else:
                    if st.button(f"🏁 Finalizei o estudo de '{sel_titulo}'"):
                        registrar_log("Assuntos_Estudados", {
                            "Usuario": st.session_state.usuario, "Materia": sel_lei, 
                            "Topico": id_a, "Status": "Concluído", "Data": datetime.datetime.now().strftime("%d/%m/%Y")
                        })
                        st.rerun()

            st.divider()

            # --- EXIBIÇÃO DAS QUESTÕES ---
            df_exibir = df_f_lei if sel_titulo == "EXIBIR TUDO" else df_f_lei[df_f_lei.iloc[:, 12] == sel_titulo]
            minhas_q = df_hist_q[df_hist_q['Usuario'] == st.session_state.usuario]['Questao'].tolist() if not df_hist_q.empty else []

            for i, row in df_exibir.iterrows():
                q_id = str(row.iloc[0])
                ja_fez = q_id in minhas_q
                status_html = '<span class="status-badge concluido">RESOLVIDA</span>' if ja_fez else '<span class="status-badge pendente">PENDENTE</span>'
                
                with st.container():
                    st.markdown(f'<div class="question-box"><b>QUESTÃO {q_id}</b> {status_html}<br><br>{row.iloc[3]}</div>', unsafe_allow_html=True)
                    
                    # Colunas A a D (4, 5, 6, 7)
                    ops = {"A": row.iloc[4], "B": row.iloc[5], "C": row.iloc[6], "D": row.iloc[7]}
                    ops_v = {k: v for k, v in ops.items() if str(v).strip() != '' and str(v).lower() != 'nan'}
                    
                    escolha = st.radio(f"Selecione (Q{q_id}):", list(ops_v.values()), key=f"r_{q_id}", label_visibility="collapsed")
                    
                    if st.button(f"Validar Q{q_id}", key=f"b_{q_id}", use_container_width=True):
                        letra = [l for l, t in ops_v.items() if t == escolha][0]
                        gab = str(row.iloc[8]).strip().upper()
                        status = "Acerto" if letra == gab else "Erro"
                        
                        registrar_log("Log_Progresso", {
                            "Usuario": st.session_state.usuario, "Materia": sel_lei, "Titulo": sel_titulo,
                            "Questao": q_id, "Status": status, "Data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        })
                        
                        if status == "Acerto": st.success("🎯 Resposta Correta! Alvo batido.")
                        else: st.error(f"❌ Incorreto. O gabarito é ({gab})")
                        st.info(f"💡 Base Legal: {row.iloc[9]}")

    except Exception as e:
        st.error(f"⚠️ Erro ao acessar a aba '{area}'.")
        st.info("Verifique se o nome da aba na planilha é exatamente esse, sem acentos.")

# --- MODO PERFORMANCE ---
elif menu == "📊 Performance":
    st.header("📊 Inteligência de Desempenho")
    if not df_hist_q.empty:
        meu_h = df_hist_q[df_hist_q['Usuario'] == st.session_state.usuario]
        if not meu_h.empty:
            total = len(meu_h)
            acertos = len(meu_h[meu_h['Status'] == 'Acerto'])
            st.metric("Taxa de Sucesso", f"{(acertos/total*100):.1f}%", f"{total} questões respondidas")
            
            fig = px.pie(names=['Acertos', 'Erros'], values=[acertos, total-acertos], 
                         color_discrete_sequence=['#28a745', '#dc3545'], hole=.4)
            st.plotly_chart(fig)
        else: st.info("Resolva questões para visualizar sua performance.")
    else: st.info("Ainda não há dados de progresso registrados.")
