# CP06 — Smart Factory | Edge Computing

- **Curso:** Ciências da Computação — 2º ano
- **Turma:** não informada (atualizar antes da entrega)
- **Equipe:** João Victor Alves de Abreu e Rodrigo Kenshin Viana Matayoshi

## Integrantes

- João Victor Alves de Abreu — RM564946
- Rodrigo Kenshin Viana Matayoshi — RM564026

## Links obrigatórios da entrega

- **Projeto Wokwi:** PENDENTE — criar/importar a simulação no Wokwi e substituir por link público funcional.
- **Vídeo YouTube (Não listado):** PENDENTE — gravar demonstração de 2 a 5 minutos e inserir o link.

> Os dois links precisam estar acessíveis sem convite ou autorização. O diagrama e firmware da pasta `firmware/` são a base pronta para importar/compilar no Wokwi. Nenhum link externo foi inventado.

## Arquitetura

```text
ESP32 + DHT22 + LEDs
   ├─ calcula NORMAL/ALERTA localmente e controla os LEDs (edge)
   └─ publica JSON a cada 5 s via MQTT
             ↓
   broker.hivemq.com:1883 (broker público)
             ↓
      API Flask (container api, :5000)
             ↓ HTTP interno do Compose
   Dashboard Flask (container dashboard, :5001)
```

O broker apenas transporta mensagens. A regra de estado e os LEDs são determinados no ESP32. A API mantém em memória somente a leitura válida mais recente e o dashboard a apresenta. Nenhum broker é instalado ou executado pelo projeto.

## Regra de operação

- Temperatura **> 35 °C**: estado `ALERTA`, LED vermelho ligado e verde desligado.
- Temperatura **≤ 35 °C**: estado `NORMAL`, LED verde ligado e vermelho desligado.
- Exatamente 35 °C é `NORMAL`. A umidade é exibida e não altera o estado.
- Mensagem MQTT: `{"temperatura": 36.5, "umidade": 60.0, "estado": "ALERTA"}`.

### Tópico MQTT

```text
edge/2ano/turma-nao-informada/cp06/equipe-b9c1a2/dados
```

**Atenção:** `turma-nao-informada` é provisório porque a turma não veio na solicitação. Antes da entrega, troque esse segmento pelo nome/número real da turma **nos três lugares**: `firmware/src/main.cpp`, `compose.yaml` e este README. O broker é público: o tópico e os identificadores de cliente foram anonimizados; publique somente dados simulados, sem informações pessoais. Os client IDs (`cp06-esp32-...` e `cp06-api-...`) são diferentes.

## Componentes Wokwi

O `firmware/diagram.json` inclui ESP32 DevKit, DHT22, dois LEDs e resistores de 220 Ω. Ligações usadas:

| Componente | Pino ESP32 |
|---|---:|
| DHT22 DATA | GPIO 4 |
| LED verde (via resistor) | GPIO 18 |
| LED vermelho (via resistor) | GPIO 19 |
| Alimentação do sensor | 3V3 e GND |

O Wi-Fi de simulação usa `Wokwi-GUEST`, sem senha. Para publicar no HiveMQ, a simulação precisa ter acesso à internet conforme o ambiente Wokwi utilizado.

### Compilar o firmware

Com PlatformIO instalado:

```bash
cd firmware
pio run
```

As bibliotecas Arduino para DHT22 e PubSubClient estão definidas em `firmware/platformio.ini` e `firmware/libraries.txt` (Wokwi). Monitor serial a 115200 bps.

## Executar API e dashboard com Docker Compose

Na raiz do projeto:

```bash
docker compose up --build
```

- Dashboard: <http://localhost:5001>
- API: <http://localhost:5000/dados>
- Encerrar: `Ctrl+C`; para parar em background, `docker compose down`.

A API retorna `503` e `{"mensagem":"Aguardando dados do ESP32"}` até receber uma mensagem válida. O dashboard mostra “Aguardando dados” nesse período, sem inventar valores. A atualização manual é pelo botão **Atualizar leitura**; há também atualização periódica a cada 15 segundos.

## Testes

Na raiz do repositório:

```bash
python -m pip install -r api/requirements.txt -r dashboard/requirements.txt
python -m unittest discover -s test -v
```

Os testes cobrem o limite de 35 °C, campos obrigatórios e consistência do estado MQTT, atualização da última leitura, resposta `503` inicial, renderização do dashboard sem medições fictícias e indisponibilidade da API. Para uma integração física/simulada completa, deixe os serviços Docker em execução e inicie a simulação Wokwi; valide o dashboard para temperaturas de 30 °C, 35 °C, 36 °C e 30 °C, observando `NORMAL → NORMAL → ALERTA → NORMAL` e os LEDs correspondentes.

Para validar também a compilação do firmware, dentro de `firmware/` execute `pio run` (PlatformIO).

## Dificuldade encontrada e solução

Uma dificuldade é coordenar duas aplicações com responsabilidades diferentes e evitar que a interface apresente valores antes da chegada da primeira medição. A solução mantém o caminho de dados simples: o ESP32 publica a leitura, a API assina o tópico e guarda a última mensagem válida, e o dashboard consulta a API pela rede interna do Compose. A resposta `503` é tratada como estado de espera, não como uma medição. A decisão crítica dos LEDs permanece local no ESP32, preservando o propósito de Edge Computing mesmo se a API ou o dashboard estiverem indisponíveis.

## Estrutura

```text
.
├── api/                 # Flask :5000 e cliente/assinante MQTT
├── dashboard/           # Flask :5001 e página web
├── firmware/            # PlatformIO, ESP32 e diagrama Wokwi
├── test/                # testes automatizados da API
└── compose.yaml          # somente api e dashboard
```
