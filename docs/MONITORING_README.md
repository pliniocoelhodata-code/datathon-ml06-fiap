# 📊 Guia de Observabilidade e Monitoramento

Este documento detalha a infraestrutura de observabilidade do projeto Datathon, incluindo métricas, dashboards, tracking de experimentos e alertas.

---

## 🏗️ Arquitetura de Observabilidade

```
Aplicação → Prometheus → Grafana
    ↓           ↓          ↓
  MLflow    Loki       Alertas
    ↓        ↓          ↓
Tracking   Logs     Notificações
```

### Componentes Principais

| Componente | Responsabilidade | Porta | URL |
|------------|------------------|-------|-----|
| **Prometheus** | Coleta e armazenamento de métricas | 9090 | http://localhost:9090 |
| **Grafana** | Visualização e dashboards | 3000 | http://localhost:3000 |
| **MLflow** | Tracking de experimentos | 5000 | http://localhost:5000 |
| **Loki** | Agregação de logs | 3100 | - |

---

## 📈 Métricas no Prometheus

### Métricas de API
```prometheus
# Contadores
prediction_requests_total{ticker="PETR4", status="success"} 150
prediction_requests_total{ticker="VALE3", status="error"} 2

# Histogramas
prediction_duration_seconds_bucket{le="0.1"} 120
prediction_duration_seconds_bucket{le="1.0"} 145
prediction_duration_seconds_count 150

# Gauges
last_predicted_stock_price{ticker="PETR4"} 32.45
```

### Métricas de Drift Detection
```prometheus
# Métricas de drift
model_drift_share{model_name="stock_lstm_v1"} 0.15
model_psi{model_name="stock_lstm_v1"} 0.08
```

### Como Consultar Métricas

#### Via Interface Web
1. Acesse http://localhost:9090
2. Use queries como:
   - `rate(prediction_requests_total[5m])` - Taxa de requests
   - `histogram_quantile(0.95, rate(prediction_duration_seconds_bucket[5m]))` - Latência p95

#### Via API
```bash
# Status do Prometheus
curl http://localhost:9090/api/v1/status/runtimeinfo

# Query de métricas
curl "http://localhost:9090/api/v1/query?query=up"
```

---

## 📊 Dashboards no Grafana

### Acesso Inicial
- **URL**: http://localhost:3000
- **Usuário**: admin
- **Senha**: admin
- **Primeiro acesso**: Será solicitado mudança de senha

### Dashboards Disponíveis

#### 1. **🏢 Business Metrics Dashboard** (`ml_business_dashboard`)
**Foco**: Métricas de negócio e ML do projeto
- **Métricas**:
  - Taxa de erro da API
  - Monitoramento de drift (share of drifted columns)
  - PSI (Population Stability Index)
  - Latência de predições (média e P95)
  - Volume de predições por ticker
  - Últimos preços previstos
  - Taxa de sucesso por status
  - Logs de eventos de drift

#### 2. **🖥️ Infrastructure Metrics Dashboard** (`ml_infra_dashboard`)
**Foco**: Métricas de infraestrutura e sistema
- **Métricas**:
  - CPU usage por container
  - Memória RAM por container
  - Status dos serviços (up/down)
  - Requests por segundo nos serviços
  - Disk usage por container
  - Network I/O (RX/TX)
  - Container logs (excluindo métricas/health)

### Criando Novos Dashboards

1. **Acesse Grafana** → **+** → **New Dashboard**
2. **Adicione painel** → **Add a new panel**
3. **Configure fonte de dados** → Selecione "Prometheus"
4. **Escreva query** → Exemplo: `rate(prediction_requests_total[5m])`
5. **Configure visualização** → Gráfico, tabela, etc.

---

## 🔬 MLflow - Tracking de Experimentos

### Experimentos Disponíveis

#### **Stock_Analysis_Datathon**
- **Runs de Treinamento**: Métricas de modelo (RMSE, MAE, R²)
- **Runs de Drift**: Análise de drift com detalhes por coluna
- **Artefatos**: Modelos salvos, scalers, relatórios JSON

### Como Usar MLflow

#### Via Interface Web
1. Acesse http://localhost:5000
2. Navegue pelos experimentos
3. Compare runs e visualize métricas
4. Baixe artefatos (modelos, scalers)

