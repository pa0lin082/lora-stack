# MQTT Meshtastic Subscriber con InfluxDB

Script Python per sottoscriversi al server MQTT Meshtastic, decodificare completamente i messaggi protobuf usando gli schemi ufficiali e salvare tutti i dati in InfluxDB per analisi e visualizzazione.

## ✨ Caratteristiche

- **Decodifica completa protobuf**: Usa gli schemi ufficiali Meshtastic per decodificare accuratamente i messaggi
- **Salvataggio automatico InfluxDB**: Tutti i messaggi vengono salvati automaticamente in InfluxDB
- **Analisi topic**: Interpreta automaticamente la struttura dei topic MQTT Meshtastic  
- **Supporto multi-formato**: JSON, testo, protobuf binario e dati binari generici
- **Decodifica payload tipizzata**: Riconosce e decodifica messaggi di testo, posizione, telemetria, ecc.
- **Submodule git**: Usa i protobuf ufficiali tramite git submodule per aggiornamenti automatici
- **Tags intelligenti**: I dati sono organizzati con tag per region, gateway, canale, node_id, ecc.
- **Gestione timezone UTC**: Tutti i timestamp sono gestiti correttamente in UTC per InfluxDB

## 📦 Installazione

### Prerequisiti
- Python 3.8+
- Git

### Setup iniziale

1. **Clona il repository con submodules:**
   ```bash
   git clone --recursive <url-repository>
   cd influxDBIngest
   ```

2. **Se hai già clonato, inizializza i submodules:**
   ```bash
   git submodule update --init --recursive
   ```

3. **Installa le dipendenze:**
   ```bash
   # Con pipenv (raccomandato)
   pipenv install
   
   # Oppure con pip
   pip install -r requirements.txt
   ```

4. **Genera le classi Python dai protobuf:**
   ```bash
   mkdir -p generated

   pipenv run python -m grpc_tools.protoc -Iprotobufs --python_out=generated --pyi_out=generated --grpc_python_out=generated protobufs/*.proto protobufs/meshtastic/*.proto

   ```

## 🚀 Utilizzo

### Avvio del subscriber

```bash
# Modalità normale - si connette a MQTT e salva i dati
pipenv run python mqtt_subscriber.py

# Modalità test - scrive solo record di prova in InfluxDB
pipenv run python mqtt_subscriber.py --test

# Mostra l'aiuto
pipenv run python mqtt_subscriber.py --help

# Con python normale  
python mqtt_subscriber.py
python mqtt_subscriber.py --test
```

### Modalità test

La modalità test (`--test`) è utile per:
- ✅ Verificare la connessione a InfluxDB
- ✅ Testare la scrittura dei dati
- ✅ Validare la configurazione prima dell'uso reale
- ✅ Debug dei problemi di connessione

La modalità test scrive 3 record di esempio (nodeinfo, telemetry, text) e esce automaticamente.

### Output esempio

```
📨 [2024-01-15 10:30:45] Topic: msh/EU_868/2/c/LongFast/!12345678
📊 Tipo: PROTOBUF | Dimensione: 156 bytes
🔧 PROTOBUF MESHTASTIC DETECTATO!
✅ Decodificato come: ServiceEnvelope
📍 Topic: EU_868 | Gateway: 2 | Formato: c | Canale: LongFast
📦 Dati Decodificati:
{
  "channelId": "LongFast",
  "gatewayId": "!87654321",
  "packet": {
    "from": 305419896,
    "to": 4294967295,
    "channel": 0,
    "decoded": {
      "portnum": "TEXT_MESSAGE_APP",
      "payload": "Q2lhbyBkYSBNZXNodGFzdGljIQ=="
    }
  }
}
🎯 Payload Tipizzato (text):
   💬 Messaggio: Ciao da Meshtastic!
```

## 🔧 Configurazione

### MQTT
Le impostazioni MQTT sono nel file `mqtt_subscriber.py`:

```python
MQTT_HOST = "trolley.proxy.rlwy.net"
MQTT_PORT = 57275
MQTT_USERNAME = "admin"
MQTT_PASSWORD = "admin"
MQTT_ROOT_TOPIC = "msh/EU_868"
```

### InfluxDB
Le impostazioni InfluxDB sono configurate nel file `mqtt_subscriber.py`:

