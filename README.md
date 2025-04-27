# Escalas Inteligentes

**Otimização de escalas presenciais em regime de trabalho híbrido**\
Aplicação *Streamlit* · Modelo MIP em *PuLP*

---

## ✨ Visão geral

O projeto **Escalas Inteligentes** nasceu da necessidade de reorganizar os espaços de trabalho de uma grande instituição financeira no cenário pós‑pandemia. Com o regime híbrido, o fluxo de pessoas no escritório tornou‑se altamente variável, causando:

- sobrecarga pontual de ambientes;
- subutilização de áreas em outros dias;
- perda de sinergia entre times que deveriam interagir presencialmente.

Nossa proposta extensionista combina **Pesquisa Operacional** e uma interface amigável em **Streamlit** para gerar escalas semanais de presença que sejam:

- **justas** — atendem às restrições individuais e de negócio;
- **eficientes** — maximizam o uso dos recursos físicos disponíveis;
- **adaptadas** — permitem cenários múltiplos e análise de sensibilidade.

O resultado é um conhecimento replicável, aplicável a qualquer organização que enfrente desafios semelhantes de alocação de espaços.

---

## 🗺️ Funcionalidades principais

| Módulo                     | Descrição                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Layout**                 | Define corredores, mesas e lugares; mostra *preview* ASCII.                                                              |
| **Times & Sinergias**      | Cadastra equipes, tamanhos e relações de sinergia.                                                                       |
| **Preferências de Dias**   | Registra dias preferenciais e obrigatórios, com pesos.                                                                   |
| **Configuração do Modelo** | Ajusta função‑objetivo, folgas, penalidades e cenários de dias obrigatórios.                                             |
| **Execução**               | Resolve cada cenário com o solver CBC via *PuLP*.                                                                        |
| **Visualização**           | Exibe métricas, alocação por mesa/dia, gráficos Altair e relatório de sensibilidade (Reduced Cost, Shadow Price, Slack). |

---
▶️ Demonstração em vídeo

Assista à compilação completa de uso da aplicação no YouTube:
https://youtu.be/a1Ne6lLUytM

---

## ⚙️ Arquitetura

```
📂 projeto/
├─ main.py                       # Front‑end Streamlit
├─ layout_configuration.py       # Configuração do layout físico
├─ cadastro_times_sinergias.py   # Times e sinergias
├─ preferencias_dias.py          # Preferências por dia
├─ configuracao_modelo_restricoes.py # Hiperparâmetros do MIP
├─ execucao_modelo.py            # Construção e solução do modelo MIP
├─ visualizacao_resultados.py    # Dashboards e relatórios
└─ requirements.txt              # Dependências Python
```

### Modelo matemático (resumo)

| Conjunto | Significado                              |
| -------- | ---------------------------------------- |
| `T`      | Times                                    |
| `P`      | Posições individuais                     |
| `M`      | Mesas                                    |
| `D_M`    | Pares de mesas (distância pré‑calculada) |
| `D`      | Dias úteis (Seg‑Sex)                     |

| Variável binária | Interpretação                                                        |
| ---------------- | -------------------------------------------------------------------- |
| `x_{t,p,d}`      | Time `t` ocupa posição `p` no dia `d`                                |
| `y_{t,m,d}`      | Time `t` ocupa **alguma** posição da mesa `m` no dia `d`             |
| `z_{t,m1,m2,d}`  | Ambas as mesas `m1` e `m2` são usadas pelo mesmo time `t` no dia `d` |
| `pres_{t,d}`     | Time `t` está presencial no dia `d`                                  |

**Objetivo (exemplo padrão)**

```
max  Σ x_{t,p,d}   −   w_dist · Σ dist(m1,m2) · z_{t,m1,m2,d}
```

> Maximizar ocupação total e, simultaneamente, penalizar a divisão de um time em mesas distantes.

**Principais restrições**

1. **Capacidade de assento**       `Σ_t x_{t,p,d} ≤ 1`  ∀ `p,d`
2. **Ligação x‑y**                  `x_{t,p,d} ≤ y_{t,m,d}`
3. **Contiguidade (mesas vs. time)** `Σ_p∈m x_{t,p,d} ≤ cap·y_{t,m,d}`
4. **Distância intra‑time**         `z_{t,m1,m2,d} ≥ y_{t,m1,d} + y_{t,m2,d} − 1`
5. **Presença mínima**              `Σ_p x_{t,p,d} = size_t · pres_{t,d}`
6. **Dias obrigatórios**            `Σ_d pres_{t,d} = k` (cenário)
7. **Folga diária**                `Σ_{t,p} x_{t,p,d} ≤ cap_total − folga_min`

---

## 🚀 Instalação rápida

> Requer Python ≥ 3.9

```bash
# 1. clone o repositório
$ git clone https://github.com/seu‑usuario/escalas‑inteligentes.git
$ cd escalas‑inteligentes

# 2. crie/ative um ambiente virtual (opcional, mas recomendado)
$ python -m venv .venv
$ source .venv/bin/activate  # Linux/macOS
# ou
$ .venv\Scripts\activate    # Windows

# 3. instale as dependências
$ pip install -r requirements.txt

# 4. execute a aplicação
$ streamlit run main.py
```

**Principais dependências**

- streamlit
- pulp  (solver CBC já incluído)
- pandas · altair · numpy · matplotlib (visualização)

---

## 🏃‍♀️ Como usar

1. **Layout**: defina corredores, mesas e lugares. Salve.
2. **Times & Sinergias**: cadastre cada time e marque sinergias bidirecionais.
3. **Preferências de Dias**: escolha dias preferenciais, número de dias obrigatórios e peso.
4. **Configuração**: selecione função‑objetivo, folga mínima e cenários (k = dias obrigatórios). Salve.
5. **Execução**: clique em *Executar Otimização* e aguarde a solução.
6. **Visualização**: explore métricas, gráficos, tabelas e o relatório de sensibilidade.

A qualquer momento, navegue pelos botões no topo ou menu lateral para voltar e ajustar parâmetros.

Contribuições e *issues* são muito bem‑vindos!

---

## 🤝 Como contribuir

1. Faça um *fork* do projeto e crie sua *feature branch* (`git checkout -b feature/minha‑feature`).
2. Commit e *push* (`git commit -m 'feat: descrição' && git push origin feature/minha‑feature`).
3. Abra um *Pull Request* descrevendo sua proposta.

Para discutir ideias antes de codar, abra uma *issue*.

---

## 📝 Licença

Distribuído sob a licença **MIT**. Consulte `LICENSE` para mais detalhes.

---

## 👤 Autor

Thiago Bibiano da Silva — [LinkedIn]([https://www.linkedin.com/in/thiagobibiano](https://www.linkedin.com/in/thiago-bibiano-da-silva-510b3b15b/)) · [thiagobibiano@ymail.com](mailto\:thiagobibiano@ymail.com)

