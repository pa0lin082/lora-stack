#!/usr/bin/env python3
"""
Script per sottoscriversi al server MQTT Meshtastic e stampare ogni pacchetto ricevuto.
"""
from config import config
import sys

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone
import base64
import argparse
import sys
import proto_decode

# InfluxDB imports
try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
    print("✅ InfluxDB library disponibile!")
except ImportError as e:
    INFLUXDB_AVAILABLE = False
    print(f"⚠️  InfluxDB library non disponibile: {e}")
    print("💡 Installa con: pipenv install influxdb-client")

try:
    from google.protobuf.message import DecodeError
    from google.protobuf import message
    from google.protobuf.json_format import MessageToDict, MessageToJson
    
    # Import dei protobuf Meshtastic generati
    import sys
    # sys.path.append('generated')
    # sys.path.append('generated/meshtastic')
    import meshtastic
    from meshtastic import mesh_pb2
    from meshtastic import mqtt_pb2
    from meshtastic import portnums_pb2
    from meshtastic import telemetry_pb2
    from meshtastic import config_pb2
    
    PROTOBUF_AVAILABLE = True
    print("✅ Protobuf Meshtastic caricati con successo!")
except ImportError as e:
    PROTOBUF_AVAILABLE = False
    print(f"⚠️  Protobuf non disponibile: {e}")
    print("💡 Esegui: pipenv install && pipenv run python -m grpc_tools.protoc --python_out=generated --proto_path=protobufs protobufs/meshtastic/*.proto")
    sys.exit()

# Client InfluxDB globale
influx_client = None
mqtt_client = None
write_api = None
args = None


