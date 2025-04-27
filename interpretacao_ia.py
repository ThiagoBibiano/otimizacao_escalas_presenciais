import time
from typing import Dict, Any


class InterpretacaoIA:
    """Classe para gerar uma interpretação textual dos resultados obtidos pelo modelo de otimização utilizando IA Generativa.

    Essa classe simula o uso de uma IA generativa para converter os dados de alocação e métricas do modelo
    em um relatório descritivo e interpretativo. Em uma implementação real, este método faria uma chamada a uma
    API de IA (por exemplo, GPT) para obter uma explicação detalhada dos resultados.

    Attributes:
        resultados (Dict[str, Any]): Dicionário contendo os resultados da execução do modelo.
            Espera-se que contenha chaves como "alocacao", "tempo_execucao" e "mensagem".
    """

    def __init__(self, resultados: Dict[str, Any]) -> None:
        """Inicializa a instância de InterpretacaoIA com os resultados do modelo.

        Args:
            resultados (Dict[str, Any]): Resultados obtidos pela execução do modelo.
        """
        self.resultados = resultados

    def interpretar_resultado(self) -> str:
        """Gera uma interpretação textual dos resultados utilizando IA Generativa.

        Este método simula a geração de um relatório descritivo que explica a alocação dos times,
        o tempo de execução e outras métricas importantes. Em uma aplicação real, uma API de IA seria chamada
        para fornecer uma interpretação baseada em linguagem natural.

        Returns:
            str: Texto explicativo com a interpretação dos resultados.
        """
        # Simula o tempo de resposta de uma API de IA generativa
        time.sleep(1)

        alocacao = self.resultados.get("alocacao", {})
        tempo_execucao = self.resultados.get("tempo_execucao", "N/A")
        mensagem = self.resultados.get("mensagem", "")

        interpretacao = "Interpretação dos Resultados:\n"
        interpretacao += f"O modelo executou a otimização em {tempo_execucao} segundos.\n"
        interpretacao += "A alocação obtida foi a seguinte:\n"

        for corredor, mesas in alocacao.items():
            interpretacao += f"\nNo {corredor}:\n"
            for mesa_info in mesas:
                mesa = mesa_info.get("mesa")
                posicoes = mesa_info.get("posicoes", [])
                times_str = ", ".join(posicoes)
                interpretacao += f"  Mesa {mesa}: {times_str}\n"

        interpretacao += f"\nMensagem do modelo: {mensagem}\n"
        interpretacao += ("Essa configuração demonstra uma alta sinergia entre os times e atende, na maioria, "
                          "as preferências individuais e coletivas definidas. Recomenda-se analisar os detalhes "
                          "para identificar oportunidades de ajustes finos na distribuição, caso necessário.")
        return interpretacao


if __name__ == "__main__":
    # Exemplo de uso do módulo de Interpretação via IA Generativa
    resultados_exemplo: Dict[str, Any] = {
        "alocacao": {
            "Corredor 1": [
                {"mesa": 1, "posicoes": ["Time A", "Time B", "Time C", "Time D"]},
                {"mesa": 2, "posicoes": ["Time E", "Time F", "Time G", "Time H"]}
            ],
            "Corredor 2": [
                {"mesa": 1, "posicoes": ["Time I", "Time J", "Time K", "Time L"]},
                {"mesa": 2, "posicoes": ["Time M", "Time N", "Time O", "Time P"]}
            ]
        },
        "tempo_execucao": 1.02,
        "mensagem": "Modelo resolvido com sucesso!"
    }

    interpretador = InterpretacaoIA(resultados=resultados_exemplo)
    relatorio = interpretador.interpretar_resultado()
    print(relatorio)
