"""
Test per il modulo proto_decode.py
"""
import pytest
import sys
import os
import json
    
from proto_decode import get_available_protos
from proto_decode import decode_protobuf
import proto_decode
from meshtastic import mqtt_pb2

from mqtt_subscriber import decode_protobuf as decode_protobuf_mqtt

class TestGetAvailableProtos:
    """Test per la funzione get_available_protos"""

    def test_get_available_protos_returns_dict(self):
        """Testa che la funzione restituisca un dizionario"""
        result = get_available_protos()
        for k,v in result.items():
            print(f"🔍 {k}: {v}")
        assert isinstance(result, dict), "La funzione deve restituire un dizionario"

    def test_decode(self):
        data =  b'\nS\r\xe8v\x0c\xba\x15\xff\xff\xff\xff""\x08C\x12\x1c\r\x13i\x00\x00\x12\x15\x08e\x15o\x12\x87@\x1d\xfa\xc5r@%\x0fy\x1a@(\x93\xd2\x01H\x015O\xd9\xd6$=WL\xc0hE\x00\x00\xe8@H\x03`\xfb\xff\xff\xff\xff\xff\xff\xff\xff\x01x\x03\x98\x01\xe8\x01\xa8\x01\x01\x12\nMeshPodere\x1a\t!ba6a665c'
        res = decode_protobuf(data)
        print(f"🔍 Risultato: {json.dumps(res, indent=2, ensure_ascii=False)}")
        assert res is not None, "La funzione deve restituire un dizionario"
    
    def test_decode_single(self):
        data =  b'\nS\r\xe8v\x0c\xba\x15\xff\xff\xff\xff""\x08C\x12\x1c\r\x13i\x00\x00\x12\x15\x08e\x15o\x12\x87@\x1d\xfa\xc5r@%\x0fy\x1a@(\x93\xd2\x01H\x015O\xd9\xd6$=WL\xc0hE\x00\x00\xe8@H\x03`\xfb\xff\xff\xff\xff\xff\xff\xff\xff\x01x\x03\x98\x01\xe8\x01\xa8\x01\x01\x12\nMeshPodere\x1a\t!ba6a665c'
        res = proto_decode.decode_protobuf_single(data)
        print(f"🔍 Risultato: {json.dumps(res, indent=2, ensure_ascii=False)}")
        assert res is not None, "La funzione deve restituire un dizionario"
    
    def test_decode_protobuf_enhanced(self):
        data =  b'\nS\r\xe8v\x0c\xba\x15\xff\xff\xff\xff""\x08C\x12\x1c\r\x13i\x00\x00\x12\x15\x08e\x15o\x12\x87@\x1d\xfa\xc5r@%\x0fy\x1a@(\x93\xd2\x01H\x015O\xd9\xd6$=WL\xc0hE\x00\x00\xe8@H\x03`\xfb\xff\xff\xff\xff\xff\xff\xff\xff\x01x\x03\x98\x01\xe8\x01\xa8\x01\x01\x12\nMeshPodere\x1a\t!ba6a665c'
        res = proto_decode.decode_protobuf_enhanced(data)
        print(f"🔍 Risultato: {json.dumps(res, indent=2, ensure_ascii=False)}")
        assert res is not None, "La funzione deve restituire un dizionario"
    
    
     

    # def test_get_available_protos_not_empty(self):
    #     """Testa che il dizionario restituito non sia vuoto"""
    #     result = get_available_protos()
    #     assert len(result) > 0, "Il dizionario deve contenere almeno un protobuf"

    # def test_protobuf_classes_have_descriptor(self):
    #     """Testa che tutte le classi abbiano un DESCRIPTOR"""
    #     result = get_available_protos()
    #     for name, proto_class in result.items():
    #         assert hasattr(proto_class, 'DESCRIPTOR'), f"La classe {name} deve avere un DESCRIPTOR"
    #         assert hasattr(proto_class.DESCRIPTOR, 'name'), f"Il DESCRIPTOR di {name} deve avere un nome"

    # def test_known_protobuf_classes_present(self):
    #     """Testa che alcune classi protobuf note siano presenti"""
    #     result = get_available_protos()
        
    #     # Verifica che ci siano alcune classi che ci aspettiamo
    #     expected_classes = [
    #         'Position',      # da mesh_pb2
    #         'User',          # da mesh_pb2
    #         'MeshPacket',    # da mesh_pb2
    #         'Telemetry',     # da telemetry_pb2
    #         'DeviceMetrics', # da telemetry_pb2
    #     ]
        
    #     for expected_class in expected_classes:
    #         assert expected_class in result, f"La classe {expected_class} dovrebbe essere presente nei protobuf"

    # def test_protobuf_class_names_are_strings(self):
    #     """Testa che i nomi delle chiavi siano stringhe"""
    #     result = get_available_protos()
    #     for name in result.keys():
    #         assert isinstance(name, str), f"Il nome {name} deve essere una stringa"

    # def test_protobuf_classes_are_callable(self):
    #     """Testa che le classi protobuf siano callable (possano essere istanziate)"""
    #     result = get_available_protos()
    #     for name, proto_class in result.items():
    #         assert callable(proto_class), f"La classe {name} deve essere callable"

    # @pytest.mark.slow
    # def test_can_instantiate_protobuf_classes(self):
    #     """Testa che sia possibile istanziare le classi protobuf"""
    #     result = get_available_protos()
        
    #     # Testa alcune classi specifiche
    #     test_classes = ['Position', 'User', 'Telemetry']
        
    #     for class_name in test_classes:
    #         if class_name in result:
    #             proto_class = result[class_name]
    #             try:
    #                 instance = proto_class()
    #                 assert instance is not None, f"Dovrebbe essere possibile istanziare {class_name}"
    #             except Exception as e:
    #                 pytest.fail(f"Errore nell'istanziazione di {class_name}: {e}")

    # def test_function_handles_import_errors_gracefully(self):
    #     """Testa che la funzione gestisca gli errori di importazione correttamente"""
    #     # Questo test verifica che la funzione non sollevi eccezioni
    #     # anche se ci sono problemi con alcuni moduli
    #     try:
    #         result = get_available_protos()
    #         assert isinstance(result, dict)
    #     except Exception as e:
    #         pytest.fail(f"La funzione non dovrebbe sollevare eccezioni: {e}")

    # def test_no_duplicate_protobuf_names(self):
    #     """Testa che non ci siano nomi di protobuf duplicati"""
    #     result = get_available_protos()
        
    #     # Conta le occorrenze di ogni nome
    #     names = list(result.keys())
    #     unique_names = set(names)
        
    #     assert len(names) == len(unique_names), "Non dovrebbero esserci nomi di protobuf duplicati"
