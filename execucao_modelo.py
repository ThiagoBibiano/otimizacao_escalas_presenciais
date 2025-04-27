# execucao_modelo.py
from __future__ import annotations
import time
from typing import Any, Dict, List, Tuple

import pulp as pl
from preferencias_dias import DIAS_UTEIS


VIABLE_STATI = {pl.LpStatusOptimal}          # 1                 (CBC)
INFEASIBLE_STATI = {pl.LpStatusInfeasible,   # -1
                    pl.LpStatusUnbounded,    # -2
                    pl.LpStatusUndefined}    # -3
# 0 = Not Solved (pode ser viável, mas não foi provado)
MAYBE_STATI = {pl.LpStatusNotSolved}


class ExecucaoModelo:
    """
    Resolve cada cenário de dias obrigatórios.
    Guarda: métricas, modelo PulP e variáveis.
    Também devolve a lista de cenários inviáveis.
    """

    # ------------------------------------------------------------------ #
    # 0. CONSTRUÇÃO
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        layout_config: Any,
        cadastro_times: Any,
        cadastro_preferencias: Any,
        configuracao_modelo: Any,
    ) -> None:
        self.layout = layout_config
        self.cad_times = cadastro_times
        self.prefs = cadastro_preferencias
        self.cfg = configuracao_modelo

        self.mesas = self._lista_mesas()
        self.posicoes = self._lista_posicoes()
        self.dist = self._dist_mesas()
        self.cap_total = len(self.posicoes)

    # ------------------------------------------------------------------ #
    # 1. HELPERS RÁPIDOS
    # ------------------------------------------------------------------ #
    def _upper_bound_feasible(self, dias_obrig: int) -> bool:
        """
        Teste de folga grossa:
        média diária necessária ≤ capacidade diária.
        Se reprovar aqui, o MIP é certamente inviável.
        """
        pessoas = sum(t.qtde_integrantes for t in self.cad_times.times.values())
        demanda_dia = pessoas * dias_obrig / len(DIAS_UTEIS)
        return demanda_dia <= self.cap_total - self.cfg.folga_minima

    # -------------------- helpers de layout -------------------------- #
    def _lista_mesas(self):
        mesas = {}
        for c in range(1, self.layout.num_corridors + 1):
            cor = f"Corredor {c}"
            for m in range(1, self.layout.tables_per_corridor[c - 1] + 1):
                mesas[f"{cor}_M{m}"] = (cor, m)
        return mesas

    def _lista_posicoes(self):
        pos = {}
        for mesa_id, (cor, _) in self.mesas.items():
            for p in range(1, self.layout.positions_per_table + 1):
                pos[f"{mesa_id}_P{p}"] = (mesa_id, cor)
        return pos

    def _dist_mesas(self):
        dist = {}
        for m1, (c1, idx1) in self.mesas.items():
            for m2, (c2, idx2) in self.mesas.items():
                if m1 >= m2:
                    continue
                dist[(m1, m2)] = 0 if m1 == m2 else (abs(idx1 - idx2) if c1 == c2 else 5 + abs(idx1 - idx2))
        return dist

    # ------------------------------------------------------------------ #
    # 2. RESOLVE UM CENÁRIO
    # ------------------------------------------------------------------ #
    def _solve_for_k(self, dias_obrig: int) -> Dict[str, Any]:
        if not self._upper_bound_feasible(dias_obrig):
            return {"status": "EarlyInfeasible"}

        times = list(self.cad_times.times.values())
        dias = DIAS_UTEIS

        # ---- variables
        x = {(t.nome, p, d): pl.LpVariable(f"x_{t.nome}_{p}_{d}", cat="Binary")
             for t in times for p in self.posicoes for d in dias}
        y = {(t.nome, m, d): pl.LpVariable(f"y_{t.nome}_{m}_{d}", cat="Binary")
             for t in times for m in self.mesas for d in dias}
        z = {(t.nome, m1, m2, d): pl.LpVariable(f"z_{t.nome}_{m1}_{m2}_{d}", cat="Binary")
             for t in times for (m1, m2) in self.dist for d in dias}
        pres = {(t.nome, d): pl.LpVariable(f"pres_{t.nome}_{d}", cat="Binary")
                for t in times for d in dias}

        prob = pl.LpProblem(f"Alocacao_k{dias_obrig}", pl.LpMaximize)

        # ---- objective
        w_dist = self.cfg.peso_distancia
        prob += (
            pl.lpSum(x.values())
            - w_dist * pl.lpSum(self.dist[m1, m2] * z[t.nome, m1, m2, d]
                                for t in times for (m1, m2) in self.dist for d in dias)
        )

        # ---- constraints (igual às versões anteriores, omitidas aqui por brevidade)
        cap = self.layout.positions_per_table
        for p in self.posicoes:
            for d in dias:
                prob += pl.lpSum(x[t.nome, p, d] for t in times) <= 1

        for t in times:
            for m in self.mesas:
                pos_mesa = [p for p, (mm, _) in self.posicoes.items() if mm == m]
                for d in dias:
                    prob += pl.lpSum(x[t.nome, p, d] for p in pos_mesa) <= cap * y[t.nome, m, d]
                    for p in pos_mesa:
                        prob += x[t.nome, p, d] <= y[t.nome, m, d]

        for t in times:
            for (m1, m2) in self.dist:
                for d in dias:
                    prob += z[t.nome, m1, m2, d] >= y[t.nome, m1, d] + y[t.nome, m2, d] - 1

        for t in times:
            for d in dias:
                prob += pl.lpSum(x[t.nome, p, d] for p in self.posicoes) == t.qtde_integrantes * pres[t.nome, d]

        for t in times:
            prob += pl.lpSum(pres[t.nome, d] for d in dias) == dias_obrig

        for d in dias:
            prob += pl.lpSum(x[t.nome, p, d] for t in times for p in self.posicoes) <= self.cap_total - self.cfg.folga_minima

        # ---- solve
        t0 = time.perf_counter()
        prob.solve(pl.PULP_CBC_CMD(msg=False))
        runtime = round(time.perf_counter() - t0, 2)

        status = pl.LpStatus[prob.status]

        # ---------- trata status ---------------------------------------
        if prob.status in INFEASIBLE_STATI:
            return {"status": status}

        if prob.status in MAYBE_STATI:
            # CBC não conseguiu provar otimalidade; ainda assim podemos
            # ler a melhor solução incumbente (se existir).
            if any(v.value() is not None for v in prob.variables()):
                status = "Feasible"
            else:                       # nada viável encontrado
                return {"status": status}

        # ---------- métricas -------------------------------------------
        ND = len(DIAS_UTEIS)  # normalmente 5
        ocup_total = sum(var.value() for var in x.values())
        taxa_semanal = ocup_total / (ND * self.cap_total)

        return dict(
            status=status,
            ocup_total=ocup_total,
            taxa_semanal=round(taxa_semanal, 3),
            tempo_execucao=runtime,
            model=prob,
            x_vars=x,
        )

    # ------------------------------------------------------------------ #
    # 3. EXECUTA TODOS OS CENÁRIOS
    # ------------------------------------------------------------------ #
    def executar(self) -> Dict[str, Any]:
        viaveis, inviaveis = {}, {}
        alocacoes, model_dict, var_dict = {}, {}, {}

        for k in self.cfg.dias_obrigatorios_range:
            res = self._solve_for_k(k)

            if res.get("status") in {"Optimal", "Feasible"}:
                # ---- métricas ----
                viaveis[k] = {kk: vv for kk, vv in res.items()
                              if kk not in ("model", "x_vars", "status")}
                model_dict[k] = res["model"]
                var_dict[k] = res["x_vars"]

                # ---- alocação legível ------------------------------
                aloc = {}
                for (team, pos, dia), var in res["x_vars"].items():
                    if var.value() != 1:
                        continue

                    # 'pos' já é exatamente a chave no seu dict self.posicoes
                    mesa_id, corredor = self.posicoes[pos]
                    # mesa_id vem como "Corredor X_MY", então extraímos o número:
                    mesa_num = int(mesa_id.split("_M")[1])

                    chave = f"{k}d | {dia} · {corredor}"
                    mesa_dict = next(
                        (m for m in aloc.setdefault(chave, []) if m["mesa"] == mesa_num),
                        None
                    )
                    if not mesa_dict:
                        mesa_dict = {
                            "mesa": mesa_num,
                            "corredor": corredor,
                            "posicoes": []
                        }
                        aloc[chave].append(mesa_dict)

                    mesa_dict["posicoes"].append(team)

                alocacoes[k] = aloc
            else:
                inviaveis[k] = res["status"]

        if not viaveis:
            raise RuntimeError("Todos os cenários foram classificados como inviáveis.")

        return dict(
            cenarios=viaveis,
            alocacoes=alocacoes,
            model_dict=model_dict,
            vars_dict=var_dict,
            inviaveis=inviaveis,
            mensagem="Processo concluído.",
        )
