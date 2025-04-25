"""
mqtt_client.py

Manages the MQTT SparkplugB connection lifecycle, message handling,
auto-reconnects, and publishes birth/death/location messages and metrics.

Includes a watchdog reconnect thread, command processing from NCMD/DCMD,
and TCP latency measurements.

Leverages Paho MQTT and Sparkplug B libraries, with error handling
via print_error from logger_module.
"""

import os
import sys
import socket
import ssl
import time
import threading
import datetime
import paho.mqtt.client as mqtt
from src.sql.database import flush_buffer, load_config
from src.utils.logger_module import log_trace, log_info, log_error, print_error, get_log_level_num, log_warn
from src.utils.system_info import get_uptime_seconds
from src.utils.restart import restart_script
from src.mqtt.sparkplug_utils import (
    create_birth_payload,
    get_death_payload,
    create_death_payload,
    create_location_payload,
)
import sparkplug_b as sparkplug


class AliasMap:
    Next_Server = 0
    Rebirth = 1
    Reboot = 2
    Dataset = 3
    Node_Metric0 = 4
    Node_Metric1 = 5
    Node_Metric2 = 6
    Node_Metric3 = 7
    Device_Metric0 = 8
    Device_Metric1 = 9
    Device_Metric2 = 10
    Device_Metric3 = 11
    My_Custom_Motor = 12


