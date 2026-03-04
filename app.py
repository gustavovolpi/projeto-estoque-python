import streamlit as st
import sqlite3
import pandas as pd
import unicodedata
from datetime import datetime, date, timedelta
import time
import io

# ==========================================================
# 1. CONFIGURAÇÕES INICIAIS E BANCO DE DADOS
# ==========================================
DB = "estoque.db"
LISTA_SETORES = ["ALMOXARIFADO", "DIRETORIA", "LIMPEZA", "PRODUCAO", "FABRICACAO", "MANUTENCAO", "ADMINISTRATIVO", "P&D", "QUALIDADE", "LOGISTICA", "ARMAZEM"]

if "logado" not in st.session_state: st.session_state.logado = False
if "form_reset_key" not in st.session_state: st.session_state.form_reset_key = 0
if "ordem_selecionada" not in st.session_state: st.session_state.ordem_selecionada = "Mais recentes primeiro"

def q(query, params=(), fetch=False):
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        res = cur.fetchall() if fetch else None
        conn.commit()
    return res

def normalizar(txt):
    if not txt: return ""
    txt = txt.strip().upper()
    txt = unicodedata.normalize("NFKD", txt)
    return "".join(c for c in txt if not unicodedata.combining(c))

def is_admin():
    return st.session_state.get("usuario") == "admin"

# Garantir que a coluna 'ativo' exista (Migração automática)
try:
    q("ALTER TABLE produtos ADD COLUMN ativo INTEGER DEFAULT 1")
except:
    pass

# --- MIGRACAO DATA/HORA SAIDA ---
try:
    q("ALTER TABLE saídas ADD COLUMN data_hora_saida DATETIME")
except:
    pass    

try:
    q("ALTER TABLE produtos ADD COLUMN embalagem_padrao TEXT DEFAULT 'un'")
except:
    pass

# ==========================================================
# 2. LOGIN E SEGURANÇA
# ==========================================================
st.set_page_config(layout="wide", page_title="Sistema de Estoque", page_icon="📦")

if not st.session_state.logado:
    st.title("🔐 Login")
    u = st.text_input("Usuário")
    s = st.text_input("Senha", type="password")
    if st.button("Entrar", key="login_btn"):
        user_data = q("SELECT username FROM usuarios WHERE username=? AND senha=?", (u, s), True)
        if user_data:
            st.session_state.logado = True
            st.session_state.usuario = user_data[0][0]
            st.rerun()
        else: st.error("Usuário ou senha inválidos")
    st.stop()

st.sidebar.write(f"👤 **{st.session_state.usuario}**")
if st.sidebar.button("Sair", key="logout_btn"):
    st.session_state.logado = False
    st.rerun()

aba_principal = st.sidebar.radio("Menu", ["📦 Estoque", "📜 Auditoria"])

