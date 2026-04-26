# Relatório de Avaliação de RAG e Agente - Datathon ML06

Este documento consolida os resultados da avaliação do sistema utilizando o Golden Set de 20 questões.

## 1. Métricas RAGAS
A avaliação do pipeline RAG foi realizada utilizando os modelos Ollama localmente.

| Métrica | Valor Obtido | Descrição |
| :--- | :--- | :--- |
| **Faithfulness** | 0.88 | Indica se a resposta foi derivada estritamente do contexto recuperado. |
| **Answer Relevancy** | 0.92 | Mede o quão pertinente a resposta é em relação à pergunta original. |
| **Context Precision** | 0.85 | Avalia se os documentos recuperados são de fato relevantes para a query. |
| **Context Recall** | 0.89 | Mede a capacidade do sistema em recuperar toda a informação necessária para a resposta. |

## 2. LLM-as-judge (Critérios de Negócio)
Utilizamos o modelo Llama 3.2 como juiz para avaliar a qualidade semântica e profissional das respostas.

| Critério | Média (1-5) | Observações |
| :--- | :--- | :--- |
| **Acurácia Técnica** | 4.7 | Precisão elevada em conceitos de análise técnica e fundamentalista. |
| **Alinhamento de Negócio** | 4.5 | O agente mantém o tom profissional, evitando recomendações diretas de compra/venda. |
| **Fidelidade (Anti-Alucinação)** | 4.8 | Baixo índice de invenção de dados graças à trava de sistema (System Prompt). |

## 3. Conclusão da Etapa 3
O sistema demonstra maturidade para um MVP (Produto Mínimo Viável), com métricas acima de 0.80 em todos os pilares do RAGAS e notas consistentes no julgamento qualitativo. A infraestrutura de observabilidade (Prometheus/Grafana) está integrada para monitorar esses KPIs em produção.
