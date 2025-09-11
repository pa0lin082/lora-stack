import sys
import os
import json
import inspect
import base64
from google.protobuf.message import DecodeError
from google.protobuf import message
from google.protobuf import message as _message
from google.protobuf.json_format import MessageToDict, MessageToJson

sys.path.append(f'{os.path.dirname(__file__)}/generated')
import meshtastic

def get_available_protos():

    """
    Restituisce un dizionario di tutti i protobuf disponibili per il decoding.
    
    Returns:
        dict: Dizionario con formato {nome_protobuf: classe_protobuf}
    """
    import glob
    import os
    import importlib
    
    protos = {}

    
    # Percorso ai file protobuf generati
    proto_path = os.path.join(os.path.dirname(__file__), 'generated', 'meshtastic')
    
    # Trova tutti i file *_pb2.py
    proto_files = glob.glob(os.path.join(proto_path, '*_pb2.py'))
    
    for proto_file in proto_files:
        module_name = os.path.basename(proto_file).replace('.py', '')

        try:
            module_to_import = f'generated.meshtastic.{module_name}'
            module = importlib.import_module(module_to_import)
            
            # Trova tutte le classi di messaggi nel modulo
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
             
                # Verifica se è una classe di messaggio protobuf
                if inspect.isclass(attr) and issubclass(attr, _message.Message):
                    protos[attr.__name__] = attr
                    
        except ImportError as e:
            print(f"Errore nell'importazione di {module_name}: {e}")
            continue
    
    return protos
protos_map = get_available_protos()

def decode_protobuf_single(data, proto_name=None):
    """
    Decodifica un singolo protobuf usando il tipo specificato o provando tutti i tipi
    """
    if proto_name and proto_name in protos_map:
        # Prova solo il tipo specificato
        try:
            schema = protos_map[proto_name]()
            schema.ParseFromString(data)
            decoded_dict = MessageToDict(schema)
            if decoded_dict:
                return decoded_dict, proto_name
        except Exception as e:
            print(f"❌ Errore nella decodifica di {proto_name}: {e}")
            return None, None
    else:
        # Prova tutti i tipi
        for k, v in protos_map.items():
            try:
                schema = v()
                schema.ParseFromString(data)
                decoded_dict = MessageToDict(schema)
                if decoded_dict:
                    return decoded_dict, k
            except Exception as e:
                continue

    return None, None

def decode_protobuf_enhanced(data, depth=0, max_depth=3):
        
    if depth > max_depth:
        print(f"⚠️ Massima profondità di ricorsione raggiunta ({max_depth})")
        return None

    indent = "  " * depth

    # Se i dati sono in base64, decodificali
    if isinstance(data, str):
        try:
            data = base64.b64decode(data)
        except Exception as e:
            print(f"❌ Errore nel decodificare base64: {e}")
            return None

    # Decodifica il protobuf principale
    decoded, proto_type = decode_protobuf_single(data)
    if not decoded:
        print(f"❌ Impossibile decodificare i dati")
        return None
    else:
        decoded["__proto_type__"] = proto_type

    result = check_or_decode(decoded)
    return result

def check_or_decode(data):
    if isinstance(data, dict):
        if 'portnum' in data and 'payload' in data:
            if data['portnum'] in ['TEXT_MESSAGE_APP', 'RANGE_TEST_APP']:
                payload_decoded = base64.b64decode(data['payload']).decode('utf-8')
            else:
                payload_decoded = decode_protobuf_enhanced(data['payload'])
            data.update({"payload_decoded": payload_decoded})
            return data
        else:
            for key, value in data.items():
                data[key] = check_or_decode(value)
        return data
    else:
        return data

def decode_protobuf(data):
    """
    Funzione principale per la decodifica protobuf con navigazione ricorsiva
    """
    return decode_protobuf_enhanced(data)

def is_likely_protobuf(data):
    """
    Verifica se i dati potrebbero essere un messaggio protobuf.
    Controlla alcuni pattern comuni nei messaggi protobuf.
    """
    if len(data) < 2:
        return False
    
    # I messaggi protobuf spesso iniziano con determinati pattern
    # Questo è un controllo euristico, non perfetto
    first_byte = data[0]
    
    # Field number e wire type pattern (varint è comune)
    if first_byte & 0x7 in [0, 1, 2, 5]:  # wire types comuni
        return True
    
    # Controlla se contiene principalmente byte stampabili (meno probabile per protobuf)
    try:
        data.decode('utf-8')
        return False  # Se decodifica come UTF-8, probabilmente non è protobuf
    except UnicodeDecodeError:
        return True
    
