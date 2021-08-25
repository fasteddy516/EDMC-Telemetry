# -*- coding: utf-8 -*-
"""Code related to settings for the EDMC-Telemetry plugin."""

import json
import logging
import tkinter as tk
from pathlib import Path
from typing import Any, Union

import myNotebook as nb  # type: ignore (provided by EDMC)
import semantic_version  # type: ignore (provided by EDMC)
from ttkHyperlinkLabel import HyperlinkLabel  # type: ignore (provided by EDMC)

from paho.mqtt import __version__ as mqtt_version


class Settings:
    """Handles storage, retrieval and access to EDMC-Telemetry settings."""

    # Base name to use for the .json settings file (default is 'settings').
    _FILE: str = "settings"

    # Folder location of .json settings file (default is in plugin folder).
    _FOLDER: Path = Path(__file__).parent

    # Minimal default configuration.
    _DEFAULT: dict[str, Any] = {
        "version": None,
        "broker": "127.0.0.1",
        "port": 1883,
        "keepalive": 60,
        "qos": 0,
        "username": "",
        "password": "",
        "client_id": "EDMCTelemetryPlugin",
        "encryption": False,
        "ca_certs": "",
        "certfile": "",
        "keyfile": "",
        "tls_insecure": False,
        "dashboard": True,
        "dashboard_format": "Processed",
        "journal": True,
        "journal_format": "Processed",
        "location": True,
        "state": False,
        "lowercase_topics": False,
        "topics": {
            "root": "Telemetry",
            "dashboard": "Dashboard",
            "journal": "Journal",
            "location": "Location",
            "state": "State",
            "system": "System",
            "station": "Station",
            "pips": "Pips",
            "sys": "Sys",
            "eng": "Eng",
            "wep": "Wep",
            "fuel": "Fuel",
            "fuelreservoir": "Reservoir",
            "fuelmain": "Main",
        },
    }

    # Setters and getters - settings should be accessed through these properties rather
    # than via the _options dictionary directly.
    @property
    def plugin_version(self) -> semantic_version:
        """Version of the EDMC-Telemetry plugin."""
        return semantic_version.Version(self._version)

    @property
    def file_version(self) -> semantic_version:
        """Version of the EDMC-Telemetry plugin used to create settings.json."""
        return semantic_version.Version(self._options["version"])

    @property
    def broker(self) -> str:
        """Address of the MQTT broker."""
        return self._options["broker"]

    @broker.setter
    def broker(self, new_value: str) -> None:
        self._options["broker"] = new_value
        self._broker_tk.set(new_value)

    @property
    def port(self) -> int:
        """Port used to communicate with the MQTT broker."""
        return self._options["port"]

    @port.setter
    def port(self, new_value: int) -> None:
        self._options["port"] = new_value
        self._port_tk.set(new_value)

    @property
    def keepalive(self) -> int:
        """MQTT keepalive period in seconds."""
        return self._options["keepalive"]

    @keepalive.setter
    def keepalive(self, new_value: int) -> None:
        self._options["keepalive"] = new_value
        self._keepalive_tk.set(new_value)

    @property
    def qos(self) -> int:
        """MQTT quality of service level for publishing to broker."""
        return self._options["qos"]

    @qos.setter
    def qos(self, new_value: int) -> None:
        self._options["qos"] = new_value
        self._qos_tk.set(new_value)

    @property
    def username(self) -> str:
        """Username for connecting to MQTT broker."""
        return self._options["username"]

    @username.setter
    def username(self, new_value: str) -> None:
        self._options["username"] = new_value
        self._username_tk.set(new_value)

    @property
    def password(self) -> str:
        """Password for connecting to MQTT broker."""
        return self._options["password"]

    @password.setter
    def password(self, new_value: str) -> None:
        self._options["password"] = new_value
        self._password_tk.set(new_value)

    @property
    def client_id(self) -> str:
        """Client ID to use for connection to the MQTT broker."""
        return self._options["client_id"]

    @client_id.setter
    def client_id(self, new_value: str) -> None:
        self._options["client_id"] = new_value
        self._client_id_tk.set(new_value)

    @property
    def encryption(self) -> bool:
        """Determine if TLS/SSL connection to the MQTT broker should be used."""
        return self._options["encryption"]

    @encryption.setter
    def encryption(self, new_value: bool) -> None:
        self._options["encryption"] = new_value
        self._encryption_tk.set(new_value)

    @property
    def ca_certs(self) -> Union[str, None]:
        """Return a string path to trusted CA certificate files."""
        if len(self._options["ca_certs"]):
            return self._options["ca_certs"]
        else:
            return None

    @ca_certs.setter
    def ca_certs(self, new_value: str) -> None:
        self._options["ca_certs"] = new_value
        self._ca_certs_tk.set(new_value)

    @property
    def certfile(self) -> Union[str, None]:
        """Return a string path to the client certificate used for authentication."""
        if len(self._options["certfile"]):
            return self._options["certfile"]
        else:
            return None

    @certfile.setter
    def certfile(self, new_value: str) -> None:
        self._options["certfile"] = new_value
        self._certfile_tk.set(new_value)

    @property
    def keyfile(self) -> Union[str, None]:
        """Return a string path to the client private key used for authentication."""
        if len(self._options["keyfile"]):
            return self._options["keyfile"]
        else:
            return None

    @keyfile.setter
    def keyfile(self, new_value: str) -> None:
        self._options["keyfile"] = new_value
        self._keyfile_tk.set(new_value)

    @property
    def tls_insecure(self) -> bool:
        """If enabled, server identity verification will be bypassed."""
        return self._options["tls_insecure"]

    @tls_insecure.setter
    def tls_insecure(self, new_value: bool) -> None:
        self._options["tls_insecure"] = new_value
        self._tls_insecure_tk.set(new_value)

    @property
    def root_topic(self) -> str:
        """Root MQTT topic that all other topics will be published under."""
        return self._options["topics"]["root"]

    @root_topic.setter
    def root_topic(self, new_value: str) -> None:
        self._options["topics"]["root"] = new_value
        self._root_topic_tk.set(new_value)

    @property
    def dashboard(self) -> bool:
        """Enable/disable publishing of dashboard telemetry."""
        return self._options["dashboard"]

    @dashboard.setter
    def dashboard(self, new_value: bool) -> None:
        self._options["dashboard"] = new_value
        self._dashboard_tk.set(new_value)

    @property
    def dashboard_format(self) -> str:
        """Format of published dashboard telemetry."""
        return self._options["dashboard_format"]

    @dashboard_format.setter
    def dashboard_format(self, new_value: str) -> None:
        self._options["dashboard_format"] = new_value
        self._dashboard_format_tk.set(new_value)

    @property
    def journal(self) -> bool:
        """Enable/disable publishing of journal telemetry."""
        return self._options["journal"]

    @journal.setter
    def journal(self, new_value: bool) -> None:
        self._options["journal"] = new_value
        self._journal_tk.set(new_value)

    @property
    def journal_format(self) -> str:
        """Format of published journal telemetry."""
        return self._options["journal_format"]

    @journal_format.setter
    def journal_format(self, new_value: str) -> None:
        self._options["journal_format"] = new_value
        self._journal_format_tk.set(new_value)

    @property
    def location(self) -> bool:
        """Enable/disable publishing of EDMC-generated location telemetry."""
        return self._options["location"]

    @location.setter
    def location(self, new_value: bool) -> None:
        self._options["location"] = new_value
        self._location_tk.set(new_value)

    @property
    def state(self) -> bool:
        """Enable/disable publishing of EDMC-generated state telemetry."""
        return self._options["state"]

    @state.setter
    def state(self, new_value: bool) -> None:
        self._options["state"] = new_value
        self._state_tk.set(new_value)

    @property
    def lowercase_topics(self) -> bool:
        """Enable/disable forcing of all topics to lowercase."""
        return self._options["lowercase_topics"]

    @lowercase_topics.setter
    def lowercase_topics(self, new_value: bool) -> None:
        self._options["lowercase_topics"] = new_value
        self._lowercase_topics_tk.set(new_value)

    # This one isn't a 'property' but is grouped with the other properties because it is
    # used like a getter.
    def topic(self, requested_topic: str) -> str:
        """Safely retrieves MQTT topics from the _options dictionary."""
        if requested_topic.lower() in self._options["topics"]:
            return self._options["topics"][requested_topic.lower()]
        else:
            return requested_topic

    def __init__(self, telemetry_version: str, logger: logging.Logger) -> None:
        """Initialize a telemetry settings object."""
        Settings._DEFAULT["version"] = telemetry_version
        self._version = telemetry_version
        self._logger = logger
        self._options = {}
        self._load()

    def _load(self) -> None:
        """Read telemetry settings from a file, creating a new file if needed."""
        settings_file = Settings._FOLDER / f"{Settings._FILE}.json"

        if settings_file.exists():
            with open(settings_file, mode="r", encoding="utf-8") as file:
                self._options = json.loads(file.read())
            self._logger.info(f"Loaded settings file <{settings_file}>")

            # Upgrade the settings file if it is out-of-date.
            if self.plugin_version > self.file_version:
                self._upgrade()

            # Generate a warning if settings are from a newer version of the plugin.
            elif self.plugin_version < self.file_version:
                self._logger.warn(
                    "JSON settings file was created by a newer version of the "
                    + f"telemetry plugin (v{self.file_version})."
                )
        else:
            self._options = Settings._DEFAULT.copy()
            self._save()

        # create tkinter variables for preferences that can be modified through the UI.
        self._broker_tk = tk.StringVar(value=self.broker)
        self._port_tk = tk.IntVar(value=self.port)
        self._keepalive_tk = tk.IntVar(value=self.keepalive)
        self._qos_tk = tk.IntVar(value=self.qos)
        self._username_tk = tk.StringVar(value=self.username)
        self._password_tk = tk.StringVar(value=self.password)
        self._client_id_tk = tk.StringVar(value=self.client_id)
        self._encryption_tk = tk.BooleanVar(value=self.encryption)
        self._ca_certs_tk = tk.StringVar(value=self.ca_certs)
        self._certfile_tk = tk.StringVar(value=self.certfile)
        self._keyfile_tk = tk.StringVar(value=self.keyfile)
        self._tls_insecure_tk = tk.BooleanVar(value=self.tls_insecure)
        self._dashboard_tk = tk.BooleanVar(value=self.dashboard)
        self._dashboard_format_tk = tk.StringVar(value=self.dashboard_format)
        self._journal_tk = tk.BooleanVar(value=self.journal)
        self._journal_format_tk = tk.StringVar(value=self.journal_format)
        self._location_tk = tk.BooleanVar(value=self.location)
        self._state_tk = tk.BooleanVar(value=self.state)
        self._root_topic_tk = tk.StringVar(value=self.root_topic)
        self._lowercase_topics_tk = tk.BooleanVar(value=self.lowercase_topics)

    def _save(self, is_backup: bool = False) -> None:
        """Write telemetry settings to a file."""
        if is_backup:
            filename = f"{Settings._FILE}_backup_{self.file_version}.json"
        else:
            filename = f"{Settings._FILE}.json"
        settings_file = Settings._FOLDER / filename

        with open(settings_file, mode="w", encoding="utf-8") as file:
            file.write(json.dumps(self._options, indent=4))

        if is_backup:
            self._logger.info(f"Backed up settings file to <{settings_file}>")
        else:
            self._logger.info(f"Saved settings file <{settings_file}>")

    def _upgrade(self) -> None:
        """Upgrades the telemetry settings file and saves a backup of the original."""
        # The upgrade process should definitely start by backing up existing data.
        self._save(is_backup=True)

        # Set the settings version to the current plugin version.
        self._options["version"] = self._version

        # Add/update settings as needed.
        for key in Settings._DEFAULT:

            # If the key is missing, add it.
            if key not in self._options:
                self._options[key] = Settings._DEFAULT[key]

            # More processing is needed if the key already exists.
            else:
                # Reset to default if type has changed (i.e. int to bool, etc.).
                if type(self._options[key]) != type(Settings._DEFAULT[key]):
                    self._options[key] = Settings._DEFAULT[key]
                    self._logger.debug(f"'{key}' was reset to its new default value.")

                # Make sure all required entries are in topics dictionary.
                elif key == "topics":
                    for topic in Settings._DEFAULT[key]:
                        if topic not in self._options[key]:
                            self._options[key][topic] = Settings._DEFAULT[key][topic]
                            self._logger.debug(f"Added missing topic '{topic}'.")

        # Remove old/invalid/deprecated settings.
        keys_to_remove = list()
        for key in self._options:
            if key not in Settings._DEFAULT:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._options[key]
            self._logger.debug(f"'{key}' is invalid and has been removed.")

        # Once the settings upgrade is complete, do a normal save.
        self._save()
        self._logger.info(f"Settings upgraded for EDMC-Telemetry {self.plugin_version}")

    def show_preferences(self, parent: nb.Notebook) -> tk.Frame:
        """Display preferences tab in UI."""
        PADX = 10
        PADY = 2

        frame = nb.Frame(parent)
        row = 0

        # mqtt broker address
        row += 1
        nb.Label(frame, text="Broker Address").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._broker_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # mqtt broker port
        row += 1
        nb.Label(frame, text="Port").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._port_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # mqtt broker keepalive
        row += 1
        nb.Label(frame, text="Keepalive").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._keepalive_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # mqtt qos
        row += 1
        nb.Label(frame, text="QoS").grid(padx=PADX, row=row, sticky=tk.W)
        nb.OptionMenu(frame, self._qos_tk, self._qos_tk.get(), 0, 1, 2).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.W
        )

        # mqtt username
        row += 1
        nb.Label(frame, text="Username").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._username_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # mqtt password
        row += 1
        nb.Label(frame, text="Password").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._password_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # mqtt client id
        row += 1
        nb.Label(frame, text="Client ID").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._client_id_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # mqtt root topic
        row += 1
        nb.Label(frame, text="Root Topic").grid(padx=PADX, row=row, sticky=tk.W)
        nb.Entry(frame, textvariable=self._root_topic_tk).grid(
            padx=PADX, pady=PADY, row=row, column=1, sticky=tk.EW
        )

        # lowercase topics
        row += 1
        nb.Checkbutton(
            frame,
            text="Convert all topics to lowercase",
            variable=self._lowercase_topics_tk,
            command="",
        ).grid(padx=PADX, row=row, sticky=tk.W)

        # dashboard
        row += 1
        nb.Checkbutton(
            frame,
            text="Publish Dashboard",
            variable=self._dashboard_tk,
            command="",
        ).grid(padx=PADX, row=row, sticky=tk.W)
        nb.OptionMenu(
            frame,
            self._dashboard_format_tk,
            self._dashboard_format_tk.get(),
            "Raw",
            "Processed",
        ).grid(padx=PADX, pady=PADY, row=row, column=1, sticky=tk.W)

        # journal
        row += 1
        nb.Checkbutton(
            frame,
            text="Publish Journal",
            variable=self._journal_tk,
            command="",
        ).grid(padx=PADX, row=row, sticky=tk.W)
        nb.OptionMenu(
            frame,
            self._journal_format_tk,
            self._journal_format_tk.get(),
            "Raw",
            "Processed",
        ).grid(padx=PADX, pady=PADY, row=row, column=1, sticky=tk.W)

        # location
        row += 1
        nb.Checkbutton(
            frame,
            text="Publish Current System/Station",
            variable=self._location_tk,
            command="",
        ).grid(padx=PADX, row=row, sticky=tk.W)

        # state
        row += 1
        nb.Checkbutton(
            frame,
            text="Publish EDMC State Tracking",
            variable=self._state_tk,
            command="",
        ).grid(padx=PADX, row=row, sticky=tk.W)

        # plugin link and version
        row += 1
        HyperlinkLabel(
            frame,
            text="https://github.com/fasteddy516/EDMC-Telemetry/",
            background=nb.Label().cget("background"),
            url="https://github.com/fasteddy516/EDMC-Telemetry/",
            underline=True,
        ).grid(padx=PADX, pady=(1, 4), row=row, column=0, sticky=tk.W)
        nb.Label(frame, text=f"Plugin Version {self.plugin_version}").grid(
            padx=PADX, pady=(1, 4), row=row, column=1, sticky=tk.E
        )

        # mqtt link and version
        row += 1
        HyperlinkLabel(
            frame,
            text="https://github.com/eclipse/paho.mqtt.python/",
            background=nb.Label().cget("background"),
            url="https://github.com/eclipse/paho.mqtt.python",
            underline=True,
        ).grid(padx=PADX, pady=(1, 4), row=row, column=0, sticky=tk.W)
        nb.Label(frame, text=f"MQTT Version {mqtt_version}").grid(
            padx=PADX, pady=(1, 4), row=row, column=1, sticky=tk.E
        )

        return frame

    def update_preferences(self) -> bool:
        """Update settings when the preferences panel is closed."""
        reset_connection = False

        # If any of these settings changed, the connection to the broker must be reset.
        if self.broker != self._broker_tk.get():
            self.broker = self._broker_tk.get()
            reset_connection = True

        if self.port != self._port_tk.get():
            self.port = self._port_tk.get()
            reset_connection = True

        if self.keepalive != self._keepalive_tk.get():
            self.keepalive = self._keepalive_tk.get()
            reset_connection = True

        if self.username != self._username_tk.get():
            self.username = self._username_tk.get()
            reset_connection = True

        if self.password != self._password_tk.get():
            self.password = self._password_tk.get()
            reset_connection = True

        if self.client_id != self._client_id_tk.get():
            self.client_id = self._client_id_tk.get()
            reset_connection = True

        # The rest of these options can be adjusted on-the-fly while connected.
        self.root_topic = self._root_topic_tk.get()
        self.lowercase_topics = self._lowercase_topics_tk.get()
        self.qos = self._qos_tk.get()
        self.dashboard = self._dashboard_tk.get()
        self.dashboard_format = self._dashboard_format_tk.get()
        self.journal = self._journal_tk.get()
        self.journal_format = self._journal_format_tk.get()
        self.location = self._location_tk.get()
        self.state = self._state_tk.get()

        self._save()

        return reset_connection
