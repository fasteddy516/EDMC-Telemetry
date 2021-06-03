# -*- coding: utf-8 -*-
"""Telemetry: An EDMC Plugin to relay dashboard status and journal entries via MQTT."""

# Written by Edward Wright (https://github.com/fasteddy516)
# Available at https://github.com/fasteddy516/EDMC-Telemetry
#
# Requires Elite Dangerous Market Connector: https://github.com/EDCD/EDMarketConnector
# Uses the Eclipse Paho MQTT Python Client (https://github.com/eclipse/paho.mqtt.python)
# for all MQTT protocol (http://mqtt.org/) interactions.

import json
import logging
import os
import time
import tkinter as tk
from typing import Any, Dict, Optional, Tuple

import myNotebook as nb
import semantic_version
from config import appname, appversion, config

import paho.mqtt.client as mqtt_client
from settings import Settings

# plugin constants
TELEMETRY_VERSION = "0.3.0"
TELEMETRY_PIPS = ("sys", "eng", "wep")


# set up logging
logger = logging.getLogger(f"{appname}.{os.path.basename(os.path.dirname(__file__))}")


# Globals
class Globals:
    """Holds module globals."""

    def __init__(self):
        """Create and initialize module globals."""
        self.status: Optional[tk.Label] = None
        self.status_message: str = "Initializing"
        self.status_color: str = "grey"
        self.mqtt_connected: bool = False
        self.current_db = {}
        self.current_location = {"system": "N/A", "station": "N/A"}
        self.current_state = {}
        self.settings = Settings(TELEMETRY_VERSION, logger)
        self.mqtt = mqtt_client.Client()


this = Globals()


# Standard EDMC plugin functions
def plugin_start3(plugin_dir: str) -> str:
    """Start the telemetry plugin."""
    if callable(appversion) and appversion() >= semantic_version.Version("5.0.0"):
        connect_telemetry()
    else:
        logger.fatal("EDMC-Telemetry requires EDMC 5.0.0 or newer.")
        status_message(message="ERROR", color="red")
    return "Telemetry"


def plugin_stop() -> None:
    """Stop the telemetry plugin."""
    disconnect_telemetry()


def plugin_app(parent: tk.Frame) -> Tuple[tk.Label, tk.Label]:
    """Show broker connection status on main UI."""
    label = tk.Label(parent, text="Telemetry:")
    this.status = tk.Label(parent, anchor=tk.W, foreground="grey", text="Initializing")
    update_status()
    this.status.bind_all("<<TelemetryStatus>>", update_status)
    return (label, this.status)


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> Optional[tk.Frame]:
    """Allow configuration to be modified from UI."""
    return this.settings.show_preferences(parent)


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """Update settings after they've been modified in UI."""
    # update_preferences() returns True if a connection reset is required
    if this.settings.update_preferences():
        logger.info("MQTT broker settings modified, connection will now restart.")
        disconnect_telemetry()
        connect_telemetry()


def status_message(message: str = "", color: str = "", background=False) -> None:
    """Update the status message and color to be displayed on the main UI."""
    if len(message):
        this.status_message = message
    if len(color):
        this.status_color = color
    if not background:
        update_status()


def update_status(event=None) -> None:
    """Post the status message to the main UI."""
    if this.status is not None:
        this.status["text"] = this.status_message
        this.status["foreground"] = this.status_color


def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]) -> None:
    """Publish dashboard status via MQTT."""
    if not this.settings.dashboard:
        return

    if not this.mqtt_connected:
        return

    dashboard_topic = this.settings.topic("dashboard")

    if this.settings.dashboard_format == "Raw":
        publish(dashboard_topic, payload=json.dumps(entry))
    else:
        for key in entry:
            # always ignore these keys
            if key.lower() == "timestamp" or key.lower() == "event":
                continue

            # publish any updated dashboard data
            if key not in this.current_db or this.current_db[key] != entry[key]:
                topic = f"{dashboard_topic}/{this.settings.topic(key)}"

                # additional processing for pip updates
                if key.lower() == "pips":
                    for i, pips in enumerate(entry[key]):
                        publish(
                            f"{topic}/{this.settings.topic(TELEMETRY_PIPS[i])}",
                            payload=str(pips),
                        )

                # additional processing for fuel updates
                elif key.lower() == "fuel":
                    for tank in entry[key]:
                        publish(
                            f"{topic}/{this.settings.topic(tank)}",
                            payload=str(entry[key][tank]),
                        )

                # standard processing for most status updates
                else:
                    publish(topic, payload=str(entry[key]))

                # update internal tracking variable (used to filter unnecessary updates)
                this.current_db[key] = entry[key]


