import streamlit as st
import pandas as pd
import unicodedata
import time
import plotly.express as px

# 1. CONFIGURAÇÃO DE PÁGINA "DECIFRE O ENIGMA"
st.set_page_config(page_title="Decifre o Enigma - EAP", page_icon="🛡️", layout="wide")

ID_PLANILHA = "1bV86Twi_Mm4mgMOzoyZFdncEmgud4rAzP9lSvmnCYUM"
URL_BRASAO = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Bras%C3%A3o_da_PMMG.svg/1200px-Bras%C3%A3o_da_PMMG.svg.png"

# Inicialização de Variáveis de Sessão
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'inicio_sessao' not in st.session_state: st.session_state.inicio_sessao = time.time()
if 'historico_questoes' not in st.session_state: st.session_state.historico_questoes = []
if 'materias_concluidas' not in st.session_state: st.session_state.materias_concluidas = set()

def normalizar_cabecalho(txt):
    txt = "".join(c for c in unicodedata.normalize('NFD', str(txt)) if unicodedata.category(c) != 'Mn')
    txt = txt.lower().strip()
    return txt.split()[0] if txt else "coluna"

@st.cache_data(ttl=10)
def load_data(nome_aba):
    url = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv&sheet={nome_aba.replace(' ', '%20')}"
    try:
        df = pd.read_csv(url, dtype=str)
        df.columns = [normalizar_cabecalho(c) for c in df.columns]
        return df.apply(lambda x: x.str.strip() if hasattr(x, 'str') else x).fillna("")
    except: return pd.DataFrame()

