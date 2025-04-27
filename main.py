# =========================
# main.py – Alocação Ótima de Times
# =========================
from __future__ import annotations
from typing import List
import altair as alt
import pandas as pd

import streamlit as st

# --- back-end modules ---
from cadastro_times_sinergias import CadastroTimesSinergias, Time
from configuracao_modelo_restricoes import ConfiguracaoModelo
from execucao_modelo import ExecucaoModelo
from preferencias_dias import (
    CadastroPreferenciasDias,
    PreferenciaDia,
    DIAS_UTEIS,
)
from visualizacao_resultados import VisualizacaoResultados
from layout_configuration import LayoutConfiguration

st.set_page_config(page_title="Alocação Ótima de Times", layout="wide")

# ------------------------------------------------------------------
# 0. DEFINIÇÕES GERAIS
# ------------------------------------------------------------------
PAGES = [
    "1 - Layout",
    "2 - Times & Sinergias",
    "3 - Preferências",
    "4 - Configuração",
    "5 - Execução",
    "6 - Visualização",
]

DEFAULTS = dict(
    # --- widgets básicos ---
    page_idx=0,
    num_corridors=1,
    positions_per_table=4,
    tables_per_corridor=[1],
    num_teams=1,
    funcao_objetivo="max_ocupacao_media",
    peso_sin=1.0,
    peso_pref=0.8,
    peso_dist=10.0,
    limite_sobrealocacao=0,
    folga_minima=5,
    dias_range=[2, 3],
    # --- buffers auxiliares ---
    _times_buf=[],
    # --- objetos de negócio ---
    layout_config=None,
    cadastro_times=None,
    cadastro_preferencias=None,
    configuracao_modelo=None,
    resultados=None,
)
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def goto(idx: int):
    st.session_state.page_idx = max(0, min(len(PAGES) - 1, idx))


# ------------------------------------------------------------------
# 0.1. CABEÇALHO DE NAVEGAÇÃO
# ------------------------------------------------------------------
st.markdown("### 📑 Fluxo da aplicação")
cols_tl = st.columns(len(PAGES), vertical_alignment="center")
for i, (c, name) in enumerate(zip(cols_tl, PAGES)):
    style = "✅" if i < st.session_state.page_idx else ("➡️" if i == st.session_state.page_idx else "▫️")
    if c.button(f"{style} {name}", key=f"tl_{i}"):
        goto(i)

col_prev, *_, col_next = st.columns(len(PAGES), vertical_alignment="center")
if col_prev.button("« Página anterior", disabled=st.session_state.page_idx == 0):
    goto(st.session_state.page_idx - 1)
if col_next.button("Próxima página »", disabled=st.session_state.page_idx == len(PAGES) - 1):
    goto(st.session_state.page_idx + 1)

# ------------------------------------------------------------------
# 0.2. SIDEBAR
# ------------------------------------------------------------------
st.sidebar.radio(
    "Menu rápido",
    PAGES,
    index=st.session_state.page_idx,
    key="sidebar_radio",
    on_change=lambda: goto(PAGES.index(st.session_state.sidebar_radio)),
)

# ------------------------------------------------------------------
# 0.3. PÁGINAS
# ------------------------------------------------------------------
page = PAGES[st.session_state.page_idx]

