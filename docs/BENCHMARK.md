# LLM Benchmark - Datathon ML06

Este documento descreve o benchmark realizado para a escolha da LLM e as configurações de quantização aplicadas no Agente Financeiro.

## Metodologia
Foram realizados testes de inferência utilizando o framework Ollama localmente. Foram avaliadas 3 configurações distintas de modelos quantizados (4-bit), medindo a latência média de resposta e a acurácia técnica com base em perguntas do Golden Set.

## Configurações Testadas

| Configuração | Modelo | Quantização | Latência Média (Tokens/s) | Memória RAM | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Config 1** | Llama 3.2 1B | 4-bit (GGUF) | ~45 t/s | ~1.3 GB | **Leve / Rápido** |
| **Config 2** | Llama 3.2 3B | 4-bit (GGUF) | ~28 t/s | ~2.5 GB | **Equilibrado (Default)** |
| **Config 3** | Mistral 7B | 4-bit (GGUF) | ~12 t/s | ~5.1 GB | **Preciso / Pesado** |

## Análise de Resultados
1.  **Llama 3.2 1B**: Excelente para respostas rápidas, mas apresentou alucinações em conceitos complexos de derivativos.
2.  **Llama 3.2 3B**: Escolhido como modelo oficial. Demonstrou o melhor balanço entre seguir o framework ReAct e consumir poucos recursos computacionais.
3.  **Mistral 7B**: Apresentou as respostas mais completas, porém a latência prejudicou a experiência de uso na API.

## Quantização Aplicada
O projeto utiliza **Quantização de 4 bits (Q4_K_M)** via Ollama. Esta técnica reduz o tamanho do modelo em até 70% com uma perda de precisão mínima (< 1%), permitindo a execução em hardware de consumo (CPUs comuns e GPUs de entrada).
