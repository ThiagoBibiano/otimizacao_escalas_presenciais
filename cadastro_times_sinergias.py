# =========================
# cadastro_times_sinergias.py (versão ajustada)
# =========================
"""Módulo de cadastro de times e sinergias – versão com utilidades extras.
"""

from __future__ import annotations

from typing import Dict, List


class Time:
    """Representa um time e suas sinergias."""

    def __init__(self, nome: str, qtde_integrantes: int, sinergias: List[str] | None = None) -> None:
        if qtde_integrantes <= 0:
            raise ValueError("A quantidade de integrantes deve ser maior que zero.")
        self.nome: str = nome
        self.qtde_integrantes: int = qtde_integrantes
        self.sinergias: List[str] = sinergias or []

    # ------------------------------------------------------------------
    # Métodos utilitários
    # ------------------------------------------------------------------
    def add_sinergia(self, outro_time: str) -> None:
        if outro_time not in self.sinergias and outro_time != self.nome:
            self.sinergias.append(outro_time)


class CadastroTimesSinergias:
    """Gerencia o conjunto de times e as relações de sinergia."""

    def __init__(self) -> None:
        self.times: Dict[str, Time] = {}

    # ------------------------------ CRUD ------------------------------ #
    def adicionar_time(self, time: Time) -> None:
        if time.nome in self.times:
            raise ValueError(f"O time '{time.nome}' já está cadastrado.")
        self.times[time.nome] = time

    def remover_time(self, nome_time: str) -> None:
        self.times.pop(nome_time, None)
        # remove referências de sinergia
        for t in self.times.values():
            if nome_time in t.sinergias:
                t.sinergias.remove(nome_time)

    # ------------------------- Sinergia ------------------------------- #
    def add_sinergia(self, time1: str, time2: str) -> None:
        """Cria sinergia bidirecional entre *time1* e *time2*."""
        if time1 not in self.times or time2 not in self.times:
            raise ValueError("Ambos os times precisam estar cadastrados antes de criar sinergia.")
        self.times[time1].add_sinergia(time2)
        self.times[time2].add_sinergia(time1)

    # ------------------------ Validação ------------------------------- #
    def validar_cadastro(self) -> bool:
        for time in self.times.values():
            for t_sin in time.sinergias:
                if t_sin not in self.times:
                    raise ValueError(
                        f"Sinergia inválida: o time '{t_sin}' não está cadastrado (referenciado em '{time.nome}')."
                    )
        return True

    # --------------------- Utilidades extras -------------------------- #
    def listar_times(self) -> List[str]:
        return list(self.times.keys())

    def obter_matriz_sinergia(self) -> Dict[str, Dict[str, int]]:
        matriz: Dict[str, Dict[str, int]] = {}
        nomes = self.listar_times()
        for a in nomes:
            matriz[a] = {}
            for b in nomes:
                matriz[a][b] = 1 if (a == b or b in self.times[a].sinergias) else 0
        return matriz