class SparkplugClient:
    """Handles MQTT connection, subscriptions, publishing, and metrics."""

    def __init__(self, db):
        """Initialize the Sparkplug client and connect to broker."""
        self.db = db
        self.tls_applied = False
        self.cfg = load_config(db)
        self.client = mqtt.Client(client_id=self.cfg["client_id"])
        self.client.username_pw_set(self.cfg.get("username"), self.cfg.get("password"))
        self.apply_security_settings()

        if self.client._tls_insecure:
            log_warn("[TLS] Insecure TLS mode enabled. Skipping cert check.")
        else:
            log_info("[TLS] Using strict certificate validation.")

        death_byte_array = bytearray(
            get_death_payload().SerializeToString()
        )
        self.client.will_set(
            f"spBv1.0/{self.cfg['group_id']}/NDEATH/{self.cfg['node_id']}",
            death_byte_array,
            0,
            False,
        )

        self.is_connected = False
        self.last_connection_time = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        self.messages_sent = 0
        self.reconnect_count = 0
        self.latency_ms = self.get_tcp_latency()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self._start_reconnect_watchdog()
        
        log_info(f"MQTT Username: {self.cfg.get('username')}")
        log_info(f"MQTT Password: {self.cfg.get('password')}")
        log_info(f"Connecting to {self.cfg['broker']}:{self.cfg['port']} as {self.cfg['username']}")

    def _setup_auth(self):
        """
        Configure MQTT username and password for broker authentication.
    
        Credentials are loaded from environment variables or the current config.
        If not present, anonymous access is attempted.
        """
        try:
            # Prefer environment variables for sensitive values
            username = os.environ.get("MQTT_USERNAME") or self.cfg.get("username")
            password = os.environ.get("MQTT_PASSWORD") or self.cfg.get("password")
    
            if username and password:
                self.client.username_pw_set(username, password)
                if get_log_level_num() <= 20:
                    log_info(f"[MQTT] Using username: {username}")
            else:
                log_warn("[MQTT] No username/password provided — anonymous mode.")
    
        except Exception as e:
            print_error("_setup_auth", e)

    
    def apply_security_settings(self):
        """
        Apply TLS/SSL settings to the MQTT client based on user configuration.
        Modes supported:
            - none: No TLS
            - tls_insecure: TLS without cert verification
            - tls_with_ca: TLS with CA cert only
            - tls_with_cert: TLS with CA + client cert/key
        """
        try:
            tls_mode = self.cfg.get("tls_mode", "none")
        
            if getattr(self.client, "_ssl_context", None) is not None:
                log_warn("[TLS] SSL already configured. Skipping re-application.")
                return
        
            if tls_mode == "none":
                log_info("[TLS] No encryption (TCP mode).")
            elif tls_mode == "tls_insecure":
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)
                self.client.tls_insecure_set(True)
                log_warn("[TLS] Insecure TLS mode enabled. Skipping cert check.")
            elif tls_mode == "tls_with_ca":
                ca_path = "certs/ca.crt"
                if not os.path.exists(ca_path):
                    log_error(f"[TLS] Missing CA cert: {ca_path}")
                    return
                self.client.tls_set(ca_certs=ca_path, cert_reqs=ssl.CERT_REQUIRED)
                log_info("[TLS] TLS with CA cert only.")
            elif tls_mode == "tls_with_cert":
                ca = "certs/ca.crt"
                crt = "certs/client.crt"
                key = "certs/client.key"
                if not all(map(os.path.exists, [ca, crt, key])):
                    log_error("[TLS] One or more cert/key files missing.")
                    log_error(f"CA: {ca}, CERT: {crt}, KEY: {key}")
                    return
                self.client.tls_set(
                    ca_certs=ca,
                    certfile=crt,
                    keyfile=key,
                    cert_reqs=ssl.CERT_REQUIRED
                )
                log_info("[TLS] TLS with client certificate auth.")
            self.tls_applied = True
        except Exception as e:
            print_error("apply_security_settings", e)


    def reload_connection(self):
        """
        Reload MQTT configuration and perform a clean reconnect.
        Used after TLS or config settings change via API.
        """
        try:
            log_info("[MQTT] Reloading MQTT connection...")
    
            # Gracefully stop any active connection
            self.client.loop_stop()
            self.client.disconnect()
    
            # Delegate everything else to self.connect()
            self.connect()
    
            log_info("[MQTT] Successfully reconnected with updated config.")
    
        except Exception as e:
            print_error("reload_connection", e)

    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT successful connection event."""
        try:
            if rc == 0:
                if get_log_level_num() <= 20:
                    log_info("[MQTT] Connected successfully")
                if get_log_level_num() <= 5:
                    log_trace(f"[MQTT] Connected to broker {self.cfg['broker']}:{self.cfg['port']}")
                self.last_connection_time = datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if get_log_level_num() <= 5:
                    log_trace("Last connection time: " + self.last_connection_time)
                self.is_connected = True
                self.publish_birth()
                time.sleep(2)
                self.publish_device_birth()
                time.sleep(2)
                flush_buffer(self.db, self)
            else:
                log_error(f"[MQTT] Failed to connect, return code {rc}")

            client.subscribe(
                f"spBv1.0/{self.get_group_id()}/NCMD/{self.get_node_id()}/#"
            )
            client.subscribe(
                f"spBv1.0/{self.get_group_id()}/DCMD/{self.get_node_id()}/#"
            )
        except Exception as e:
            print_error("_on_connect", e)

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection event."""
        log_error(f"[MQTT] Disconnected with return code {rc}")
        self.is_connected = False
        self.reconnect_count += 1

    def _on_message(client, userdata, msg, rc):
        """Handle inbound MQTT messages and execute control actions."""
        if get_log_level_num() <= 5:
            log_trace("_on_message recieved a message")
            log_trace("rc: " + str(rc))
            log_trace("payload: " + str(rc.payload))
        try:
            tokens = rc.topic.split("/")
            if (
                tokens[0] == "spBv1.0"
                and tokens[1] == client.cfg["group_id"]
                and tokens[2] in ("NCMD", "DCMD")
                and tokens[3] == client.cfg["node_id"]
            ):
                inbound_payload = sparkplug.Payload()
                inbound_payload.ParseFromString(rc.payload)
                for metric in inbound_payload.metrics:
                    if metric.name == "Node Control/Rebirth" or metric.alias == AliasMap.Rebirth:
                        client.publish_birth()
                        if get_log_level_num() <= 5:
                            log_trace("Publish birth from Node Control/Rebirth command")
                    elif metric.name == "Node Control/Reboot" or metric.alias == AliasMap.Reboot:
                        restart_script()
                        if get_log_level_num() <= 5:
                            log_trace("restart_script() from Node Control/Reboot command")
        except Exception as e:
            print_error("_on_message", e)

    def is_socket_connected(self):
        """Check whether the MQTT socket is still alive."""
        try:
            if self.client._sock:
                self.client._sock.send(b"")
                return True
        except Exception as e:
            log_error(f"[MQTT] TLS socket error: {e}")
            return False
        return False

    def _start_reconnect_watchdog(self):
        """
        Launch a background thread that monitors MQTT socket health and reconnects
        with proper birth/DBIRTH and buffer recovery.
        """
        def watchdog():
            while True:
                try:
                    self.latency_ms = self.get_tcp_latency()
    
                    if not self.is_socket_connected():
                        log_info("[MQTT] Connection lost. Reconnecting...")
    
                        # Stop any active loop and disconnect safely
                        try:
                            self.client.reconnect()
                            log_info("[MQTT] Reconnected using reconnect()")
                        except Exception as e:
                            log_warn(f"[MQTT] Disconnect failed: {e}")
    
                    #     # Reload config in case it's been updated
                    #     self.cfg = load_config(self.db)
    
                    #     # Apply updated TLS settings
                    #     self.apply_security_settings()
    
                    #     # Setup MQTT authentication again
                    #     self._setup_auth()
    
                    #     log_info("[MQTT] Initiating reconnection...")
                    #     self.client.connect(
                    #         self.cfg["broker"], self.cfg["port"], keepalive=60
                    #     )
                    #     self.client.loop_start()
    
                    #     time.sleep(2)  # Let the connection settle
    
                    #     # Check connection again
                    #     if self.client.is_connected():
                    #         log_info("[MQTT] Successfully reconnected.")
    
                    #         # Republish NBIRTH and DBIRTH to reset broker state
                    #         try:
                    #             self.publish_birth()
                    #             time.sleep(1)
                    #             self.publish_device_birth()
                    #             time.sleep(1)
                    #             flush_buffer(self.db, self)
                    #         except Exception as e:
                    #             print_error("watchdog_birth_publish", e)
    
                    #         self.is_connected = True
                    #     else:
                    #         log_warn("[MQTT] Reconnect attempt failed.")
                    #         self.is_connected = False
                    # else:
                    #     if get_log_level_num() <= 5:
                    #         log_trace("[MQTT] Watchdog: Connection is healthy.")
                    #     self.is_connected = True
    
                except Exception as e:
                    print_error("reconnect_watchdog", e)
    
                time.sleep(5)
    
        thread = threading.Thread(target=watchdog, daemon=True)
        thread.start()


    def connect(self):
        """
        Connect to the MQTT broker using current configuration.
        This method is reused for reconnects and reloads.
        """
        try:
            log_info("[MQTT] Initiating connection...")
            
            # Reload config (optional — useful if from .env or updated DB)
            self.cfg = load_config(self.db)
            
    
            # Apply security settings like TLS or certs
            self.apply_security_settings()
    
            # Apply username/password if available
            self._setup_auth()
            
            # Enable MQTT library internal debug logs
            self.client.enable_logger()
    
            # Log connection attempt details
            log_info(
                f"Connecting to {self.cfg['broker']}:{self.cfg['port']} "
                f"as {self.cfg.get('username') or '[anonymous]'}"
            )
    
            # Initiate actual connection
            self.client.connect(
                self.cfg["broker"], self.cfg["port"], keepalive=60
            )
    
            self.client.loop_start()
    
        except Exception as e:
            print_error("connect", e)

    def disconnect(self):
        """Stop loop and disconnect MQTT client."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            print_error("disconnect", e)
    
    def reload_cert(self):
        """
        Reload MQTT TLS certificates from /certs folder.
        Called after uploading new certs.
        """
        try:
            self.client.tls_set(
                ca_certs="certs/ca.crt",
                certfile="certs/client.crt",
                keyfile="certs/client.key",
                tls_version=ssl.PROTOCOL_TLSv1_2,
            )
            self.client.tls_insecure_set(False)
            log_info("Reloaded MQTT TLS certificates.")
        except Exception as e:
            print_error("reload_cert", e)

    def publish(self, topic, payload, qos=0, retain=False, is_historical=False):
        """Publish a message to the MQTT broker."""
        try:
            if not self.is_connected:
                log_warn("[MQTT] Tried to publish while disconnected.")
                return
            self.client.publish(topic, payload, qos=qos, retain=retain)
            self.messages_sent += 1
        except Exception as e:
            print_error("publish", e)

    def publish_birth(self):
        """Send NBIRTH payload."""
        try:
            topic = f"spBv1.0/{self.cfg['group_id']}/NBIRTH/{self.cfg['node_id']}"
            self.publish(topic, create_birth_payload(self.db))
            self.messages_sent += 1
        except Exception as e:
            print_error("publish_birth", e)

    def publish_device_birth(self):
        """Send DBIRTH payload (not implemented)."""
        try:
            topic = f"spBv1.0/{self.cfg['group_id']}/DBIRTH/{self.cfg['node_id']}/dev1"
            # self.publish(topic, create_device_birth_payload(self.db))
        except Exception as e:
            print_error("publish_device_birth", e)

    def publish_death(self):
        """Send NDEATH payload."""
        try:
            topic = f"spBv1.0/{self.cfg['group_id']}/NDEATH/{self.cfg['node_id']}"
            self.publish(topic, create_death_payload())
            self.messages_sent += 1
        except Exception as e:
            print_error("publish_death", e)

    def publish_location(self):
        """Send current location via NDATA payload."""
        try:
            topic = f"spBv1.0/{self.cfg['group_id']}/NDATA/{self.cfg['node_id']}"
            self.publish(topic, create_location_payload())
            self.messages_sent += 1
        except Exception as e:
            print_error("publish_location", e)

    def get_group_id(self):
        """Return the Sparkplug group ID."""
        return self.cfg["group_id"]

    def get_node_id(self):
        """Return the Sparkplug node ID."""
        return self.cfg["node_id"]

    def get_metrics(self):
        """Expose MQTT connectivity and session metrics."""
        return {
            "connected": self.is_connected,
            "last_connection_time": self.last_connection_time,
            "messages_sent": self.messages_sent,
            "reconnect_count": self.reconnect_count,
            "latency_ms": self.latency_ms,
            "uptime_seconds": get_uptime_seconds(),
        }

    def get_tcp_latency(self):
        """Measure TCP handshake latency to the broker."""
        try:
            start = time.time()
            sock = socket.create_connection(
                (self.cfg["broker"], self.cfg["port"]), timeout=60
            )
            end = time.time()
            sock.close()
            return int(round((end - start) * 1000, 2))
        except Exception:
            return None

    # Global instance for access via API
    _sparkplug_client_instance = None
    
    def maybe_reload_config(self):
        new_cfg = load_config(self.db)
        if new_cfg != self.cfg:
            self.cfg = new_cfg
            self.reload_connection()

def set_sparkplug_client_instance(instance):
    global _sparkplug_client_instance
    _sparkplug_client_instance = instance

def get_sparkplug_client_instance():
    return _sparkplug_client_instance