if page.startswith("1"):
    st.header("🗺️ Configuração Inicial do Layout")

    # -------- Sincroniza defaults a partir do objeto salvo ---------
    if st.session_state.layout_config and not st.session_state.get("_layout_loaded"):
        cfg = st.session_state.layout_config
        st.session_state.num_corridors = cfg.num_corridors
        st.session_state.positions_per_table = cfg.positions_per_table
        st.session_state.tables_per_corridor = cfg.tables_per_corridor.copy()
        st.session_state._layout_loaded = True  # flag interna

    # ----------- widgets principais -------------------------------
    num_corridors = st.number_input(
        label="Quantidade de corredores",
        min_value=1,
        step=1,
        key="num_corridors",
        help="Número de corredores no piso; cada corredor receberá as mesas indicadas abaixo."
    )

    # ajusta comprimento da lista de mesas antes dos widgets dinâmicos
    tp = st.session_state.tables_per_corridor
    if len(tp) < num_corridors:
        tp.extend([1] * (num_corridors - len(tp)))
    elif len(tp) > num_corridors:
        st.session_state.tables_per_corridor = tp[:num_corridors]
        tp = st.session_state.tables_per_corridor

    tables_per_corridor: List[int] = []
    for c in range(num_corridors):
        val = st.number_input(
            label=f"Mesas no Corredor {c + 1}",
            min_value=1,
            step=1,
            key=f"tbl_{c}",
            value=tp[c],
            help="Quantas mesas esse corredor deve ter."
        )
        tables_per_corridor.append(int(val))
        st.session_state.tables_per_corridor[c] = int(val)

    positions_per_table = st.number_input(
        label="Posições por mesa",
        min_value=2,
        step=2,
        key="positions_per_table",
        value=2,
        help="Número de assentos por mesa (deve ser par para manter duas fileiras no preview)."
    )

    try:
        tmp_cfg = LayoutConfiguration(
            num_corridors=num_corridors,
            tables_per_corridor=tables_per_corridor,
            positions_per_table=positions_per_table,
        )
        st.subheader("Preview do Layout (ASCII)")
        st.code(tmp_cfg.render_ascii())
    except ValueError:
        st.info("Defina parâmetros válidos para ver o preview.")

    if st.button("Salvar Layout"):
        try:
            st.session_state.layout_config = tmp_cfg
            st.success("Layout salvo!")
            st.json(tmp_cfg.generate_layout_preview())
        except ValueError as e:
            st.error(e)

# ---------- P2 – Times & Sinergias ----------
elif page.startswith("2"):
    st.header("👥 Cadastro de Times e Sinergias")

    # main.py – dentro de `elif page.startswith("2"):`, antes de tudo
    if not st.session_state.layout_config:
        st.warning("⚠️ Salve primeiro o layout na etapa 1 para definir a capacidade de assentos.")
        st.stop()

    # obtém o objeto de layout salvo
    cfg = st.session_state.layout_config

    # capacidade total de assentos = (mesas totais) × (posições por mesa)
    max_seats = sum(cfg.tables_per_corridor) * cfg.positions_per_table

    st.info(f"🪑 Capacidade total de assentos: **{max_seats}** pessoas por dia.")

    if st.session_state.cadastro_times and not st.session_state.get("_times_loaded"):
        st.session_state.num_teams = len(st.session_state.cadastro_times.times)
        st.session_state._times_loaded = True
        # itera sobre os objetos Time, não sobre strings
        st.session_state._times_buf = [
            {"nome": time_obj.nome, "integrantes": time_obj.qtde_integrantes}
            for time_obj in st.session_state.cadastro_times.times.values()
        ]

    num_teams = st.number_input(
        "Número de times",
        1,
        step=1,
        key="num_teams",
    )

    # ----- buffer dinâmico -----
    buf: list[dict] = st.session_state._times_buf
    while len(buf) < num_teams:
        buf.append({"nome": "", "integrantes": 1})
    while len(buf) > num_teams:
        buf.pop()

    for idx in range(num_teams):
        with st.expander(f"Time {idx + 1}", expanded=True):
            c1, c2 = st.columns(2)
            buf[idx]["nome"] = c1.text_input(
                "Nome do time",
                key=f"nome_{idx}",
                value=buf[idx]["nome"],
            )
            buf[idx]["integrantes"] = int(
                c2.number_input(
                    "Integrantes",
                    1,
                    step=1,
                    key=f"int_{idx}",
                    value=buf[idx]["integrantes"],
                )
            )

    if st.button("Salvar Times"):
        try:
            cadastro = CadastroTimesSinergias()
            for t in buf:
                cadastro.adicionar_time(Time(t["nome"], t["integrantes"], []))
            st.session_state.cadastro_times = cadastro
            st.success("✅ Times cadastrados! Agora defina as sinergias.")
        except ValueError as e:
            st.error(e)

    # ---------- matriz de sinergia ----------
    if st.session_state.cadastro_times:
        cadastro: CadastroTimesSinergias = st.session_state.cadastro_times
        teams = cadastro.listar_times()
        st.subheader("Matriz de Sinergia")

        sinergia_mat = {
            (a, b): b in cadastro.times[a].sinergias
            for i, a in enumerate(teams)
            for b in teams[i + 1 :]
        }

        for i, a in enumerate(teams):
            # calcula colunas restantes e só procede se > 0
            n_cols = len(teams) - i - 1
            if n_cols <= 0:
                break
            cols = st.columns(n_cols)
            for j, b in enumerate(teams[i + 1 :]):
                sinergia_mat[(a, b)] = cols[j].checkbox(
                    f"{a} ↔ {b}",
                    value=sinergia_mat[(a, b)],
                    key=f"sin_{a}_{b}",
                )

        if st.button("Salvar Sinergias"):
            for t in teams:
                cadastro.times[t].sinergias.clear()
            for (a, b), v in sinergia_mat.items():
                if v:
                    cadastro.add_sinergia(a, b)
            st.success("Sinergias salvas!")

