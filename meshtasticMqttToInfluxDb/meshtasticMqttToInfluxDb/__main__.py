#!/usr/bin/env python3
"""
Script per sottoscriversi al server MQTT Meshtastic e stampare ogni pacchetto ricevuto.
"""
from config import config
import sys

import json
import time
from datetime import datetime, timezone
import base64
import argparse
import proto_decode
from mqtt import MqttClient
from influxdb import InfluxdbClient
from utils import print_json, get_node_id, get_utc_timestamp, timestamp_to_utc_datetime
from influxdb_client import InfluxDBClient, Point


def parse_mqtt_payload(payload_bytes):
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
        json_data = json.loads(text)
        info["type"] = "json"
        info["content"] = json_data
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
        result = proto_decode.decode_protobuf(payload_bytes)
        info["type"] = "protobuf"
        info["content"] = result
        return info
    else:
        info["type"] = "binary"
        info["content"] = payload_bytes
        return info
    
    # Informazioni generali sui dati binari
    info["hex"] = payload_bytes.hex()
    info["base64"] = base64.b64encode(payload_bytes).decode('ascii')
    
    return info

def is_meshtastic_json_mqtt_message_callback(data):
    """
    Verifica se il messaggio è un messaggio JSON di Meshtastic.
    """
    if isinstance(data, dict) and 'type' in data and 'from' in data and 'to' in data and 'timestamp' in data:
        return True
    return False

def prepare_influxdb_point(data, timestamp=None):
    point_dict = None
    # Gestisci i diversi tipi di dati
    if is_meshtastic_json_mqtt_message_callback(data): 
        point_dict = {}
        sender_id = data['sender']
        from_node_id = get_node_id(data['from'])
        to_node_id = get_node_id(data['to'])

        # Converte il timestamp in datetime UTC usando la funzione di utilità
        point_dict['measurement'] = data['type'] 
        point_dict['time'] = timestamp_to_utc_datetime(data['timestamp'])
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
                point_dict['measurement'] = 'custom_metrics'
                for metric in data['payload']['metrics']:
                    point_dict['fields'][metric["name"]] = metric["value"]
            else:
                print(f"Recived text message: {print_json(data)}")
        else:   
            print(f"skipping message type: {data['type'] or 'unknown'}")
            # print(f"💾 Unknown type: {data['type']} \ndata: {json.dumps(data, indent=2, ensure_ascii=False)} \n point_dict: {json.dumps(point_dict, indent=2, ensure_ascii=False)}")
            point_dict = None
    else:
        print(f"❌ try_to_import_message: data non è un messaggio JSON di Meshtastic")
        return
   
    # print(f"📨 try_to_import_message: point_dict:{print_json(point_dict)}")
   
    # Converti tutti i campi in point_dict['fields'] che sono float o integer in float
    if point_dict and 'fields' in point_dict:
        for key, value in point_dict['fields'].items():
            if isinstance(value, (int, float)):
                point_dict['fields'][key] = float(value)

                
    return point_dict

def try_to_import_message( data, timestamp=None):
    """
    Scrive i dati decodificati in InfluxDB.
    """
    point_dict = prepare_influxdb_point(data, timestamp)
    if point_dict is None:
        return

    share_poit_for_home_assistant(point_dict)

    if args.dry_run:
        # print(f"🚀 try_to_import_message dry-run -> point_dict: \n{print_json(point_dict)}")
        return
    
    
    try:
        point = Point.from_dict(point_dict)
        # InfluxDB richiede sempre timestamp in UTC
        influxdb_client.write_api.write(bucket=config['INFLUXDB_BUCKET'], org=config['INFLUXDB_ORG'], record=point) 
        print(f"💾 Point written in InfluxDB: {point}")
    except Exception as e:
        print(e)
        print(f"❌ Errore scrittura InfluxDB: {e} ")
        # Debug: stampa il point per vedere cosa è andato storto
        print(f"🔍 Debug point: {point} \n data: {print_json(point_dict)}")

    return

def share_poit_for_home_assistant(point_dict):
    """
    Condividi il punto per Home Assistant.
    """
    print(f"🔍 share_poit_for_home_assistant: {point_dict}")

    node_id = point_dict['tags']['node_id']

    if point_dict['measurement'] in ['telemetry', 'custom_metrics']:
        for key, value in point_dict['fields'].items():
            topic = f"homeassitant/sensor/{node_id}/{key}"
            # print(f"🔍 topic: {topic} value: {value}")
            mqtt_client.publish(topic, value)
        

    return

def on_mqtt_message_callback(msg):
    """Callback chiamata quando viene ricevuto un messaggio."""
    timestamp = get_utc_timestamp()
    print(f"📨 on_mqtt_message_callback: timestamp:{timestamp} ")
    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    topic = msg.topic
    print(f"\n📨 [{timestamp_str}] Topic: {topic}")
    print(f"📨 msg: {msg}")

    # Analizza il tipo di payload
    msg_parsed = parse_mqtt_payload(msg.payload)
    
    if msg_parsed['type'] == 'json':
        try_to_import_message(msg_parsed['content'], timestamp)
    elif msg_parsed['type'] == 'text':
        print(f"📦 skip msg type text {print_json(msg_parsed)}")
        pass
        
    elif msg_parsed['type'] == 'protobuf':
        print(f"📦 skip msg type protobuf")
        pass
    else:  # binary
        print(f"📦 skip msg type binary")
        pass
    
    
    print("-" * 80)

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
    global args, influxdb_client, mqtt_client

    args = parse_arguments()
    # Modalità test
    if args.test:
        result = test_influxdb()
        sys.exit(0 if result else 1)
    
    if args.dry_run:
        print("🚀 Modalità dry-run: non salverò i dati in InfluxDB")

    influxdb_client = InfluxdbClient()

    influx_success = influxdb_client.init_influxdb()
    if influx_success:
        print(f"📊 Bucket: {config['INFLUXDB_BUCKET']} | Org: {config['INFLUXDB_ORG']}")
    print("-" * 80)

    mqtt_client = MqttClient(on_message_callback=on_mqtt_message_callback)
    mqtt_client.connect()
    mqtt_client.start_loop()

if __name__ == "__main__":
    main()