# --- LOGIN ---
if not st.session_state.autenticado:
    st.markdown("""<style>.login-card { text-align: center; padding: 40px; background: #f0f2f6; border-radius: 20px; border-top: 12px solid #1c83e1; margin: auto; max-width: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }</style>""", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image(URL_BRASAO, width=100)
        st.title("Decifre o Enigma")
        u_input = st.text_input("Usuário:")
        p_input = st.text_input("Senha:", type="password")
        if st.button("INICIAR MISSÃO"):
            df_u = load_data("Usuarios")
            if not df_u.empty:
                col_u = df_u.columns[0]
                if u_input in df_u[col_u].values:
                    linha = df_u[df_u[col_u] == u_input]
                    if p_input == str(linha.iloc[0, 1]):
                        st.session_state.autenticado = True
                        st.session_state.usuario = u_input
                        st.session_state.inicio_sessao = time.time()
                        st.rerun()
                    else: st.error("Senha incorreta.")
                else: st.error("Usuário não cadastrado.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- HEADER INTERNO ---
c1, c2 = st.columns([1, 6])
with c1: st.image(URL_BRASAO, width=80)
with c2: 
    st.title("Decifre o Enigma")
    st.caption(f"🛡️ Logado como: Sgt {st.session_state.usuario}")

# --- SIDEBAR ---
tempo_estudo = int(time.time() - st.session_state.inicio_sessao)
hrs, rem = divmod(tempo_estudo, 3600)
mins, segs = divmod(rem, 60)
st.sidebar.write(f"⏱️ **Tempo de Missão:** `{hrs:02d}:{mins:02d}:{segs:02d}`")

menu = st.sidebar.radio("Navegação:", ["📝 Simulado Principal", "📖 Teoria (Busca Ativa)", "📊 Performance"])

if st.sidebar.button("🔄 Reiniciar Status Quo"):
    st.session_state.historico_questoes = []
    st.session_state.materias_concluidas = set()
    st.rerun()

# --- MODO SIMULADO (RESTAURADO) ---
if menu == "📝 Simulado Principal":
    area_sel = st.sidebar.selectbox("Área do Edital:", ["Legislacao_Institucional", "Doutrina_Operacional", "Legislacao_Juridica"])
    df_q = load_data(area_sel)
    
    if not df_q.empty:
        col_m = 'materia' if 'materia' in df_q.columns else df_q.columns[1]
        materias = sorted(df_q[col_m].unique())
        
        mats_display = [f"{'✅' if m in st.session_state.materias_concluidas else '⚪'} {m}" for m in materias]
        sel_formatada = st.sidebar.selectbox("Filtrar Disciplina:", ["TODAS"] + mats_display)
        sel_m = sel_formatada[2:] if sel_formatada != "TODAS" else "TODAS"
        
        if sel_m != "TODAS":
            ja_estudada = sel_m in st.session_state.materias_concluidas
            if st.sidebar.button("Marcar como Concluída ✅" if not ja_estudada else "Matéria Estudada ✅"):
                st.session_state.materias_concluidas.add(sel_m)
                st.rerun()

        df_f = df_q if sel_m == "TODAS" else df_q[df_q[col_m] == sel_m]

        for i, row in df_f.iterrows():
            with st.container():
                st.markdown(f'<div style="background:white; padding:20px; border-radius:10px; border-left:8px solid #1c83e1; margin-bottom:15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);"><b>QUESTÃO {row.get("id", i+1)}</b> | {row.get(col_m)}<br><br>{row.get("pergunta")}</div>', unsafe_allow_html=True)
                
                # Montagem das Opções A, B, C, D
                ops = {"A": row.get('a'), "B": row.get('b'), "C": row.get('c'), "D": row.get('d')}
                ops_v = {k: v for k, v in ops.items() if str(v).lower() != 'nan' and v != ""}
                
                if ops_v:
                    escolha = st.radio(f"Selecione a resposta para Q{row.get('id')}:", list(ops_v.values()), key=f"rad_{i}_{area_sel}")
                    
                    if st.button(f"Validar Q{row.get('id')}", key=f"btn_{i}_{area_sel}"):
                        letra_sel = [l for l, t in ops_v.items() if t == escolha][0]
                        gab = str(row.get('correta')).strip().upper()
                        status = "Acerto" if letra_sel == gab else "Erro"
                        
                        st.session_state.historico_questoes.append({'area': area_sel, 'materia': row.get(col_m), 'status': status})
                        
                        if status == "Acerto": st.success("🎯 Resposta Correta!")
                        else: st.error(f"❌ Incorreto. Gabarito: ({gab})")
                        st.info(f"💡 Explicação: {row.get('explicacao', 'Consulte o manual correspondente.')}")
                st.divider()

# --- MODO TEORIA (COM BUSCA ATIVA) ---
elif menu == "📖 Teoria (Busca Ativa)":
    st.header("📖 Centro de Difusão de Teoria")
    busca = st.text_input("🔍 Decifre o Enigma (Busca por Artigo, Assunto ou Palavra-Chave):", "").strip().lower()
    df_t = load_data("Explicacoes_Teoria")
    
    if not df_t.empty:
        col_mat_t = df_t.columns[0]
        mats_t = sorted(df_t[col_mat_t].unique())
        sel_t = st.sidebar.selectbox("📚 Filtrar por Matéria:", ["TODAS"] + list(mats_t))
        df_t_f = df_t if sel_t == "TODAS" else df_t[df_t[col_mat_t] == sel_t]
        
        if busca:
            df_t_f = df_t_f[df_t_f.apply(lambda row: busca in str(row).lower(), axis=1)]
        
        for idx, r in df_t_f.iterrows():
            txt_teoria = str(r.iloc[2]).replace('\n', '<br>')
            with st.expander(f"📌 {r.iloc[0]} | {r.iloc[1]}"):
                st.markdown(f"""<div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-right: 8px solid #1c83e1; margin-bottom: 10px;">
                    <div style='font-size:18px; color: #2c3e50; line-height: 1.6;'>{txt_teoria}</div>
                    <hr><small style='color: #666;'><b>Palavras-chave:</b> {r.iloc[3] if len(r)>3 else ""}</small>
                </div>""", unsafe_allow_html=True)

# --- MODO PERFORMANCE ---
elif menu == "📊 Performance":
    st.header("📊 Análise de Desempenho")
    if st.session_state.historico_questoes:
        df_hist = pd.DataFrame(st.session_state.historico_questoes)
        fig = px.sunburst(df_hist, path=['area', 'status'], color='status',
                           color_discrete_map={'Acerto': '#28a745', 'Erro': '#dc3545'})
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Resolva questões para gerar seu gráfico de aproveitamento.")