# ---------- P3 – Preferências ----------
elif page.startswith("3"):
    st.header("📅 Preferências de Dias")
    if not st.session_state.cadastro_times:
        st.warning("Cadastre os times primeiro.")
    else:
        cadastro_pref = CadastroPreferenciasDias()

        for t in st.session_state.cadastro_times.listar_times():
            pref_ant = (
                st.session_state.cadastro_preferencias.preferencias.get(t)
                if st.session_state.cadastro_preferencias
                else None
            )
            with st.expander(t):
                col1, col2, col3 = st.columns(3)
                dias_sel = col1.multiselect(
                    "Dias preferenciais",
                    DIAS_UTEIS,
                    default=[
                        d for d, v in pref_ant.dias_preferenciais.items() if v
                    ]
                    if pref_ant
                    else [],
                    key=f"dias_{t}",
                    help="Selecione os dias da semana em que este time prefere estar presente."
                )
                obrig = col2.slider(
                    "Dias obrigatórios",
                    0,
                    len(DIAS_UTEIS),
                    value=pref_ant.dias_obrigatorios if pref_ant else 2,
                    key=f"obrig_{t}",
                    help="Defina o número mínimo de dias em que este time deve obrigatoriamente comparecer."
                )
                peso = col3.number_input(
                    "Peso",
                    0.0,
                    step=0.1,
                    value=pref_ant.peso if pref_ant else 1.0,
                    key=f"peso_{t}",
                    help="Ajuste a importância (peso) desta preferência ao otimizar o modelo."
                )
                cadastro_pref.adicionar_preferencia(
                    PreferenciaDia(
                        nome=t,
                        dias_preferenciais={d: d in dias_sel for d in DIAS_UTEIS},
                        dias_obrigatorios=obrig,
                        peso=peso,
                    )
                )

        if st.button("Salvar Preferências", help="Clique para validar e salvar todas as preferências definidas."):
            try:
                cadastro_pref.validar_preferencias()
                st.session_state.cadastro_preferencias = cadastro_pref
                st.success("Preferências salvas!")
            except ValueError as e:
                st.error(e)