class JSONSerializerWithDatetime(json.JSONEncoder):
    """
    Serializzatore JSON personalizzato che gestisce anche i datetime.
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)

def print_json(data):
    """
    Serializza i dati in formato JSON utilizzando il serializzatore personalizzato.
    
    Args:
        data (any): I dati da serializzare.
    
    Returns:
        str: Stringa JSON dei dati serializzati.
    """
    return json.dumps(data, cls=JSONSerializerWithDatetime, indent=2, ensure_ascii=False)

def get_node_id(node_num):
    """
    Converte un NodeNum (numero intero) in un Node ID (stringa con prefisso !)
    
    Args:
        node_num (int): Il numero del nodo (es. 305419896)
    
    Returns:
        str: L'ID del nodo formattato (es. "!12345678")
    """
    return f"!{node_num:08x}"

def analyze_payload_type(payload_bytes):
    """
    Analizza il tipo di payload e restituisce informazioni utili.
    """
    info = {
        "size": len(payload_bytes),
        "type": "unknown"
    }
    
    # Prova JSON
    try:
        text = payload_bytes.decode('utf-8')
        json.loads(text)
        info["type"] = "json"
        info["content"] = text
        return info
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    
    # Prova testo normale
    try:
        text = payload_bytes.decode('utf-8')
        # Se decodifica senza errori e contiene caratteri stampabili
        if all(ord(c) < 128 and (c.isprintable() or c.isspace()) for c in text):
            info["type"] = "text"
            info["content"] = text
            return info
    except UnicodeDecodeError:
        pass
    
    # Controlla se potrebbe essere protobuf
    if proto_decode.is_likely_protobuf(payload_bytes):
        info["type"] = "protobuf"
    else:
        info["type"] = "binary"
    
    # Informazioni generali sui dati binari
    info["hex"] = payload_bytes.hex()
    info["base64"] = base64.b64encode(payload_bytes).decode('ascii')
    
    return info

def get_utc_timestamp():
    """
    Restituisce il timestamp UTC corrente come datetime UTC.
    """
    return datetime.now(timezone.utc)

def timestamp_to_utc_datetime(timestamp):
    """
    Converte un timestamp Unix in datetime UTC.
    """
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    elif isinstance(timestamp, datetime):
        # Se è già un datetime, assicurati che sia UTC
        if timestamp.tzinfo is None:
            # Se non ha timezone, assume sia UTC
            return timestamp.replace(tzinfo=timezone.utc)
        else:
            # Converte in UTC se ha un altro timezone
            return timestamp.astimezone(timezone.utc)
    else:
        # Se non è un formato riconosciuto, usa il timestamp corrente
        return get_utc_timestamp()

def init_influxdb():
    """
    Inizializza il client InfluxDB.
    """

    global write_api, influx_client
 
    if not INFLUXDB_AVAILABLE:
        print("⚠️  InfluxDB non disponibile, i dati non verranno salvati")
        return False
    
    try:
        url = f"{config['INFLUXDB_HOST']}:{config['INFLUXDB_PORT']}"
        influx_client = InfluxDBClient(
            url=url,
            token=config['INFLUXDB_TOKEN'],
            org=config['INFLUXDB_ORG']
        )
        
        # Testa la connessione
        health = influx_client.health()
        if health.status == "pass":
            print(f"✅ Connesso a InfluxDB: {config['INFLUXDB_URL']}")
            write_api = influx_client.write_api(write_options=SYNCHRONOUS)
            return True
        else:
            print(f"❌ InfluxDB non disponibile: {health.message}")
            return False
            
    except Exception as e:
        print(f"❌ Errore connessione InfluxDB: {e}")
        return False

def test_influxdb():
    """
    Modalità test: scrive alcuni record di test in InfluxDB e esce.
    """
    print("🧪 MODALITÀ TEST - Scrittura record di prova in InfluxDB")
    print("-" * 80)
    
    # Inizializza InfluxDB
    if not init_influxdb():
        print("❌ Impossibile connettersi a InfluxDB")
        return False
    
    # Crea alcuni record di test con timestamp UTC
    current_utc_timestamp = int(get_utc_timestamp().timestamp())
    
    test_records = [
        {
            "type": "nodeinfo",
            "sender": "!test1234",
            "from": 305419896,
            "to": 4294967295,
            "timestamp": current_utc_timestamp,
            "payload": {
                "id": "!test1234",
                "longname": "Test Node",
                "shortname": "TEST",
                "hardware": "T-BEAM"
            }
        },
        {
            "type": "telemetry",
            "sender": "!test5678",
            "from": 305419896,
            "to": 4294967295,
            "timestamp": current_utc_timestamp + 1,  # 1 secondo dopo
            "payload": {
                "battery_level": 85,
                "voltage": 2.3,
                "channel_utilization": 12.5,
                "air_util_tx": 2.3
            }
        }
    ]
    
    success_count = 0
    
    for i, record in enumerate(test_records, 1):
        try:
            print(f"📝 Scrittura record test {i}/{len(test_records)}: {record}")
            write_to_influxdb(record)
            success_count += 1
            time.sleep(1)  # Pausa tra le scritture
            
        except Exception as e:
            print(f"❌ Errore scrittura record {i}: {e}")
    
    print("-" * 80)
    print(f"✅ Test completato: {success_count}/{len(test_records)} record scritti con successo")
    
    if influx_client:
        influx_client.close()
        print("💾 InfluxDB disconnesso")
    
    return success_count == len(test_records)

def init_mqtt():
    """
    Inizializza il client MQTT.
    """
    global mqtt_client
    mqtt_client = mqtt.Client()

    mqtt_client.username_pw_set(config['MQTT_USERNAME'], config['MQTT_PASSWORD'])
    
    # Assegna i callback
    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message
    mqtt_client.on_subscribe = on_subscribe
    mqtt_client.on_log = on_log

    return mqtt_client

def write_to_influxdb( data, timestamp=None):
    """
    Scrive i dati decodificati in InfluxDB.
    """
   
    if not write_api:
        print(f"❌ InfluxDB write_api non disponibile")
        return
    if not influx_client:
        print(f"❌ InfluxDB influx_client non disponibile")
        return

    # print(f"Scrivo in InfluxDB:  {data} timestamp:{timestamp}")

    point_dict = None
    # Gestisci i diversi tipi di dati
    if isinstance(data, dict) and 'type' in data: 
        point_dict = {}
        sender_id = data['sender']
        from_node_id = get_node_id(data['from'])
        to_node_id = get_node_id(data['to'])


        # Converte il timestamp in datetime UTC usando la funzione di utilità
        point_dict['time'] = timestamp_to_utc_datetime(data['timestamp'])
        point_dict['measurement'] = data['type'] 
        point_dict['tags'] = {
            'gateway': sender_id,
            'node_id': from_node_id,
            'to_node_id': to_node_id
        }
        point_dict['fields'] = {
        }

    
        if data['type'] == 'telemetry':
            point_dict['fields'].update(data['payload'])
        elif data['type'] == 'nodeinfo':
            point_dict['tags'].update({
                'hardware': data['payload']['hardware'],
                'longname': data['payload']['longname'],
                'shortname': data['payload']['shortname']
            })
        elif data['type'] == 'position':
            point_dict['fields'].update(data['payload'])
        elif data['type'] == 'text':
            if data['payload'] and 'type' in data['payload'] and data['payload']['type'] == 'custom_metrics':
                for metric in data['payload']['metrics']:
                    point_dict['fields'][metric["name"]] = metric["value"]
        else:
            print(f"skipping message type: {data['type'] or 'unknown'}")
            # print(f"💾 Unknown type: {data['type']} \ndata: {json.dumps(data, indent=2, ensure_ascii=False)} \n point_dict: {json.dumps(point_dict, indent=2, ensure_ascii=False)}")
            point_dict = None
   
   
    # Converti tutti i campi in point_dict['fields'] che sono float o integer in float
    if point_dict and 'fields' in point_dict:
        for key, value in point_dict['fields'].items():
            if isinstance(value, (int, float)):
                point_dict['fields'][key] = float(value)

    if point_dict is None:
        # print(f"❌ Point non disponibile: {data}, {type(data)}")
        return
    
    try:
        if args.dry_run:
            print(f"🚀 write_to_influxdb dry-run -> point_dict: \n{print_json(point_dict)}")
            return
        point = Point.from_dict(point_dict)
        # InfluxDB richiede sempre timestamp in UTC
        write_api.write(bucket=config['INFLUXDB_BUCKET'], org=config['INFLUXDB_ORG'], record=point)
        display_time = point_dict["time"].strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"💾 Salvato in InfluxDB: {data['type']} da {data.get('sender', 'unknown')} @ {display_time}")   
        point_dict['time'] = display_time
        print(f"💾 Risultato scrittura InfluxDB: {point} \n data: {json.dumps(point_dict, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(e)
        print(f"❌ Errore scrittura InfluxDB: {e} ")
        # Debug: stampa il point per vedere cosa è andato storto
        print(f"🔍 Debug point: {point}")

    return
   

def on_connect(client, userdata, flags, rc):
    """Callback chiamata quando il client si connette al broker MQTT."""
    if rc == 0:
        print(f"✅ Connesso al broker MQTT {config['MQTT_HOST']}:{config['MQTT_PORT']}")
        # Sottoscriviti a tutti i topic sotto il root
        topic = f"{config['MQTT_ROOT_TOPIC']}/#"
        client.subscribe(topic)
        print(f"📡 Sottoscritto al topic: {topic}")
    else:
        print(f"❌ Errore di connessione. Codice: {rc}")

def on_disconnect(client, userdata, rc):
    """Callback chiamata quando il client si disconnette dal broker."""
    print(f"🔌 Disconnesso dal broker MQTT. Codice: {rc}")

def on_message(client, userdata, msg):
    """Callback chiamata quando viene ricevuto un messaggio."""
    timestamp = get_utc_timestamp()
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    topic = msg.topic
    
    print(f"\n📨 [{timestamp_str}] Topic: {topic}")
    
    # Analizza il tipo di payload
    payload_info = analyze_payload_type(msg.payload)
    
    # print(f"📊 Tipo: {payload_info['type'].upper()} | Dimensione: {payload_info['size']} bytes")
    
    data_to_save = None
    
    if payload_info['type'] == 'json':
        try:
            json_data = json.loads(payload_info['content'])
            print(f"📦 JSON: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
            data_to_save = json_data
        except json.JSONDecodeError:
            print(f"❌ JSONDecodeError Contenuto: {payload_info['content']}")
            # data_to_save = payload_info['content']
            
    elif payload_info['type'] == 'text':
        # print(f"📦 Testo: {payload_info['content']}")
        pass
        
    elif payload_info['type'] == 'protobuf':
        # print(f"🔧 PROTOBUF MESHTASTIC DETECTATO!")
        # print(f"🔧 Payload PROTOBUF:")
        # print(msg.payload)

        result = proto_decode.decode_protobuf(msg.payload)
        if result:
            print(f"📦 Payload PROTOBUF:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            data_to_save = result
        else:
            print(f"❌ Impossibile decodificare il protobuf")
        
    else:  # binary
        print(f"📦 Dati binari:")
        print(f"   Hex: {payload_info['hex'][:100]}{'...' if len(payload_info['hex']) > 100 else ''}")
        print(f"   Base64: {payload_info['base64'][:100]}{'...' if len(payload_info['base64']) > 100 else ''}")
        data_to_save = None
    
    # Salva i dati in InfluxDB
    if data_to_save is not None:
        write_to_influxdb(data_to_save, timestamp)
    
    print("-" * 80)

def on_subscribe(client, userdata, mid, granted_qos):
    """Callback chiamata quando la sottoscrizione è confermata."""
    print(f"✅ Sottoscrizione confermata. QoS: {granted_qos}")

def on_log(client, userdata, level, buf):
    """Callback per i log del client MQTT (opzionale)."""
    # Decommentare la riga seguente per vedere i log dettagliati
    # print(f"🔍 Log: {buf}")
    pass

def parse_arguments():
    """
    Parsing degli argomenti da linea di comando.
    """
    parser = argparse.ArgumentParser(
        description="MQTT Meshtastic Subscriber con InfluxDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python mqtt_subscriber.py                    # Modalità normale
  python mqtt_subscriber.py --test             # Modalità test InfluxDB
  python mqtt_subscriber.py --help             # Mostra questo aiuto

Per più informazioni consulta il README.md
        """
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Modalità test: scrive record di prova in InfluxDB e esce"
    )

    parser.add_argument(
        "--dry-run", '-d',
        action="store_true",
        help="Modalità dry-run: non salva i dati in InfluxDB"
    )
    
    parser.add_argument(
        "--version",
        action="version", 
        version="MQTT Meshtastic Subscriber v1.0.0"
    )
    
    return parser.parse_args()

