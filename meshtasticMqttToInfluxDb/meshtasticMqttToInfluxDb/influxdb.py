from config import config

try:
    from influxdb_client import InfluxDBClient, Point
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
    print("✅ InfluxDB library disponibile!")
except ImportError as e:
    INFLUXDB_AVAILABLE = False
    print(f"⚠️  InfluxDB library non disponibile: {e}")
    print("💡 Installa con: pipenv install influxdb-client")



class InfluxdbClient:
    def __init__(self):
        self.influx_client = None
        self.write_api = None

    def init_influxdb(self):
        if not INFLUXDB_AVAILABLE:
            print("⚠️  InfluxDB non disponibile, i dati non verranno salvati")
            return False

        url = f"{config['INFLUXDB_HOST']}:{config['INFLUXDB_PORT']}"
        self.influx_client = InfluxDBClient(url=url, token=config['INFLUXDB_TOKEN'])
        # Testa la connessione
        health = self.influx_client.health()
        if health.status == "pass":
            print(f"✅ Connesso a InfluxDB: {url}")
            self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
            return True
        else:
            print(f"❌ InfluxDB non disponibile: {health.message}")
            raise Exception(f"❌ InfluxDB non disponibile: {health.message}")
            return False