#### Via Python API
```python
import mlflow
import mlflow.keras

# Conectar ao servidor
mlflow.set_tracking_uri("http://localhost:5000")

# Registrar experimento
mlflow.set_experiment("Stock_Analysis_Datathon")

# Iniciar run
with mlflow.start_run():
    # Logar parâmetros
    mlflow.log_param("learning_rate", 0.001)

    # Logar métricas
    mlflow.log_metric("rmse", 0.85)

    # Logar modelo
    mlflow.keras.log_model(model, "model")
```

### Comparando Experimentos

1. **Selecione múltiplos runs**
2. **Compare métricas**: RMSE, MAE, tempo de treinamento
3. **Visualize artefatos**: Modelos, scalers, configurações
4. **Exporte comparações** para relatórios

---

## 🚨 Sistema de Alertas

### Alertas Configurados

#### **Business Alerts** (Dashboard Business)
- **High Error Rate**: Taxa de erro da API > 10%
  - **Severidade**: Critical
  - **Ação**: Notificação imediata
- **High Latency**: Latência P95 > 2 segundos
  - **Severidade**: Warning
  - **Ação**: Alerta no dashboard
- **Drift Detection**: Drift share > 0.2 ou PSI > 0.2
  - **Severidade**: Critical
  - **Ação**: Retraining trigger + notificação

#### **Infrastructure Alerts** (Dashboard Infrastructure)
- **High CPU**: CPU > 90% por > 5 minutos
  - **Severidade**: Warning
  - **Ação**: Alerta de escalabilidade
- **High Memory**: Memória > 500MB por > 5 minutos
  - **Severidade**: Warning
  - **Ação**: Alerta de vazamento de memória
- **Service Down**: Container parado
  - **Severidade**: Critical
  - **Ação**: Notificação imediata + tentativa de restart

### Configurando Novos Alertas

#### No Grafana
1. **Painel** → **Alert** → **Create Alert**
2. **Query**: `model_drift_share > 0.1`
3. **Condições**: Para > 5 minutos
4. **Notificações**: Email, Slack, PagerDuty

#### No Prometheus (Alertmanager)
```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(prediction_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High prediction latency detected"
```

---

## 📝 Logs e Troubleshooting

### Logs de Aplicação (Loki)

#### Consultando Logs
```bash
# Via Loki API
curl "http://localhost:3100/loki/api/v1/query_range?query={job=\"api\"}&start=1640995200&end=1640998800"

# Via Grafana Explore
1. Acesse Grafana → Explore
2. Selecione fonte "Loki"
3. Query: {job="api"} |= "ERROR"
```

#### Estrutura de Logs
```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "service": "api",
  "user": "user123",
  "ticker": "PETR4",
  "predicted_price": 32.45,
  "event": "prediction_success"
}
```

### Troubleshooting Comum

#### Prometheus não coleta métricas
```bash
# Verificar targets
curl http://localhost:9090/api/v1/targets

# Verificar configuração
docker logs prometheus
```

#### Grafana não conecta ao Prometheus
1. **Data Sources** → **Prometheus**
2. **URL**: http://prometheus:9090
3. **Test Connection**

#### MLflow não registra runs
```python
# Verificar conexão
import mlflow
mlflow.set_tracking_uri("http://localhost:5000")
print(mlflow.get_tracking_uri())
```

---

## 🔧 Configuração Avançada

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
```

### Grafana Provisioning
```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
```

### MLflow Backend
```bash
# Usando SQLite (padrão)
export MLFLOW_TRACKING_URI=http://localhost:5000

# Para produção, usar PostgreSQL
export MLFLOW_TRACKING_URI=postgresql://user:pass@localhost/mlflow
```

---

## 📚 Referências

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [MLflow Documentation](https://mlflow.org/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)

---

## 🤝 Suporte

Para questões sobre observabilidade:
1. Verifique logs dos containers: `docker compose logs [service]`
2. Consulte métricas em tempo real no Prometheus
3. Visualize dashboards no Grafana
4. Documente issues no repositório</content>
<parameter name="filePath">\\wsl.localhost\Ubuntu\home\anacaroline\\datathon-ml06-fiap\\docs\\MONITORING_README.md