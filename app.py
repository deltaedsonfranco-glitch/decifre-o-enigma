import streamlit as st
import pandas as pd
import unicodedata
import time
import plotly.express as px

# 1. CONFIGURAÇÃO DE IDENTIDADE E CURSOR (MÃOZINHA)
st.set_page_config(page_title="ESTRATÉGIA GABARITO - Missão 3º Sgt", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* Forçar cursor de mãozinha em elementos interativos */
    button, .stButton>button, .streamlit-expanderHeader, [data-baseweb="select"], .stRadio label, .stSelectbox {
        cursor: pointer !important;
    }
    .theory-card { background: white; padding: 25px; border-radius: 12px; border-left: 10px solid #1c83e1; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 25px; }
    .question-box { background: #fdfdfd; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

ID_PLANILHA = "1bV86Twi_Mm4mgMOzoyZFdncEmgud4rAzP9lSvmnCYUM"
URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bras%C3%A3o_da_PMMG.svg/1200px-Bras%C3%A3o_da_PMMG.svg.png"

# Inicialização de Memória de Estudo
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'historico_questoes' not in st.session_state: st.session_state.historico_questoes = []
if 'progresso_local' not in st.session_state: st.session_state.progresso_local = {}

@st.cache_data(ttl=5)
def load_data(nome_aba):
    url = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet={nome_aba.replace(' ', '%20')}"
    try:
        df = pd.read_csv(url, dtype=str).fillna("")
        return df.apply(lambda x: x.str.strip() if hasattr(x, 'str') else x)
    except: return pd.DataFrame()

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown('<div style="text-align:center; padding-top: 50px;">', unsafe_allow_html=True)
    st.image(URL_BRASAO, width=100)
    st.title("ESTRATÉGIA GABARITO")
    st.subheader("🛡️ Missão 3º Sargento")
    
    col_l1, col_l2, col_l3 = st.columns([1,2,1])
    with col_l2:
        u_input = st.text_input("Usuário PM:")
        p_input = st.text_input("Senha de Acesso:", type="password")
        if st.button("INICIAR MISSÃO"):
            df_u = load_data("Usuarios")
            if not df_u.empty:
                if u_input in df_u.iloc[:, 0].values:
                    linha = df_u[df_u.iloc[:, 0] == u_input]
                    if p_input == str(linha.iloc[0, 1]):
                        st.session_state.autenticado = True
                        st.session_state.usuario = u_input
                        st.rerun()
                    else: st.error("Senha incorreta.")
                else: st.error("Usuário não autorizado.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- BARRA LATERAL (RANKING E LOGOUT) ---
st.sidebar.image(URL_BRASAO, width=60)
st.sidebar.markdown(f"### Sgt {st.session_state.usuario}")

# Cálculo do Ranking Privado
if st.session_state.historico_questoes:
    df_h = pd.DataFrame(st.session_state.historico_questoes)
    acertos = len(df_h[df_h['status'] == 'Acerto'])
    total = len(df_h)
    perc = (acertos/total*100)
    st.sidebar.metric("Seu Aproveitamento", f"{perc:.1f}%")
    st.sidebar.write(f"✅ {acertos} de {total} questões")

st.sidebar.divider()
menu = st.sidebar.radio("Navegação Principal:", ["📝 Simulado", "📖 Teoria", "📊 Performance"])

st.sidebar.divider()
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

# --- MODO SIMULADO (COLUNAS L E M) ---
if menu == "📝 Simulado":
    st.header("📝 Treinamento por Questões")
    area = st.sidebar.selectbox("Área do Edital:", ["Legislacao_Institucional", "Doutrina_Operacional", "Legislacao_Juridica"])
    
    # Exibir onde parou
    if area in st.session_state.progresso_local:
        st.info(f"📍 Último estudo nesta área: {st.session_state.progresso_local[area]}")

    df_q = load_data(area)
    
    if not df_q.empty:
        try:
            # Filtro pela Coluna L (Lei/Manual) - Índice 11
            col_l_idx = 11
            # Filtro pela Coluna M (Título/Capítulo) - Índice 12
            col_m_idx = 12
            
            lista_leis = sorted(df_q.iloc[:, col_l_idx].unique())
            sel_lei = st.selectbox("🎯 1. Selecione a Lei ou Manual:", lista_leis)
            
            df_f_lei = df_q[df_q.iloc[:, col_l_idx] == sel_lei]
            lista_titulos = sorted(df_f_lei.iloc[:, col_m_idx].unique())
            
            sel_titulo = st.selectbox(f"📖 2. Tópico de {sel_lei}:", ["VER TODOS"] + lista_titulos)
            
            # Registrar progresso na sessão
            st.session_state.progresso_local[area] = f"{sel_lei} > {sel_titulo}"

            df_final = df_f_lei if sel_titulo == "VER TODOS" else df_f_lei[df_f_lei.iloc[:, col_m_idx] == sel_titulo]

            for i, row in df_final.iterrows():
                with st.container():
                    st.markdown(f'<div class="question-box"><b>QUESTÃO {row.iloc[0]}</b><br><small>{sel_lei} | {row.iloc[col_m_idx]}</small><br><br>{row.iloc[3]}</div>', unsafe_allow_html=True)
                    
                    # Alternativas E, F, G, H (Indices 4, 5, 6, 7)
                    ops = {"A": row.iloc[4], "B": row.iloc[5], "C": row.iloc[6], "D": row.iloc[7]}
                    ops_v = {k: v for k, v in ops.items() if v != ""}
                    
                    escolha = st.radio(f"Resposta para a Questão {row.iloc[0]}:", list(ops_v.values()), key=f"rad_{i}_{area}")
                    
                    if st.button(f"Validar Q{row.iloc[0]}", key=f"btn_{i}_{area}"):
                        letra_sel = [l for l, t in ops_v.items() if t == escolha][0]
                        gab = str(row.iloc[8]).strip().upper() # Coluna I
                        status = "Acerto" if letra_sel == gab else "Erro"
                        
                        st.session_state.historico_questoes.append({'materia': sel_lei, 'status': status})
                        
                        if status == "Acerto": st.success("🎯 Alvo atingido! Resposta correta.")
                        else: st.error(f"❌ Falha na missão. Gabarito: ({gab})")
                        st.info(f"💡 Explicação: {row.iloc[9]}") # Coluna J
                    st.divider()
        except Exception as e:
            st.error(f"Erro ao ler colunas L e M. Verifique sua planilha. Detalhe: {e}")

# --- MODO TEORIA ---
elif menu == "📖 Teoria":
    st.header("📖 Caderno de Doutrina")
    df_t = load_data("Explicacoes_Teoria")
    if not df_t.empty:
        busca = st.text_input("🔍 O que deseja pesquisar na teoria?", "").lower()
        for idx, r in df_t.iterrows():
            if busca in str(r).lower():
                texto_formatado = str(r.iloc[2]).replace('\n', '<br>')
                with st.expander(f"📌 {r.iloc[0]} - {r.iloc[1]}"):
                    st.markdown(f'<div class="theory-card">{texto_formatado}</div>', unsafe_allow_html=True)

# --- MODO PERFORMANCE ---
elif menu == "📊 Performance":
    st.header("📊 Análise de Desempenho")
    if st.session_state.historico_questoes:
        df_perf = pd.DataFrame(st.session_state.historico_questoes)
        fig = px.bar(df_perf.groupby(['materia', 'status']).size().reset_index(name='Qtd'), 
                     x='materia', y='Qtd', color='status', barmode='group',
                     color_discrete_map={'Acerto': '#28a745', 'Erro': '#dc3545'},
                     title="Aproveitamento por Matéria")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Realize o simulado para visualizar estatísticas de combate.")
