import json
from datetime import datetime, timezone
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