# ==========================================================
# 3. ABA ESTOQUE
# ==========================================================
if aba_principal == "📦 Estoque":
    st.title("📦 Controle de Estoque")

        # Consulta alterada para Soft Delete
    prods = [p[0] for p in q("SELECT nome FROM produtos WHERE ativo = 1 ORDER BY nome", fetch=True)]

    # --- SEÇÃO DE ENTRADA ---
    with st.expander("➕ Entrada de Estoque", expanded=False):
        n_sel = st.selectbox("Produto", options=prods, index=None, key=f"ent_n_{st.session_state.form_reset_key}")
        n_ent = st.text_input("Novo Produto", key=f"ent_m_{st.session_state.form_reset_key}").upper() if n_sel is None else n_sel
        t_ent = st.selectbox("Tipo", ["Por unidade", "Por embalagem"], key=f"ent_t_{st.session_state.form_reset_key}")
        
        if t_ent == "Por unidade":
            q_ent = st.number_input("Qtd", min_value=0, key=f"ent_q_{st.session_state.form_reset_key}")
        else:
            c1, c2, c3 = st.columns(3)
            emb_d = [e[0] for e in q("SELECT nome FROM embalagens ORDER BY nome", fetch=True)]
            t_emb = c1.selectbox("Tipo Emb.", ["Selecionar..."] + emb_d, key=f"ent_te_{st.session_state.form_reset_key}")
            i_emb = c2.number_input("Itens/emb", min_value=1, key=f"ent_ie_{st.session_state.form_reset_key}")
            qe_emb = c3.number_input("Qtd emb", min_value=1, key=f"ent_qe_{st.session_state.form_reset_key}")
            q_ent = i_emb * qe_emb

        if st.button("Confirmar Entrada", key=f"btn_confirm_ent_{st.session_state.form_reset_key}"):
            n_norm = normalizar(n_ent)
            # Se o produto existia mas estava inativo, reativamos ele
            q("INSERT INTO produtos (nome, ativo) VALUES (?, 1) ON CONFLICT(nome) DO UPDATE SET ativo = 1", (n_norm,))
            q("INSERT INTO estoque_setores (produto, setor, quantidade) VALUES (?, 'ALMOXARIFADO', ?) ON CONFLICT(produto, setor) DO UPDATE SET quantidade = quantidade + ?", (n_norm, q_ent, q_ent))
            p_id = q("SELECT id FROM produtos WHERE nome=?", (n_norm,), True)[0][0]
            q("INSERT INTO entradas_unidade (produto_id, quantidade, usuario, tipo_movimentacao) VALUES (?, ?, ?, ?)", (p_id, q_ent, st.session_state.usuario, ""))
            st.success("Entrada realizada!"); st.session_state.form_reset_key += 1; time.sleep(1); st.rerun()

    # --- SEÇÃO DE SAÍDA ---
    with st.expander("➖ Saída / Retirada", expanded=False):
        item_s = st.selectbox("Item", options=prods, index=None, key=f"sai_n_{st.session_state.form_reset_key}")
        c_set, c_resp = st.columns(2)
        set_dest = c_set.selectbox("Destino", LISTA_SETORES, key=f"sai_sd_{st.session_state.form_reset_key}")
        
        l_col = q("SELECT DISTINCT UPPER(responsavel) FROM saídas WHERE responsavel IS NOT NULL AND responsavel != ''", fetch=True)
        lista_nomes = sorted([r[0] for r in l_col if r[0] and r[0] != "+ DIGITAR NOVO..."])
        sugs = ["+ DIGITAR NOVO..."] + lista_nomes                                         
        
        resp_sel = c_resp.selectbox("Responsável", sugs, key=f"sai_re_sel_{st.session_state.form_reset_key}")
        responsavel = c_resp.text_input("Nome", key=f"sai_re_new_{st.session_state.form_reset_key}").upper() if resp_sel == "+ DIGITAR NOVO..." else resp_sel
        qtd_s = st.number_input("Qtd Saída", min_value=1, key=f"sai_q_{st.session_state.form_reset_key}")

        # Novos campos de Data e Hora para Saída
        st.markdown("---")
        c_dt, c_hr = st.columns(2)
        data_s = c_dt.date_input("Data da Saída Real", value=datetime.now(), key=f"sai_dt_{st.session_state.form_reset_key}")
        hora_s = c_hr.time_input("Hora da Saída Real", value=datetime.now(), key=f"sai_hr_{st.session_state.form_reset_key}")
        
        # Combinação dos campos em um único datetime para o banco
        dt_saida_combinada = datetime.combine(data_s, hora_s).strftime('%Y-%m-%d %H:%M:%S')

        if st.button("Confirmar Saída", key=f"btn_confirm_sai_{st.session_state.form_reset_key}"):
            if item_s and responsavel and qtd_s > 0:
                n_norm_s = normalizar(item_s)
                saldo_atual = q("SELECT quantidade FROM estoque_setores WHERE produto=? AND setor='ALMOXARIFADO'", (n_norm_s,), True)
                saldo_disponivel = saldo_atual[0][0] if saldo_atual else 0
                
                if qtd_s > saldo_disponivel:
                    st.error(f"Estoque insuficiente! Saldo atual: {int(saldo_disponivel)} un")
                else:
                    p_id_s = q("SELECT id FROM produtos WHERE nome=?", (n_norm_s,), True)[0][0]
                    q("UPDATE estoque_setores SET quantidade = quantidade - ? WHERE produto=? AND setor='ALMOXARIFADO'", (qtd_s, n_norm_s))
                    
                    # INSERT ATUALIZADO COM A NOVA COLUNA
                    q("""INSERT INTO saídas (produto_id, quantidade, usuario, responsavel, observacao, data_hora_saida) 
                         VALUES (?, ?, ?, ?, ?, ?)""", 
                      (p_id_s, qtd_s, st.session_state.usuario, responsavel, f"PARA: {set_dest}", dt_saida_combinada))
                    
                    st.success("Saída registrada!")
                    st.session_state.form_reset_key += 1
                    time.sleep(1)
                    st.rerun()
            else:
                st.warning("Preencha todos os campos corretamente.")

    # --- GERENCIAR EMBALAGENS ---
    if is_admin():
        with st.expander("📦 Gerenciar Tipos de Embalagens", expanded=False):
            c_cad, c_btn = st.columns([4, 1], vertical_alignment="bottom")
            nova_emb = c_cad.text_input("Nome da Nova Embalagem", key="input_nova_emb_final")
            if c_btn.button("Cadastrar", key="btn_cad_emb_final", use_container_width=True):
                if nova_emb:
                    q("INSERT OR IGNORE INTO embalagens (nome) VALUES (?)", (nova_emb.strip().upper(),))
                    st.rerun()
            
            st.divider()
            st.subheader("🗑️ Remover Embalagens")
            embs = q("SELECT nome FROM embalagens ORDER BY nome", fetch=True)
            for emb_nome in [e[0] for e in embs]:
                col_n, col_l = st.columns([4, 1])
                col_n.write(f"• {emb_nome}")
                if col_l.button("🗑️", key=f"del_emb_{emb_nome}"):
                    q("DELETE FROM embalagens WHERE nome = ?", (emb_nome,))
                    st.rerun()

    # --- SALDO ATUAL ---
    st.divider()
    c_tit, c_atu = st.columns([4, 1], vertical_alignment="bottom")
    c_tit.subheader("📊 Saldo Atual")

    if c_atu.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # Campo de busca e filtros
    c_bus, c_pos, c_ord = st.columns([2.5, 1, 1.5], vertical_alignment="bottom")
    busca = c_bus.text_input("🔍 Buscar por nome do item", key="f_busca_vfinal")
    f_pos = c_pos.checkbox("Somente positivo", value=False, key="f_pos_check")

    op_ordem = ["Mais recentes primeiro", "Itens com alerta ativo", "Nome A-Z", "Nome Z-A", "Estoque baixo primeiro", "Estoque alto primeiro"]
    ordem = c_ord.selectbox("Ordenar por", op_ordem, index=0, key="f_ord_vfinal")

    # SQL base alterada para WHERE p.ativo = 1
    sql_base = """
    SELECT p.id, p.nome, COALESCE(p.estoque_minimo, 0), 
        COALESCE((SELECT quantidade FROM estoque_setores WHERE produto = p.nome AND setor = 'ALMOXARIFADO'), 0) as qtd,
        (SELECT MAX(data_hora) FROM (
            SELECT data_hora FROM entradas_unidade WHERE produto_id = p.id 
            UNION ALL 
            SELECT data_hora FROM saídas WHERE produto_id = p.id
        )) as ultima_mov
    FROM produtos p
    WHERE p.ativo = 1
    ORDER BY ultima_mov DESC, p.id DESC -- Garante o padrão no nível do Banco de Dados
    """
    dados = q(sql_base, fetch=True)

    lista_f = []
    for pid, nome, pmin, qreal, u_mov in dados:
        if (busca and busca.upper() not in nome): continue
        if (f_pos and qreal <= 0): continue
        lista_f.append({
            "id": pid, "nome": nome, "min": pmin, "qtd": qreal, 
            "baixo": qreal <= pmin and pmin > 0,
            "data": u_mov if u_mov else "2000-01-01 00:00:00"
        })

    if ordem == "Mais recentes primeiro":
        # Ordena pela data de movimentação e usa o ID como critério de desempate (mais novos primeiro)
        lista_f = sorted(lista_f, key=lambda x: (x["data"], x["id"]), reverse=True)
    elif ordem == "Itens com alerta ativo":
        lista_f = sorted(lista_f, key=lambda x: (not x["baixo"], x["qtd"]))
    elif ordem == "Nome A-Z":
        lista_f = sorted(lista_f, key=lambda x: x["nome"])
    elif ordem == "Nome Z-A":
        lista_f = sorted(lista_f, key=lambda x: x["nome"], reverse=True)
    elif ordem == "Estoque baixo primeiro":
        lista_f = sorted(lista_f, key=lambda x: x["qtd"])
    elif ordem == "Estoque alto primeiro":
        lista_f = sorted(lista_f, key=lambda x: x["qtd"], reverse=True)

    if lista_f:
        buffer_est = io.BytesIO()
        df_export_est = pd.DataFrame(lista_f)[["nome", "qtd", "min"]]
        df_export_est.columns = ["Produto", "Quantidade Atual", "Mínimo Alerta"]
        with pd.ExcelWriter(buffer_est, engine='xlsxwriter') as writer:
            df_export_est.to_excel(writer, index=False, sheet_name='Saldo')
        st.download_button(
            label="📥 Exportar Saldo Filtrado para Excel",
            data=buffer_est.getvalue(),
            file_name=f"saldo_estoque_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_export_est_vfinal",
            use_container_width=True
        )

    itens_pg = 20
    total_pg = (len(lista_f) // itens_pg) + (1 if len(lista_f) % itens_pg > 0 else 0)
    pg_at = st.number_input(f"Página (de {total_pg})", min_value=1, max_value=max(1, total_pg), value=1, key="nav_est") if total_pg > 1 else 1

    # --- EXIBIÇÃO DOS EXPANDERS ---
    for item in lista_f[(pg_at-1)*itens_pg : pg_at*itens_pg]:
        # Busca a embalagem definida para este produto
        emb_txt = q("SELECT embalagem_padrao FROM produtos WHERE id=?", (item['id'],), True)[0][0]
        
        # Formata o label conforme solicitado
        label = f"{'⚠️' if item['baixo'] else '📦'} {item['nome']} — {int(item['qtd'])} {emb_txt}"
        if item['baixo']: label += f" (Mínimo: {item['min']})"

        with st.expander(label):
            c_label, c_input_min, c_emb, c_btn = st.columns([1.2, 0.8, 1, 1], vertical_alignment="center")
            
            c_label.markdown("<div style='font-size: 13px; color: gray;'>Configurações:</div>", unsafe_allow_html=True)
            
            # Estoque Mínimo
            novo_m = c_input_min.number_input("Mín", min_value=0, value=int(item['min']), key=f"m_{item['id']}", help="Estoque Mínimo")
            
            # Dropdown de Embalagens
            embs_disponiveis = ["un"] + [e[0].lower() for e in q("SELECT nome FROM embalagens ORDER BY nome", fetch=True)]
            emb_atual = q("SELECT embalagem_padrao FROM produtos WHERE id=?", (item['id'],), True)[0][0]
            if emb_atual not in embs_disponiveis: embs_disponiveis.append(emb_atual)
            
            nova_emb = c_emb.selectbox("Embalagem", options=embs_disponiveis, index=embs_disponiveis.index(emb_atual), key=f"emb_p_{item['id']}")
            
            if c_btn.button("Salvar", key=f"b_{item['id']}", use_container_width=True):
                q("UPDATE produtos SET estoque_minimo = ?, embalagem_padrao = ? WHERE id = ?", (novo_m, nova_emb, item['id']))
                st.success("Salvo!")
                time.sleep(0.5); st.rerun()

            # --- FUNCIONALIDADE SOFT DELETE (ADMIN) COM CONFIRMAÇÃO ---
            if is_admin():
                st.divider()
                c_txt_del, c_chk_del, c_btn_del = st.columns([2, 1, 1], vertical_alignment="center")
                
                c_txt_del.write("⚠️ **Excluir Produto?**")
                # Checkbox serve como trava de segurança
                confirmar = c_chk_del.checkbox("Confirmar", key=f"chk_del_{item['id']}")
                
                if confirmar:
                    if c_btn_del.button("Confirmar", key=f"btn_del_{item['id']}", use_container_width=True, type="primary"):
                        # 1. Executa Soft Delete
                        q("UPDATE produtos SET ativo = 0 WHERE id = ?", (item['id'],))
                        # 2. Registra Log
                        q("INSERT INTO logs_admin (operador, acao, detalhe) VALUES (?,?,?)", 
                          (st.session_state.usuario, "EXCLUSAO PRODUTO", f"O admin excluiu o item: {item['nome']} (ID: {item['id']})"))
                        st.error("Item excluído!")
                        time.sleep(0.8)
                        st.rerun()
                else:
                    c_btn_del.button("Excluir", key=f"btn_dummy_{item['id']}", use_container_width=True, disabled=True)

            st.divider()
            ultimas = q("""
                SELECT * FROM (
                    SELECT datetime(data_hora, '-3 hours'), usuario, 'ENTRADA' as t, quantidade, tipo_movimentacao as obs, '' as resp 
                    FROM entradas_unidade WHERE produto_id = ? 
                    UNION ALL 
                    SELECT datetime(data_hora, '-3 hours'), usuario, 'SAÍDA' as t, -quantidade, observacao as obs, responsavel as resp 
                    FROM saídas WHERE produto_id = ?
                ) ORDER BY 1 DESC LIMIT 3
            """, (item['id'], item['id']), fetch=True)
            
            for d, u, t, qm, obs, resp in ultimas:
                cor = "green" if t == "ENTRADA" else "red"
                obs_l = obs.split("AJUSTE ADMIN: ")[-1] if "AJUSTE ADMIN" in obs else obs
                if obs_l.startswith("PARA:") or obs_l.startswith("ENTRADA:") or not obs_l.strip(): 
                    obs_l = "---"
                
                st.write(f"""
                    <div style="font-size: 11px; margin-bottom: 2px;">
                        {pd.to_datetime(d).strftime('%d/%m %H:%M')} | 
                        {u} | 
                        <b style="color:{cor}">{t}</b> | 
                        <b>{qm} un</b> | 
                        {resp.upper() if resp else '---'} | 
                        <i>{obs_l}</i>
                    </div>
                """, unsafe_allow_html=True)

# ==========================================================
# 4. ABA AUDITORIA
# ==========================================================
elif aba_principal == "📜 Auditoria":
    st.title("📜 Histórico de Movimentações")
    
    with st.expander("🔍 Filtros de Relatório", expanded=True):
        c1, c2, c3 = st.columns(3); c4, c5, c6 = st.columns(3); c7, _, _ = st.columns(3)
        hoje = date.today()
        d_ini = c1.date_input("Início", hoje - timedelta(days=30), format="DD/MM/YYYY")
        d_fim = c2.date_input("Fim", hoje, format="DD/MM/YYYY")
        f_set = c3.selectbox("Setor", ["Todos"] + LISTA_SETORES)
        
        l_res = q("SELECT DISTINCT UPPER(responsavel) FROM saídas WHERE responsavel IS NOT NULL", fetch=True)
        f_res = c4.selectbox("Colaborador/Responsável", ["Todos"] + [r[0] for r in l_res if r[0]])
        
        f_usr = c5.selectbox("Operador do Sistema", ["Todos"] + [u[0] for u in q("SELECT username FROM usuarios", fetch=True)])
        f_tip = c6.selectbox("Tipo de Movimentação", ["Todos", "ENTRADA", "SAÍDA"])
        
        # AGORA APENAS UM CAMPO: Filtra apenas ativos para o preenchimento rápido
        prods_aud = [p[0] for p in q("SELECT nome FROM produtos WHERE ativo = 1 ORDER BY nome", fetch=True)]
        f_prod = c7.selectbox("Produto", ["Todos"] + prods_aud, key="f_prod_aud_unica")
        
        apenas_com_obs = st.checkbox("Exibir apenas itens com Comentários/Ajustes")

    # SQL Dinâmica atualizada para incluir data_hora_saida
    sql = """
        SELECT * FROM (
            SELECT 
                datetime(e.data_hora, '-3 hours') as Data, e.usuario as Operador, p.nome as Item, 
                'ENTRADA' as Tipo, e.quantidade as Qtd, 
                CASE 
                    WHEN e.tipo_movimentacao LIKE 'PARA: %' THEN REPLACE(SUBSTR(e.tipo_movimentacao, 1, INSTR(e.tipo_movimentacao || ' |', ' |') - 1), 'PARA: ', '')
                    ELSE 'ALMOXARIFADO' 
                END as Setor,
                CASE 
                    WHEN e.tipo_movimentacao LIKE '%RESP: %' THEN REPLACE(SUBSTR(e.tipo_movimentacao, INSTR(e.tipo_movimentacao, 'RESP: ') + 6, INSTR(SUBSTR(e.tipo_movimentacao, INSTR(e.tipo_movimentacao, 'RESP: ') + 6), ' |') - 1), 'RESP: ', '')
                    ELSE UPPER(e.usuario) 
                END as Responsavel,
                e.tipo_movimentacao as Obs, e.id as mid, p.id as pid,
                '-' as DataSaidaReal -- Valor fixo para Entradas
            FROM entradas_unidade e JOIN produtos p ON e.produto_id = p.id 
            UNION ALL 
            SELECT 
                datetime(s.data_hora, '-3 hours') as Data, s.usuario as Operador, p.nome as Item, 
                'SAÍDA' as Tipo, -s.quantidade as Qtd, 
                CASE 
                    WHEN s.observacao LIKE 'PARA: %' THEN REPLACE(SUBSTR(s.observacao, 1, INSTR(s.observacao || ' |', ' |') - 1), 'PARA: ', '')
                    ELSE '---'
                END as Setor,
                UPPER(COALESCE(NULLIF(s.responsavel, ''), s.usuario)) as Responsavel, s.observacao as Obs, s.id as mid, p.id as pid,
                datetime(s.data_hora_saida) as DataSaidaReal -- Valor da nova coluna
            FROM saídas s JOIN produtos p ON s.produto_id = p.id
        ) WHERE DATE(Data) BETWEEN ? AND ?
    """
    params = [d_ini.isoformat(), d_fim.isoformat()]
    
    if f_set != "Todos": sql += " AND Setor = ?"; params.append(f_set)
    if f_res != "Todos": sql += " AND Responsavel = ?"; params.append(f_res)
    if f_usr != "Todos": sql += " AND Operador = ?"; params.append(f_usr)
    if f_tip != "Todos": sql += " AND Tipo = ?"; params.append(f_tip)
    if f_prod != "Todos": sql += " AND Item = ?"; params.append(f_prod) 
    
    if apenas_com_obs:
        sql += """ AND (
            Obs LIKE '%AJUSTE ADMIN:%' 
            OR (Obs != '' AND Obs != '---' AND Obs NOT LIKE 'PARA: %' AND Obs NOT LIKE 'ENTRADA:%')
        )"""

    res_aud = q(sql + " ORDER BY Data DESC", params, fetch=True)
    
    if res_aud:
        buffer = io.BytesIO()
        df_export = pd.DataFrame(res_aud, columns=["Data", "Operador", "Item", "Tipo", "Qtd", "Setor", "Responsavel", "Obs", "MID", "PID", "Data Saída Real"])
        df_export['Data Saída Real'] = pd.to_datetime(df_export['Data Saída Real'], errors='coerce').dt.strftime('%d/%m/%Y %H:%M').fillna('-')
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Auditoria')
            
        st.download_button(
            label="📥 Exportar Relatório para Excel",
            data=buffer.getvalue(),
            file_name=f"relatorio_estoque_{hoje.strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_export_excel_aud"
        )

        itens_pg = 15
        total_pg = (len(res_aud) // itens_pg) + (1 if len(res_aud) % itens_pg > 0 else 0)
        c_pag_h, c_info_h = st.columns([1, 4])
        pg_aud = c_pag_h.number_input(f"Página (de {total_pg})", min_value=1, max_value=max(1, total_pg), value=1, key="nav_h_final")
        
        st.markdown("""
            <div style="display: flex; font-weight: bold; border-bottom: 2px solid #ccc; padding-bottom: 5px; margin-bottom: 10px; font-size: 13px;">
                <div style="flex: 0.7;">Data Movim.</div>
                <div style="flex: 0.7;">Data Saída</div>
                <div style="flex: 0.8;">Operador</div>
                <div style="flex: 1.5;">Produto</div>
                <div style="flex: 0.6;">Tipo</div>
                <div style="flex: 0.4;">Qtd</div>
                <div style="flex: 1.1;">Setor</div>
                <div style="flex: 1.2;">Responsável</div>
                <div style="flex: 3.5;">Obs.</div> <div style="flex: 0.2;"></div>
            </div>
        """, unsafe_allow_html=True)

        idx_ini = (pg_aud - 1) * itens_pg
        for r_data, r_oper, r_item, r_tipo, r_qtd, r_setor, r_resp, r_obs, r_mid, r_pid, r_dt_saida in res_aud[idx_ini : idx_ini + itens_pg]:
            col_dados, col_edit = st.columns([0.97, 0.03])

            if r_dt_saida is None or r_dt_saida == '-':
                dt_saida_formatada = '-'
            else:
                try:
                    dt_saida_formatada = pd.to_datetime(r_dt_saida).strftime('%d/%m %H:%M')
                except:
                    dt_saida_formatada = '-'
            
            # Busca a embalagem atual do produto para exibir no histórico
            res_emb = q("SELECT embalagem_padrao FROM produtos WHERE id=?", (r_pid,), True)
            emb_aud = res_emb[0][0] if res_emb else "un"
            
            if "AJUSTE ADMIN:" in r_obs:
                obs_exibicao = r_obs.split("AJUSTE ADMIN: ")[-1].strip()
            elif r_obs.startswith("PARA:") or r_obs.startswith("ENTRADA:") or not r_obs.strip():
                obs_exibicao = "---"
            else:
                obs_exibicao = r_obs

            setor_limpo = r_setor.split("|")[0].strip()
            cor_obs = "#DAA520" if "AJUSTE ADMIN:" in r_obs else "#444"

            col_dados.markdown(f"""
                <div style="display: flex; font-size: 11px; border-bottom: 1px solid #eee; padding: 5px 0; align-items: center;">
                    <div style="flex: 0.7;">{pd.to_datetime(r_data).strftime('%d/%m %H:%M')}</div>
                    <div style="flex: 0.7; color: #4169E1;">{dt_saida_formatada}</div>
                    <div style="flex: 0.8;">{r_oper}</div>
                    <div style="flex: 1.5;"><b>{r_item}</b></div>
                    <div style="flex: 0.6; color: {'green' if r_tipo == 'ENTRADA' else 'red'};">{r_tipo}</div>
                    <div style="flex: 0.4;"><b>{abs(int(r_qtd))} {emb_aud}</b></div>
                    <div style="flex: 1.1;">{setor_limpo}</div>
                    <div style="flex: 1.2;">{r_resp}</div>
                    <div style="flex: 3.5; color: {cor_obs}; font-style: italic; font-weight: bold;">{obs_exibicao}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if is_admin() and col_edit.button("📝", key=f"btn_aud_{r_tipo}_{r_mid}"):
                st.session_state[f"form_ed_{r_tipo}_{r_mid}"] = True
            
            if st.session_state.get(f"form_ed_{r_tipo}_{r_mid}"):
                with st.form(f"f_aj_final_{r_tipo}_{r_mid}"):
                    st.markdown(f"### 🔧 Ajuste de Registro: {r_item}")
                    
                    # Campo para alterar o nome do item
                    new_nome = st.text_input("Nome do Item", value=r_item).upper()
                    
                    c1, c2 = st.columns(2)
                    new_q = c1.number_input("Qtd Correta", value=abs(r_qtd), min_value=0)
                    new_s = c2.selectbox("Setor Correto", LISTA_SETORES, index=LISTA_SETORES.index(setor_limpo) if setor_limpo in LISTA_SETORES else 0)
                    
                    new_r = st.text_input("Responsável Correto", value=r_resp).upper()
                    motivo = st.text_input("Motivo da Alteração (Obrigatório)", key=f"mot_{r_tipo}_{r_mid}")
                    
                    # Colunas para os botões de ação
                    c_conf, c_canc = st.columns(2)
                    
                    # BOTÃO CONFIRMAR
                    if c_conf.form_submit_button("Confirmar Alteração", use_container_width=True):
                        if not motivo: 
                            st.error("⚠️ Motivo obrigatório!")
                        else:
                            mudancas = []
                            if new_nome != r_item:
                                mudancas.append(f"Nome: {r_item} > {new_nome}")
                                q("UPDATE produtos SET nome = ? WHERE id = ?", (new_nome, r_pid))
                                q("UPDATE estoque_setores SET produto = ? WHERE produto = ?", (new_nome, r_item))
                            
                            if new_s != setor_limpo: mudancas.append(f"Setor: {setor_limpo} > {new_s}")
                            if new_r != r_resp: mudancas.append(f"Resp: {r_resp} > {new_r}")
                            if new_q != abs(r_qtd): mudancas.append(f"Qtd: {abs(r_qtd)} > {new_q}")

                            txt_m = " | ".join(mudancas)
                            rastro = f"AJUSTE ADMIN: [{r_tipo}] {new_nome} | {txt_m} | Motivo: {motivo}"
                            nova_obs_db = f"PARA: {new_s} | RESP: {new_r} | {rastro}"

                            if r_tipo == 'SAÍDA':
                                q("UPDATE saídas SET responsavel=?, observacao=?, quantidade=? WHERE id=?", 
                                  (new_r, nova_obs_db, new_q, r_mid))
                            else:
                                q("UPDATE entradas_unidade SET tipo_movimentacao=?, quantidade=? WHERE id=?", 
                                  (nova_obs_db, new_q, r_mid))

                            # Registro no log de admin
                            q("INSERT INTO logs_admin (operador, acao, detalhe) VALUES (?,?,?)", 
                              (st.session_state.usuario, "AJUSTE AUDITORIA", rastro))

                            # Ajuste de estoque
                            diff = new_q - abs(r_qtd)
                            if diff != 0:
                                val = diff if r_tipo == 'ENTRADA' else -diff
                                q("UPDATE estoque_setores SET quantidade = quantidade + ? WHERE produto=? AND setor='ALMOXARIFADO'", (val, new_nome))
                            
                            st.success("Alterações aplicadas!")
                            # Limpa os campos fechando o formulário
                            st.session_state[f"form_ed_{r_tipo}_{r_mid}"] = False
                            time.sleep(0.5)
                            st.rerun()

                    # BOTÃO CANCELAR (Restaurado)
                    if c_canc.form_submit_button("Cancelar", use_container_width=True):
                        st.session_state[f"form_ed_{r_tipo}_{r_mid}"] = False
                        st.rerun()

    if is_admin():
        st.divider()
        with st.expander("🛡️ Detalhes de Ajustes Administrativos", expanded=True):
            busca_l = st.text_input("🔍 Pesquisar nos logs", key="f_l_final")
            l_adm_r = q("SELECT datetime(data_hora, '-3 hours'), operador, acao, detalhe FROM logs_admin ORDER BY data_hora DESC", fetch=True)
            if l_adm_r:
                l_adm_f = [r for r in l_adm_r if not busca_l or (busca_l.upper() in r[1].upper() or busca_l.upper() in r[3].upper())]
                if l_adm_f:
                    itens_l = 8
                    total_pg_l = (len(l_adm_f) // itens_l) + (1 if len(l_adm_f) % itens_l > 0 else 0)
                    c_pg_l, _ = st.columns([1, 4])
                    pg_l = c_pg_l.number_input(f"Página Log", min_value=1, max_value=max(1, total_pg_l), value=1, key="nav_l_final")
                    st.table(pd.DataFrame(l_adm_f[(pg_l-1)*itens_l : pg_l*itens_l], columns=["Data/Hora", "Admin", "Ação", "Histórico"]))