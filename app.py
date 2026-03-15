import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import time
import plotly.express as px

# 1. ESTILO VISUAL DE ELITE
st.set_page_config(page_title="QG DO EAP - Estratégia Gabarito", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .question-box {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        border-left: 8px solid #1e3a8a;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        color: #1e293b;
    }
    .status-badge { font-weight: 700; font-size: 0.75rem; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; }
    .concluido { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .pendente { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
    .check-assunto {
        background: linear-gradient(90deg, #dcfce7 0%, #ffffff 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #bbf7d0; margin-bottom: 25px; font-weight: 600; color: #166534;
    }
    </style>
""", unsafe_allow_html=True)

URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bras%C3%A3o_da_PMMG.svg/1200px-Bras%C3%A3o_da_PMMG.svg.png"

# CONEXÃO
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    MINHA_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except:
    st.error("⚠️ Erro nos Secrets do VS Code (.streamlit/secrets.toml)")
    st.stop()

# FUNÇÃO DE REGISTRO
def registrar_log(aba, dados):
    try:
        df_atual = conn.read(spreadsheet=MINHA_URL, worksheet=aba, ttl=0)
        df_novo = pd.concat([df_atual, pd.DataFrame([dados])], ignore_index=True)
        conn.update(spreadsheet=MINHA_URL, worksheet=aba, data=df_novo)
        st.toast("Sincronizado! ✅")
    except: pass

if 'autenticado' not in st.session_state: st.session_state.autenticado = False

# --- LOGIN ---
if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;">', unsafe_allow_html=True)
    st.image(URL_BRASAO, width=120)
    st.title("ESTRATÉGIA GABARITO")
    with st.form("login"):
        u_input = st.text_input("Usuário PM:").strip().lower()
        p_input = st.text_input("Senha:", type="password").strip()
        if st.form_submit_button("INICIAR MISSÃO"):
            df_u = conn.read(spreadsheet=MINHA_URL, worksheet="Usuarios", ttl=0)
            user_row = df_u[df_u.iloc[:, 0].astype(str).str.lower().str.strip() == u_input]
            if not user_row.empty and str(user_row.iloc[0, 1]).strip() == p_input:
                st.session_state.autenticado = True
                st.session_state.usuario = u_input
                st.rerun()
            else: st.error("Dados incorretos.")
    st.stop()

# --- CARREGAR HISTÓRICOS ---
df_hist_q = conn.read(spreadsheet=MINHA_URL, worksheet="Log_Progresso", ttl=0)
df_hist_a = conn.read(spreadsheet=MINHA_URL, worksheet="Assuntos_Estudados", ttl=0)

# --- NAVEGAÇÃO ---
st.sidebar.image(URL_BRASAO, width=80)
menu = st.sidebar.radio("Menu:", ["📝 Simulado", "📊 Performance", "🚪 Sair"])

if menu == "🚪 Sair":
    st.session_state.autenticado = False
    st.rerun()

if menu == "📝 Simulado":
    area = st.sidebar.selectbox("Área:", ["Legislacao_Institucional", "Doutrina_Operacional", "Legislacao_Juridica"])
    try:
        df_q = conn.read(spreadsheet=MINHA_URL, worksheet=area, ttl="2m")
        if not df_q.empty:
            # TRAVA DE SEGURANÇA: Limpa espaços em branco dos nomes das matérias (Coluna L)
            df_q.iloc[:, 11] = df_q.iloc[:, 11].astype(str).str.strip()
            df_q.iloc[:, 12] = df_q.iloc[:, 12].astype(str).str.strip()
            
            leis = sorted([x for x in df_q.iloc[:, 11].unique() if x != 'nan' and x != ''])
            sel_lei = st.selectbox("🎯 Disciplina:", leis)
            
            df_f_lei = df_q[df_q.iloc[:, 11] == sel_lei]
            titulos = sorted([x for x in df_f_lei.iloc[:, 12].unique() if x != 'nan' and x != ''])
            sel_titulo = st.selectbox("📖 Tópico:", ["VER TUDO"] + titulos)

            # Marcação de Assunto Estudado
            if sel_titulo != "VER TUDO":
                id_a = f"{sel_lei} - {sel_titulo}"
                ja = not df_hist_a[(df_hist_a['Usuario'] == st.session_state.usuario) & (df_hist_a['Topico'].str.strip() == id_a)].empty if not df_hist_a.empty else False
                if ja: st.markdown('<div class="check-assunto">✅ Tópico já estudado.</div>', unsafe_allow_html=True)
                else:
                    if st.button("🏁 Marcar como Estudado"):
                        registrar_log("Assuntos_Estudados", {"Usuario": st.session_state.usuario, "Materia": sel_lei, "Topico": id_a, "Status": "Concluído", "Data": datetime.datetime.now().strftime("%d/%m/%Y")})
                        st.rerun()

            df_exibir = df_f_lei if sel_titulo == "VER TUDO" else df_f_lei[df_f_lei.iloc[:, 12] == sel_titulo]
            minhas_q = df_hist_q[df_hist_q['Usuario'] == st.session_state.usuario]['Questao'].astype(str).tolist() if not df_hist_q.empty else []

            for i, row in df_exibir.iterrows():
                q_id = str(row.iloc[0])
                badge = '<span class="status-badge concluido">RESOLVIDA</span>' if q_id in minhas_q else '<span class="status-badge pendente">PENDENTE</span>'
                with st.container():
                    st.markdown(f'<div class="question-box"><b>Q{q_id}</b> {badge}<br><br>{row.iloc[3]}</div>', unsafe_allow_html=True)
                    ops = {"A": row.iloc[4], "B": row.iloc[5], "C": row.iloc[6], "D": row.iloc[7]}
                    ops_v = {k: v for k, v in ops.items() if str(v).strip() != '' and str(v).lower() != 'nan'}
                    escolha = st.radio(f"Opção Q{q_id}:", list(ops_v.values()), key=f"r_{q_id}", label_visibility="collapsed")
                    if st.button(f"Validar Q{q_id}", key=f"b_{q_id}"):
                        letra = [l for l, t in ops_v.items() if t == escolha][0]
                        gab = str(row.iloc[8]).strip().upper()
                        status = "Acerto" if letra == gab else "Erro"
                        registrar_log("Log_Progresso", {"Usuario": st.session_state.usuario, "Materia": sel_lei, "Titulo": sel_titulo, "Questao": q_id, "Status": status, "Data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")})
                        if status == "Acerto": st.success("🎯 Correto!")
                        else: st.error(f"❌ Gabarito: {gab}")
                        st.info(f"💡 Dica: {row.iloc[9]}")
    except Exception as e: st.error(f"Erro na aba {area}: {e}")

elif menu == "📊 Performance":
    st.header("📊 Performance")
    if not df_hist_q.empty:
        meu_h = df_hist_q[df_hist_q['Usuario'] == st.session_state.usuario]
        if not meu_h.empty:
            acertos = len(meu_h[meu_h['Status'] == 'Acerto'])
            st.metric("Aproveitamento", f"{(acertos/len(meu_h)*100):.1f}%")
            st.plotly_chart(px.pie(names=['Acertos', 'Erros'], values=[acertos, len(meu_h)-acertos], color_discrete_sequence=['#28a745', '#dc3545']))