# ---------- P4 – Configuração ----------
elif page.startswith("4"):
    st.header("⚙️ Configuração do Modelo e Restrições")

    # ——— Função objetivo ———
    funcao_objetivo = st.selectbox(
        label="Função objetivo",
        options=("max_ocupacao_media", "max_satisfacao", "min_desalocacao"),
        index=0,  # padrão: maximizar ocupação média
        help="Define o critério que o modelo vai otimizar: \
             ocupação, satisfação geral ou minimizar realocações."
    )

    # ——— Pesos das restrições ———
    c1, c2, c3 = st.columns(3)
    peso_sin = c1.number_input(
        label="Peso sinergia",
        min_value=0.0,
        step=0.1,
        value=1.0,
        help="Quanto penalizar quando times sem sinergia fiquem próximos."
    )
    peso_pref = c2.number_input(
        label="Peso preferência",
        min_value=0.0,
        step=0.1,
        value=1.0,
        help="Força de atender aos dias que cada time prefere."
    )
    peso_dist = c3.number_input(
        label="Peso distância",
        min_value=0.0,
        step=0.5,
        value=10.0,
        help="Penalidade para dividir um time em mesas muito distantes."
    )

    # ——— Limites numéricos ———
    limite_sobrealocacao = st.number_input(
        label="Limite global de sobrealocação",
        min_value=0,
        max_value=100,
        step=1,
        value=0,
        help="Máximo de pessoas realocadas além das preferências (por semana)."
    )
    folga_minima = st.number_input(
        label="Folga mínima de cadeiras por dia",
        min_value=0,
        max_value=10,
        step=1,
        value=2,
        help="Número mínimo de assentos vazios que devem sobrar diariamente."
    )

    # ——— Cenários de dias obrigatórios ———
    dias_range = st.multiselect(
        label="Dias presenciais obrigatórios (cenários)",
        options=[1, 2, 3, 4, 5],
        default=[2, 3],
        help="Para análise de sensibilidade: testa-se cada valor desta lista."
    )

    # ——— Ação de salvar ———
    if st.button("Salvar configuração"):
        try:
            cfg = ConfiguracaoModelo(
                funcao_objetivo=funcao_objetivo,
                pesos_restricoes={
                    "sinergia": peso_sin,
                    "preferencia": peso_pref,
                    "distancia": peso_dist,
                },
                limite_sobrealocacao=limite_sobrealocacao,
                folga_minima=folga_minima,
                peso_distancia=peso_dist,
                dias_obrigatorios_range=dias_range,
            )
            st.session_state.configuracao_modelo = cfg
            st.success("✅ Configuração salva com sucesso!")
            st.code(cfg.resumo_configuracao())
        except ValueError as e:
            st.error(f"❌ {e}")

# ---------- P5 – Execução ----------
elif page.startswith("5"):
    st.header("🚀 Execução do Modelo")
    requisitos = (
        st.session_state.layout_config,
        st.session_state.cadastro_times,
        st.session_state.cadastro_preferencias,
        st.session_state.configuracao_modelo,
    )
    if not all(requisitos):
        st.warning("Conclua as etapas 1-4 antes de executar o modelo.")
    else:
        if st.button("Executar Otimização"):
            try:
                executor = ExecucaoModelo(
                    st.session_state.layout_config,
                    st.session_state.cadastro_times,
                    st.session_state.cadastro_preferencias,
                    st.session_state.configuracao_modelo,
                )
                st.session_state.resultados = executor.executar()
                st.success("Modelo resolvido!")

                # ————— aviso de cenários inviáveis —————
                inviaveis = st.session_state.resultados.get("inviaveis", {})
                if inviaveis:
                    descricoes = [
                        f"{k} dias ({status})"
                        for k, status in inviaveis.items()
                    ]
                    msg = "Cenários sem solução viável: " + ", ".join(descricoes)
                    st.warning(msg)

            except Exception as e:
                st.error(f"Erro na execução: {e}")

        # mostra o JSON de resultados (incluindo cenários válidos e inviáveis)
        if st.session_state.get("resultados"):
            st.json(st.session_state.resultados)

