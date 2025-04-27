from typing import Dict, List, Optional


class ConfiguracaoModelo:
    """Configura o modelo de otimização e suas restrições.

    Novos parâmetros
    ----------------
    folga_minima : int
        Número mínimo de cadeiras vazias que deve sobrar em cada dia.
    peso_distancia : float
        Peso da penalidade de distância entre mesas quando um mesmo time se divide.
    dias_obrigatorios_range : List[int]
        Lista de valores (cenários) para o número de dias presenciais obrigatórios
        a serem testados na análise de sensibilidade.
    """

    OBJETIVOS_VALIDOS = {"max_ocupacao_media", "max_satisfacao", "min_desalocacao"}

    # ------------------------------------------------------------------ #
    def __init__(
        self,
        funcao_objetivo: str,
        pesos_restricoes: Dict[str, float],
        limite_sobrealocacao: float,
        folga_minima: int = 0,
        peso_distancia: float = 10.0,
        dias_obrigatorios_range: Optional[List[int]] = None,
        restricoes_realocacao: Optional[Dict[str, bool]] = None,
    ) -> None:
        # -------- parâmetros básicos ---------------------------------- #
        if funcao_objetivo not in self.OBJETIVOS_VALIDOS:
            raise ValueError(
                f"Tipo de função objetivo inválido. Opções: {self.OBJETIVOS_VALIDOS}"
            )
        if limite_sobrealocacao < 0:
            raise ValueError("O limite de sobrealocação não pode ser negativo.")
        for nome, peso in pesos_restricoes.items():
            if peso < 0:
                raise ValueError(f"O peso da restrição '{nome}' não pode ser negativo.")

        # -------- novos parâmetros ------------------------------------ #
        if folga_minima < 0:
            raise ValueError("A folga mínima não pode ser negativa.")
        if peso_distancia < 0:
            raise ValueError("O peso de distância deve ser não negativo.")
        if dias_obrigatorios_range is None or len(dias_obrigatorios_range) == 0:
            dias_obrigatorios_range = [2]  # valor padrão

        self.funcao_objetivo: str = funcao_objetivo
        self.pesos_restricoes: Dict[str, float] = pesos_restricoes
        self.limite_sobrealocacao: float = limite_sobrealocacao
        self.folga_minima: int = folga_minima
        self.peso_distancia: float = peso_distancia
        self.dias_obrigatorios_range: List[int] = sorted(set(dias_obrigatorios_range))
        self.restricoes_realocacao: Dict[str, bool] = (
            restricoes_realocacao if restricoes_realocacao else {}
        )

    # ------------------------------------------------------------------ #
    def resumo_configuracao(self) -> str:
        """Retorna um resumo textual das configurações."""
        return (
            f"Função objetivo: {self.funcao_objetivo}\n"
            f"Pesos: {self.pesos_restricoes} (distância={self.peso_distancia})\n"
            f"Limite sobrealocação: {self.limite_sobrealocacao}\n"
            f"Folga mínima (cadeiras/dia): {self.folga_minima}\n"
            f"Cenários dias obrigatórios: {self.dias_obrigatorios_range}\n"
            f"Restrições de realocação: {self.restricoes_realocacao}"
        )