def journal_entry(
    cmdr: str,
    is_beta: bool,
    system: str,
    station: str,
    entry: Dict[str, Any],
    state: Dict[str, Any],
) -> None:
    """Process player journal entries."""
    if not this.mqtt_connected:
        return

    if this.settings.location:
        if this.current_location["system"] != system:
            publish(
                f"{this.settings.topic('location')}/{this.settings.topic('system')}",
                payload="" if system is None else system,
            )
            this.current_location["system"] = system

        if this.current_location["station"] != station:
            publish(
                f"{this.settings.topic('location')}/{this.settings.topic('station')}",
                payload="" if station is None else station,
            )
            this.current_location["station"] = station

    if this.settings.state:
        if this.current_state != state:
            new_state = state.copy()
            if "Friends" in new_state and isinstance(new_state["Friends"], set):
                new_state["Friends"] = list(new_state["Friends"])
            publish(this.settings.topic("state"), payload=json.dumps(new_state))
            this.current_state = state.copy()

    if not this.settings.journal:
        return

    topic = this.settings.topic("journal")

    if this.settings.journal_format == "Raw":
        data = entry
    else:
        topic = f"{topic}/{entry['event']}"
        data = entry.copy()
        del data["event"]
        del data["timestamp"]

    publish(topic, payload=json.dumps(data))


def connect_telemetry() -> None:
    """Establish a connection with the MQTT broker."""
    status_message(message="Connecting", color="steel blue")
    this.mqtt.reinitialise(client_id=this.settings.client_id)
    this.mqtt.on_connect = mqttCallback_on_connect
    this.mqtt.on_disconnect = mqttCallback_on_disconnect
    this.mqtt.username_pw_set(this.settings.username, this.settings.password)
    this.mqtt.connect_async(
        this.settings.broker,
        this.settings.port,
        this.settings.keepalive,
    )
    this.mqtt.loop_start()


def disconnect_telemetry() -> None:
    """Break connection to the MQTT broker."""
    status_message(message="Disconnecting", color="steel blue")
    this.mqtt.loop_stop()
    this.mqtt.disconnect()
    start = time.monotonic()
    while this.mqtt_connected:
        time.sleep(0.1)
        if (time.monotonic() - start) >= 5.0:
            logger.error("Timeout waiting for MQTT to disconnect.")
            break


def publish(topic: str, payload: str):
    """Publish the specified payload to the specified MQTT topic."""
    topic = f"{this.settings.topic('root')}/{topic}"
    if this.settings.lowercase_topics:
        topic = topic.lower()
    this.mqtt.publish(topic, payload=payload, qos=this.settings.qos, retain=False)


def mqttCallback_on_connect(client, userdata, flags, rc):
    """Run this callback when connection to a broker is established."""
    logger.info("Connected to MQTT Broker")
    this.current_db = {}
    this.current_location["system"] = "N/A"
    this.current_location["station"] = "N/A"
    this.current_state = {}
    this.mqtt_connected = True
    status_message(message="Online", color="dark green", background=True)
    if this.status is not None and not config.shutting_down:
        this.status.event_generate("<<TelemetryStatus>>", when="tail")


def mqttCallback_on_disconnect(client, userdata, rc):
    """Run this callback when the connection to the broker is lost."""
    logger.info("Disconnected from MQTT Broker")
    this.mqtt_connected = False
    status_message(message="Offline", color="orange red", background=True)
    if this.status is not None and not config.shutting_down:
        this.status.event_generate("<<TelemetryStatus>>", when="tail")