# ---------- P6 – Visualização ----------
else:
    st.header("📊 Visualização dos Resultados")
    if not st.session_state.resultados:
        st.warning("Execute o modelo primeiro.")
    else:
        visual = VisualizacaoResultados(st.session_state.resultados)
        cen_opts = visual.cenarios_disponiveis()
        k_sel = st.selectbox("Cenário (dias obrigatórios)", cen_opts, index=0)

        ind = visual.indicadores_cenario(k_sel)

        # calcula folga mínima em %
        cfg = st.session_state.configuracao_modelo
        layout = st.session_state.layout_config
        cap_total = sum(layout.tables_per_corridor) * layout.positions_per_table
        folga_perc = (1 - cfg.folga_minima / cap_total) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Taxa de Ocupação Semanal", ind["taxa"])
        c2.metric("Capacidade Osciosa",     ind["folga"])
        c3.metric("Ocupação Desejada", f"{folga_perc:.1f} %", help="Calculado baseando-se na folga.")
        c4.metric("Tempo de Processamento",     ind["t"])

        df_cnt, df_det = visual.tabela_semana(k_sel)
        st.subheader("Ocupação por Mesa × Dia (nº de pessoas)")
        st.dataframe(df_cnt, use_container_width=True)

        with st.expander("Distribuição dos times por Mesa/Dia"):
            st.dataframe(df_det, use_container_width=True)

        rep = visual.relatorio_sensibilidade(k_sel)
        if rep:
            with st.expander("Relatório de Sensibilidade (detalhado)"):
                st.subheader("Valor ótimo")
                st.dataframe(rep["objetivo"])
                st.subheader("Variáveis (valor & Reduced Cost)")
                st.dataframe(rep["variaveis"], use_container_width=True)
                st.caption(
                    "• **Alocado** = 1 indica que o time ocupou o assento naquele dia.\n"
                    "• **Custo Reduzido** mostra o quanto o valor da função-objetivo mudaria "
                    "se incluíssemos a variável à base.\n"
                )
                st.subheader("Restrições (Shadow Price & Slack)")
                st.dataframe(rep["restricoes"], use_container_width=True)
                st.caption(
                    "• **Preço-Sombra** é a variação marginal na função-objetivo por "
                    "unidade de folga/rigidez da restrição.\n"
                    "• **Slack** mostra quanto resta até atingir o limite da restrição."
                )



        # Sensibilidade global
        df_sens = visual.sensibilidade_df()
        if not df_sens.empty:
            st.subheader("Sensibilidade global")
            st.dataframe(df_sens, use_container_width=True)

            # — prepara dados para o gráfico de barras + linha —
            # df_sens já tem colunas: Dias_obrig, taxa_semanal, ocup_total, etc.
            df_plot = df_sens.copy()
            df_plot["Taxa (%)"] = df_plot["taxa_semanal"] * 100




            # cria DataFrame longo com duas séries: Taxa Semanal e Folga Mínima
            df_long = pd.DataFrame({
                "Dias_obrig": list(df_plot["Dias_obrig"]) * 2,
                "Percentual": list(df_plot["Taxa (%)"]) + [folga_perc] * len(df_plot),
                "Métrica":    ["Taxa Semanal"] * len(df_plot)
                              + ["Folga Mínima"] * len(df_plot),
            })

            # gráfico de barras para Taxa Semanal
            bars = (
                alt.Chart(df_long[df_long["Métrica"] == "Taxa Semanal"])
                .mark_bar()
                .encode(
                    x=alt.X(
                        "Dias_obrig:O",
                        title="Dias Obrigatórios",
                        axis=alt.Axis(labelAngle=0)
                    ),
                    y=alt.Y(
                        "Percentual:Q",
                        title="Percentual (%)",
                        scale=alt.Scale(domain=[0, 105])
                    ),
                    color=alt.Color("Métrica:N", title="Legenda")
                )
            )

            # linha tracejada para Folga Mínima
            line = (
                alt.Chart(df_long[df_long["Métrica"] == "Folga Mínima"])
                .mark_line(strokeDash=[4, 4], size=2)
                .encode(
                    x="Dias_obrig:O",
                    y="Percentual:Q",
                    color=alt.Color("Métrica:N", title="Legenda")
                )
            )

            # combinação e títulos
            chart = (
                (bars + line)
                .properties(
                    title="Taxa Semanal vs. Folga Mínima por Dias Obrigatórios"
                )
            )

            st.altair_chart(chart, use_container_width=True)
