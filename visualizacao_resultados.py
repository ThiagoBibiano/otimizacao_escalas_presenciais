# visualizacao_resultados.py
# ================================================================
from __future__ import annotations
from typing import Any, Dict, List, Tuple

import pandas as pd
import pulp as pl


class VisualizacaoResultados:
    """
    Apresenta resultados de todos os cenários resolvidos pelo solver.

    result:
        ├─ alocacoes[k]   dict  dia·mesa → lista de mesas/posições
        ├─ cenarios[k]    dict  métricas (ocup_total, taxa_semanal, tempo_execucao, …)
        ├─ model_dict[k]  PuLP model
        └─ vars_dict[k]   dict key→PuLP-var
    """

    def __init__(self, resultados: Dict[str, Any]) -> None:
        self.alocacoes = resultados.get("alocacoes", {})
        self.cenarios   = resultados.get("cenarios", {})
        self.model_dict = resultados.get("model_dict", {})
        self.vars_dict  = resultados.get("vars_dict", {})

    def cenarios_disponiveis(self) -> List[int]:
        return sorted(self.alocacoes)

    def tabela_semana(self, k: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        corredores_mesas = {
            (m["corredor"], m["mesa"])
            for lst in self.alocacoes.get(k, {}).values()
            for m in lst
        }
        idx = pd.MultiIndex.from_tuples(
            sorted(corredores_mesas), names=["Corredor", "Mesa"]
        )
        counts = pd.DataFrame(0, index=idx, columns=dias)
        detail_rows = []
        for chave, lst in self.alocacoes.get(k, {}).items():
            _, resto = chave.split("|")
            dia, corredor = [s.strip() for s in resto.split("·")]
            for m in lst:
                cnt = len(m["posicoes"])
                counts.at[(m["corredor"], m["mesa"]), dia] += cnt
                detail_rows.append({
                    "Corredor": m["corredor"],
                    "Mesa":     m["mesa"],
                    "Dia":      dia,
                    "Times":    ", ".join(m["posicoes"]),
                })
        detail = (
            pd.DataFrame(detail_rows)
              .sort_values(["Corredor", "Mesa", "Dia"])
        )
        return counts, detail

    def indicadores_cenario(self, k: int) -> Dict[str, str]:
        met = self.cenarios[k]
        # taxa_semanal vem como fração [0,1], converte para %
        taxa_perc = met["taxa_semanal"] * 100
        folga_perc = 100 - taxa_perc
        tempo     = met["tempo_execucao"]
        return {
            "taxa": f"{taxa_perc:.1f} %",
            "folga": f"{folga_perc:.1f} %",
            "t":     f"{tempo:.2f}s",
        }

    def sensibilidade_df(self) -> pd.DataFrame:
        if not self.cenarios:
            return pd.DataFrame()
        return (
            pd.DataFrame(self.cenarios).T
              .reset_index()
              .rename(columns={"index": "Dias_obrig"})
              .sort_values("Dias_obrig")
        )

    def antigo_relatorio_sensibilidade(self, k: int) -> Dict[str, pd.DataFrame]:
        if k not in self.model_dict:
            return {}
        model  = self.model_dict[k]
        x_vars = self.vars_dict[k]

        obj_df = pd.DataFrame({"Valor ótimo":[pl.value(model.objective)]})

        vars_df = pd.DataFrame([
            {
              "Variavel":    str(key),
              "Valor":       var.value(),
              "ReducedCost": var.dj,
            }
            for key, var in x_vars.items()
        ])

        rest_df = pd.DataFrame([
            {
              "Restricao":  name,
              "ShadowPrice":c.pi,
              "Slack":      c.slack,
            }
            for name, c in model.constraints.items()
        ])

        return {"objetivo": obj_df, "variaveis": vars_df, "restricoes": rest_df}

    # visualizacao_resultados.py  –  substitua relatorio_sensibilidade()

    def relatorio_sensibilidade(self, k: int) -> Dict[str, pd.DataFrame]:
        """
        Retorna três dataframes mais ‘amigáveis’:
            • objetivo   – valor ótimo
            • variaveis  – detalhado (time, mesa, posição, dia…)
            • restricoes – com tipo inferido + preços-sombra
        """
        if k not in self.model_dict:
            return {}

        model  = self.model_dict[k]
        x_vars = self.vars_dict[k]

        # ---- 1. objetivo -------------------------------------------------
        obj_df = pd.DataFrame(
            {"Valor ótimo da função-objetivo": [pl.value(model.objective)]}
        )

        # ---- 2. variáveis ------------------------------------------------
        var_rows = []
        for (team, pos, dia), var in x_vars.items():
            corredor_lbl, mesa_lbl, pos_lbl = pos.split("_")
            mesa_num = mesa_lbl.replace("M", "")
            pos_num  = pos_lbl.replace("P", "")
            var_rows.append(
                dict(
                    Time=team,
                    Corredor=corredor_lbl,
                    Mesa=int(mesa_num),
                    Posição=int(pos_num),
                    Dia=dia,
                    Alocado=int(var.value()),
                    Custo_Reduzido=round(var.dj, 3),
                )
            )
        vars_df = (
            pd.DataFrame(var_rows)
            .sort_values(["Dia", "Corredor", "Mesa", "Posição", "Time"])
            .reset_index(drop=True)
        )

        # ---- 3. restrições ----------------------------------------------
        def _tipo_rest(nome: str) -> str:
            if nome.startswith("_C"):
                idx = int(nome[2:])
                # limites empíricos ajustados ao modelo gerado
                if idx <= 5 * 25:            # 5 dias × (até 25 assentos)
                    return "Capacidade Assento"
                elif idx <= 2 * 5 * 5:       # depois vêm ligações x ≤ y
                    return "Contiguidade Time×Mesa"
                elif idx <= 3 * 5 * 5:       # depois vêm z ≥ y1+y2-1
                    return "Distância Intra-time"
                else:
                    return "Outras"
            elif nome.startswith("pres_"):
                return "Obrigatoriedade de dias"
            else:
                return "Capacidade Total"
        rest_rows = []
        for name, c in model.constraints.items():
            rest_rows.append(
                dict(
                    Restrição_ID=name,
                    Tipo=_tipo_rest(name),
                    Preço_Sombra=round(c.pi, 3),
                    Slack=c.slack,
                )
            )
        rest_df = pd.DataFrame(rest_rows).sort_values("Tipo")

        return {"objetivo": obj_df, "variaveis": vars_df, "restricoes": rest_df}

