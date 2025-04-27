from typing import List, Dict, Any
import math


class LayoutConfiguration:
    """Classe para gerenciar a configuração inicial do layout da aplicação Streamlit.

    Esta classe permite ao usuário definir o número de corredores, o número de mesas por corredor
    e o número de posições por mesa. Também fornece um método para gerar uma visualização do layout.

    Atributos:
        num_corridors (int): O número total de corredores.
        tables_per_corridor (List[int]): Uma lista onde cada elemento representa o número de mesas em um corredor.
        positions_per_table (int): O número de posições disponíveis por mesa.
    """

    def __init__(self, num_corridors: int, tables_per_corridor: List[int],
                 positions_per_table: int) -> None:
        """Inicializa a configuração do layout com os parâmetros especificados.

        Args:
            num_corridors (int): O número de corredores.
            tables_per_corridor (List[int]): Uma lista de inteiros, cada um representando o número de mesas
                no respectivo corredor. O tamanho da lista deve ser igual a `num_corridors`.
            positions_per_table (int): O número de posições disponíveis por mesa.

        Raises:
            ValueError: Se algum dos parâmetros numéricos não for positivo ou se o tamanho da
                lista `tables_per_corridor` não corresponder ao valor de `num_corridors`.
        """
        if num_corridors <= 0:
            raise ValueError("O número de corredores deve ser um inteiro positivo.")
        if positions_per_table <= 0:
            raise ValueError("O número de posições por mesa deve ser um inteiro positivo.")
        if len(tables_per_corridor) != num_corridors:
            raise ValueError("O tamanho de tables_per_corridor deve ser igual a num_corridors.")

        for num_tables in tables_per_corridor:
            if num_tables <= 0:
                raise ValueError("Cada corredor deve ter ao menos uma mesa.")

        self.num_corridors = num_corridors
        self.tables_per_corridor = tables_per_corridor
        self.positions_per_table = positions_per_table

    def generate_layout_preview(self) -> Dict[str, Any]:
        """Gera uma visualização prévia da configuração do layout.

        A visualização é retornada como um dicionário aninhado onde cada corredor é representado por uma chave,
        e o valor é uma lista de dicionários para cada mesa, contendo o número da mesa e sua
        capacidade de posições.

        Returns:
            Dict[str, Any]: Um dicionário aninhado representando a visualização do layout.
        """
        preview = {}
        for corridor_index in range(1, self.num_corridors + 1):
            tables = []
            num_tables = self.tables_per_corridor[corridor_index - 1]
            for table_index in range(1, num_tables + 1):
                table_config = {
                    "table_number": table_index,
                    "positions": self.positions_per_table
                }
                tables.append(table_config)
            preview[f"Corredor {corridor_index}"] = tables
        return preview

    def render_ascii(self) -> str:
        """Gera um ‘desenho’ ASCII com corredores lado a lado."""
        col_width = max(10, 10 + self.positions_per_table * 2)          # largura mínima
        header = "".join(f"{f'Corredor {i+1}':<{col_width}}"            # cabeçalho
                         for i in range(self.num_corridors))

        max_tables = max(self.tables_per_corridor)
        lines: List[str] = [header]

        for t in range(max_tables):
            row_lbl, row1, row2 = "", "", ""
            for c in range(self.num_corridors):
                if t < self.tables_per_corridor[c]:
                    lbl = f"Mesa {t+1}: "
                    per_row = math.ceil(self.positions_per_table / 2)
                    seats = "[L]" * per_row
                    row_lbl += f"{lbl:<{col_width}}"
                    row1   += f"{seats:<{col_width}}"
                    row2   += f"{seats:<{col_width}}"
                else:                                                  # corredor sem essa mesa
                    row_lbl += " " * col_width
                    row1   += " " * col_width
                    row2   += " " * col_width
            lines += [row_lbl.rstrip(), row1.rstrip(), row2.rstrip(), ""]

        return "\n".join(lines)


def validate_layout_configuration(config: LayoutConfiguration) -> bool:
    """Valida a configuração de layout fornecida.

    Esta função verifica se os valores de corredores, mesas por corredor e posições por mesa são positivos,
    garantindo que o comprimento da lista `tables_per_corridor` corresponda ao número de corredores.

    Args:
        config (LayoutConfiguration): Uma instância de LayoutConfiguration a ser validada.

    Returns:
        bool: True se a configuração for válida.

    Raises:
        ValueError: Se algum parâmetro da configuração for inválido.
    """
    if config.num_corridors <= 0:
        raise ValueError("Configuração inválida: o número de corredores deve ser maior que zero.")
    if config.positions_per_table <= 0:
        raise ValueError("Configuração inválida: o número de posições por mesa deve ser maior que zero.")
    if len(config.tables_per_corridor) != config.num_corridors:
        raise ValueError("Configuração inválida: o tamanho de tables_per_corridor deve ser igual ao número de corredores.")
    return True


if __name__ == "__main__":
    # Exemplo de uso:
    try:
        # Define uma configuração de layout:
        # - 3 corredores com [2, 3, 2] mesas respectivamente
        # - Cada mesa possui 4 posições
        layout_config = LayoutConfiguration(
            num_corridors=3,
            tables_per_corridor=[2, 3, 2],
            positions_per_table=4
        )
        validate_layout_configuration(layout_config)
        preview = layout_config.generate_layout_preview()
        print("Visualização do Layout:")
        for corridor, tables in preview.items():
            print(corridor + ":")
            for table in tables:
                print(f"  Mesa {table['table_number']} - Posições: {table['positions']}")
    except ValueError as err:
        print(f"Erro na configuração: {err}")
