#!/usr/bin/env python3
"""
Modulo per gestire le connessioni e operazioni MQTT.
Fornisce una classe pulita e riutilizzabile per la gestione di MQTT.
"""

import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime, timezone
from typing import Callable, Optional
from config import config


class MqttClient:
    """
    Classe per gestire le connessioni e operazioni MQTT in modo pulito e organizzato.
    """
    
    def __init__(self, on_message_callback: Optional[Callable] = None):
        """
        Inizializza il client MQTT.
        
        Args:
            on_message_callback: Funzione da chiamare quando arriva un messaggio
        """
        self.client = None
        self.is_connected = False
        self.on_message_callback = on_message_callback
        
        # Configurazione da config
        self.host = config['MQTT_HOST']
        self.port = config['MQTT_PORT']
        self.username = config['MQTT_USERNAME']
        self.password = config['MQTT_PASSWORD']
        self.root_topic = config['MQTT_ROOT_TOPIC']
        
        self._setup_client()
    
    def _setup_client(self):
        """Configura il client MQTT con callback e credenziali."""
        self.client = mqtt.Client()
        
        # Imposta credenziali
        self.client.username_pw_set(self.username, self.password)
        
        # Assegna i callback
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_log = self._on_log
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback chiamata quando il client si connette al broker MQTT."""
        if rc == 0:
            self.is_connected = True
            print(f"✅ Connesso al broker MQTT {self.host}:{self.port}")
            
            # Sottoscriviti a tutti i topic sotto il root
            topic = f"{self.root_topic}/#"
            client.subscribe(topic)
            print(f"📡 Sottoscritto al topic: {topic}")
        else:
            self.is_connected = False
            print(f"❌ Errore di connessione MQTT. Codice: {rc}")
            self._print_connection_error(rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback chiamata quando il client si disconnette dal broker."""
        self.is_connected = False
        print(f"🔌 Disconnesso dal broker MQTT. Codice: {rc}")
        
        if rc != 0:
            print("⚠️  Disconnessione inattesa! Tentativo di riconnessione...")
    
    def _on_message(self, client, userdata, msg):
        print(f"📨 msg: {msg}")
        """Callback chiamata quando viene ricevuto un messaggio."""
        try:
            
            
            print(f"📨 Messaggio ricevuto su {msg.topic}")
            
            # Chiama il callback personalizzato se fornito
            if self.on_message_callback:
                try:
                    self.on_message_callback(msg)
                except Exception as e:
                    print(f"❌ Errore nel callback personalizzato: {e}")
            
        except UnicodeDecodeError:
            print(f"⚠️  Impossibile decodificare il messaggio su {msg.topic}")
        except Exception as e:
            print(f"❌ Errore nella gestione del messaggio: {e}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback chiamata quando la sottoscrizione è confermata."""
        print(f"✅ Sottoscrizione confermata. QoS: {granted_qos}")
    
    def _on_log(self, client, userdata, level, buf):
        """Callback per i log del client MQTT (opzionale)."""
        # Decommentare per debug dettagliato
        # print(f"🔍 MQTT Log: {buf}")
        pass
    
    def _print_connection_error(self, rc):
        """Stampa dettagli dell'errore di connessione."""
        error_messages = {
            1: "Versione del protocollo non corretta",
            2: "Identificatore client non valido",
            3: "Server non disponibile",
            4: "Username o password non validi",
            5: "Non autorizzato"
        }
        
        if rc in error_messages:
            print(f"💡 Dettaglio errore: {error_messages[rc]}")
    
    def connect(self) -> bool:
        """
        Connette al broker MQTT.
        
        Returns:
            bool: True se la connessione è riuscita, False altrimenti
        """
        try:
            print("-" * 80)
            print(f"🔄 Tentativo di connessione a {self.host}:{self.port}...")
            self.client.connect(self.host, self.port, 60)

            print("🚀 Avvio del client MQTT Meshtastic...")
            print(f"🌐 Server: {config['MQTT_HOST']}:{config['MQTT_PORT']}")
            print(f"👤 Username: {config['MQTT_USERNAME']}")
            print(f"📡 Topic root: {config['MQTT_ROOT_TOPIC']}")
            print("-" * 80)

            return True
        except Exception as e:
            print(f"❌ Errore durante la connessione MQTT: {e}")
            return False
    
    def disconnect(self):
        """Disconnette dal broker MQTT."""
        if self.client and self.is_connected:
            print("🔌 Disconnessione dal broker MQTT...")
            self.client.disconnect()
    
    def start_loop(self):
        """Avvia il loop principale per ricevere messaggi."""
        if not self.client:
            print("❌ Client MQTT non inizializzato!")
            return False
        
        try:
            print("⏳ Avvio del loop di ricezione messaggi...")
            print("💡 Premi Ctrl+C per interrompere")
            print("=" * 80)
            
            self.client.loop_forever()
            return True
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Interruzione da tastiera ricevuta")
            self.disconnect()
        except Exception as e:
            print(f"❌ Errore nel loop MQTT: {e}")
            return False
    
    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        """
        Pubblica un messaggio su un topic.
        
        Args:
            topic: Topic su cui pubblicare
            payload: Contenuto del messaggio
            qos: Quality of Service (0, 1, 2)
            retain: Se il messaggio deve essere retained
            
        Returns:
            bool: True se la pubblicazione è riuscita
        """
        if not self.is_connected:
            print("❌ Non connesso al broker MQTT!")
            return False
        
        try:
            result = self.client.publish(topic, payload, qos, retain)
            if result.rc == 0:
                # print(f"📤 Messaggio pubblicato su {topic}")
                return True
            else:
                print(f"❌ Errore nella pubblicazione: {result.rc}")
                return False
        except Exception as e:
            print(f"❌ Errore durante la pubblicazione: {e}")
            return False
    
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """
        Sottoscrive a un topic specifico.
        
        Args:
            topic: Topic a cui sottoscriversi
            qos: Quality of Service
            
        Returns:
            bool: True se la sottoscrizione è riuscita
        """
        if not self.is_connected:
            print("❌ Non connesso al broker MQTT!")
            return False
        
        try:
            result = self.client.subscribe(topic, qos)
            if result[0] == 0:
                print(f"📡 Sottoscritto al topic: {topic}")
                return True
            else:
                print(f"❌ Errore nella sottoscrizione: {result[0]}")
                return False
        except Exception as e:
            print(f"❌ Errore durante la sottoscrizione: {e}")
            return False
    
    def get_status(self) -> dict:
        """
        Restituisce lo stato attuale del client.
        
        Returns:
            dict: Dizionario con informazioni di stato
        """
        return {
            'connected': self.is_connected,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'root_topic': self.root_topic
        }
    
    def __enter__(self):
        """Supporto per context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automatico quando si esce dal context manager."""
        self.disconnect()
