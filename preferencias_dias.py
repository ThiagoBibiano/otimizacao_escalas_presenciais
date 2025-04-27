# =========================
# preferencias_dias.py (versão aprimorada)
# =========================
from __future__ import annotations

from typing import Dict, List

DIAS_UTEIS: List[str] = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]


class PreferenciaDia:
    """Preferências de presença para um time."""

    def __init__(
        self,
        nome: str,
        dias_preferenciais: Dict[str, bool] | None = None,
        dias_obrigatorios: int = 0,
        peso: float = 1.0,
    ) -> None:
        if dias_obrigatorios < 0 or dias_obrigatorios > len(DIAS_UTEIS):
            raise ValueError("Dias obrigatórios fora do intervalo válido.")
        self.nome = nome
        self.dias_preferenciais = dias_preferenciais or {d: False for d in DIAS_UTEIS}
        # valida chaves
        for k in self.dias_preferenciais:
            if k not in DIAS_UTEIS:
                raise ValueError(f"Dia inválido: {k}")
        self.dias_obrigatorios = dias_obrigatorios
        self.peso = peso

    # util
    def contar_preferencias(self) -> int:
        return sum(self.dias_preferenciais.values())

    def gerar_resumo(self) -> str:
        marcados = [d for d, v in self.dias_preferenciais.items() if v]
        return (
            f"{self.nome}: dias preferenciais = {marcados or 'Nenhum'}, "
            f"obrigatórios = {self.dias_obrigatorios}, peso = {self.peso}"
        )


class CadastroPreferenciasDias:
    """Gerencia todas as preferências de dias."""

    def __init__(self) -> None:
        self.preferencias: Dict[str, PreferenciaDia] = {}

    def adicionar_preferencia(self, pref: PreferenciaDia) -> None:
        if pref.nome in self.preferencias:
            raise ValueError(f"Preferência para '{pref.nome}' já cadastrada.")
        self.preferencias[pref.nome] = pref

    def atualizar_preferencia(self, pref: PreferenciaDia) -> None:
        if pref.nome not in self.preferencias:
            raise ValueError("Preferência inexistente.")
        self.preferencias[pref.nome] = pref

    def validar_preferencias(self) -> bool:
        for pref in self.preferencias.values():
            if pref.dias_obrigatorios > len(DIAS_UTEIS):
                raise ValueError(
                    f"{pref.nome}: dias obrigatórios excedem número de dias úteis."
                )
        return True