def main():
    """Funzione principale."""
    global args
    args = parse_arguments()
    
    # Modalità test
    if args.test:
        result = test_influxdb()
        sys.exit(0 if result else 1)
    
    if args.dry_run:
        print("🚀 Modalità dry-run: non salverò i dati in InfluxDB")
        
    
    # Modalità normale
    print("🚀 Avvio del client MQTT Meshtastic...")
    print(f"🌐 Server: {config['MQTT_HOST']}:{config['MQTT_PORT']}")
    print(f"👤 Username: {config['MQTT_USERNAME']}")
    print(f"📡 Topic root: {config['MQTT_ROOT_TOPIC']}")
    print("-" * 80)
    
    # Inizializza InfluxDB
    print("🔧 Inizializzazione InfluxDB...")
    influx_success = init_influxdb()
    if influx_success:
        print(f"📊 Bucket: {config['INFLUXDB_BUCKET']} | Org: {config['INFLUXDB_ORG']}")
    print("-" * 80)

    # Inizializza il client MQTT
    print("🔧 Inizializzazione MQTT...")
    mqtt_client = init_mqtt()
    if mqtt_client:
        print(f"📊 Client MQTT inizializzato")
    print("-" * 80)
    
    # Crea il client MQTT
    client = mqtt_client
    
    # # Imposta le credenziali
    # client.username_pw_set(config['MQTT_USERNAME'], config['MQTT_PASSWORD'])
    
    # # Assegna i callback
    # client.on_connect = on_connect
    # client.on_disconnect = on_disconnect
    # client.on_message = on_message
    # client.on_subscribe = on_subscribe
    # client.on_log = on_log
    
    try:
        # Connessione al broker
        print(f"🔄 Tentativo di connessione a {config['MQTT_HOST']}:{config['MQTT_PORT']}...")
        mqtt_client.connect(config['MQTT_HOST'], config['MQTT_PORT'], 60)
        
        # Avvia il loop per gestire i messaggi
        print("⏳ Avvio del loop di ricezione messaggi...")
        print("💡 Premi Ctrl+C per interrompere")
        print("=" * 80)
        
        mqtt_client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Interruzione da tastiera ricevuta")
        mqtt_client.disconnect()
        if influx_client:
            influx_client.close()
            print("💾 InfluxDB disconnesso")
        print("👋 Disconnessione completata")
        
    except Exception as e:
        print(f"❌ Errore: {e} ")
        client.disconnect()
        if influx_client:
            influx_client.close()

if __name__ == "__main__":
    main()