```python
INFLUXDB_URL = "https://influxdb-production-7b25.up.railway.app/"
INFLUXDB_TOKEN = "your-token-here"
INFLUXDB_ORG = "mesh"
INFLUXDB_BUCKET = "mesh"
```

⚠️ **Sicurezza**: Per uso in produzione, sposta le credenziali in variabili d'ambiente:

```bash
export INFLUXDB_TOKEN="your-token-here"
export INFLUXDB_URL="your-url-here"
```

## 📁 Struttura del progetto

```
influxDBIngest/
├── mqtt_subscriber.py          # Script principale
├── Pipfile                     # Dipendenze pipenv
├── requirements.txt            # Dipendenze pip
├── protobufs/                  # Submodule con protobuf Meshtastic
└── generated/                  # Classi Python generate
    └── meshtastic/
        ├── mesh_pb2.py
        ├── mqtt_pb2.py
        └── ...
```

## 🔄 Aggiornamento protobuf

Per aggiornare agli ultimi protobuf Meshtastic:

```bash
# Aggiorna il submodule
git submodule update --remote protobufs

# Rigenera le classi Python
rm -rf generated
mkdir -p generated  
pipenv run python -m grpc_tools.protoc --python_out=generated --proto_path=protobufs protobufs/meshtastic/*.proto
```

## 🎯 Tipi di messaggio supportati

Lo script può decodificare automaticamente:

- **ServiceEnvelope**: Contenitore principale per messaggi MQTT
- **MeshPacket**: Pacchetti mesh diretti
- **Position**: Dati di posizione GPS
- **User**: Informazioni sui nodi
- **Telemetry**: Metriche del dispositivo e ambientali
- **Text Messages**: Messaggi di testo tra utenti

## 📊 Schema Dati InfluxDB

I dati vengono salvati nella measurement `meshtastic_message` con la seguente struttura:

### Tags
- `topic`: Topic MQTT completo
- `payload_type`: Tipo di payload (json, protobuf, text, binary)
- `region`: Regione Meshtastic (es. EU_868)
- `gateway`: ID del gateway
- `format`: Formato messaggio (json, c, ecc.)
- `channel`: Nome del canale
- `node_id`: ID del nodo mittente

### Fields
- **Per messaggi JSON**: Tutti i campi con prefisso `json_`
- **Per messaggi protobuf**: 
  - `protobuf_decoded`: true
  - `from_node`: ID nodo mittente
  - `to_node`: ID nodo destinatario
  - `channel_index`: Indice del canale
  - `portnum`: Tipo di porta
  - `payload_b64`: Payload in base64
  - `protobuf_json`: JSON completo decodificato
- **Per messaggi testo**: `text_message`
- **Per dati binari**: `raw_data`

### Query di esempio

```sql
-- Tutti i messaggi dell'ultima ora
SELECT * FROM meshtastic_message WHERE time >= now() - 1h

-- Messaggi di testo per canale
SELECT * FROM meshtastic_message 
WHERE payload_type = 'protobuf' AND portnum = 'TEXT_MESSAGE_APP'
GROUP BY channel

-- Statistiche per nodo
SELECT count(*) FROM meshtastic_message 
WHERE time >= now() - 24h 
GROUP BY node_id
```

## 📋 Dipendenze

- `paho-mqtt`: Client MQTT
- `protobuf`: Libreria Protocol Buffers di Google
- `grpcio-tools`: Tool per generare classi Python dai .proto
- `influxdb-client`: Client ufficiale InfluxDB v2

## 🐛 Troubleshooting

**Errore "protobuf non disponibile":**
```bash
pipenv install protobuf grpcio-tools
```

**Errore "generated module not found":**
```bash
# Rigenera le classi
pipenv run python -m grpc_tools.protoc --python_out=generated --proto_path=protobufs protobufs/meshtastic/*.proto
```

**Submodule vuoto:**
```bash
git submodule update --init --recursive
```

**Test InfluxDB fallisce:**
```bash
# Verifica le credenziali InfluxDB nel file mqtt_subscriber.py
# Controlla che il bucket e l'organizzazione esistano
# Testa la connessione manualmente:
pipenv run python mqtt_subscriber.py --test
```

## 📚 Link utili

- [Repository Protobuf Meshtastic](https://github.com/meshtastic/protobufs)
- [Documentazione Meshtastic](https://meshtastic.org)
- [Specifiche MQTT Meshtastic](https://meshtastic.org/docs/software/mqtt/)

---

Premi `Ctrl+C` per interrompere lo script.
