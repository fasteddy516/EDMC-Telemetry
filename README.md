# EDMC-Telemetry
  
Written by [Edward Wright](https://github.com/fasteddy516) for use with the [Elite: Dangerous Market Connector](https://github.com/EDCD/EDMarketConnector) (EDMC) by Jonathan Harris and the [Elite Dangerous Community Developers](https://github.com/EDCD).


## Description

This plugin takes the dashboard status and/or player journal updates from Elite: Dangerous as ingested by EDMC and distributes them via the [MQTT connectivity protocol](http://mqtt.org/).  Its primary use case is to provide in-game status and feedback to custom cockpits and controls.  

Want to build a custom flight stick and throttle with led feedback that accurately reflects the state of your hardpoints, landing gear, and cargo scoop?  How about a set of backlit controls that all change colour when you toggle between combat and analysis cockpit modes?  Maybe just a little LCD display that shows you how many jumps are left on your current route?  EDMC-Telemetry can provide the necessary status to drive this feedback through MQTT.

If you're interested in building your own controls, there are MQTT client libraries available for [just about every major programming language and platform](https://mqtt.org/software/).  Of particular interest are the [Arduino Client](https://www.arduino.cc/reference/en/libraries/pubsubclient/), [CircuitPython Client](https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/), Raspberry Pi via [Python Client](https://github.com/eclipse/paho.mqtt.python), and even [Node-Red](https://cookbook.nodered.org/mqtt/connect-to-broker).

_For a detailed list of the status and events that are available, please see the [Elite Dangerous Player Journal](https://elite-journal.readthedocs.io/en/latest/File%20Format/) documentation._ 

  
## Prerequisites
  
* First and foremost, this plugin requires EDMC.  
  
  **_As of version 0.3.0, EDMC version 5.0.0 or higher is required._**
  
* The plugin needs somewhere to send the data, which means a correctly installed and configured MQTT broker is required.  I personally use - and develop EDMC-Telemetry using - the [Eclipse Mosquitto™](https://mosquitto.org/) broker installed on a [Raspberry Pi](http://raspberrypi.org)


## Limitations

EDMC-Telemetry publishes messages using MQTT v3.1.1 through raw TCP with no encryption.  WebSockets and SSL/TLS encryption are not supported.

  
## Installation

  * On EDMC's `Plugins` settings tab press the `Open` button. This reveals the `plugins` folder where EDMC looks for plugins.
  * Download the [latest release](https://github.com/fasteddy516/EDMC-Telemetry/releases/latest) of this plugin.
  * Open the `.zip` archive that you downloaded and move the `Telemetry` folder contained inside into the `plugins` folder.

  _You will need to re-start EDMC for it to notice the new plugin._


## Configuration

After installing the plugin, it can be configured using the "Telemetry" tab in EDMC's "settings" dialog.  The following options are available:

* **Broker Address**: IP Address / hostname of MQTT broker. _(default=127.0.0.1)_

* **Port**: TCP/IP port used by MQTT broker _(default=1883)_

* **Keepalive**: MQTT keepalive in seconds _(default=60)_
  
* **QoS**: MQTT QoS setting _(0=at most once, 1=at least once, 2=exactly once, default=0)_
  
* **Username**: Username for authentication with MQTT broker. _(leave blank if not required)_
  
* **Password**: Password for authentication with MQTT broker. _(leave blank if not required)_

* **Client ID**: MQTT client ID used when connecting to the broker.  If you have multiple instances of EDMC-Telemetry connecting to the same broker, this value will have to be unique for each instance.  _(default=EDMCTelemetryClient)_

* **Root Topic**: Root topic for all MQTT messages from EDMC-Telemetry.  You can include multiple topic levels here, so something like `Telemetry/CMDR1` is valid if needed. _(default=Telemetry)_

* **Convert all topics to lowercase**: If you don't like capital letters in your MQTT topics, enable this option. _(default=unchecked)_
  
* **Publish Dashboard**: 

  Use the checkbox to enable/disable publishing of [dashboard](https://elite-journal.readthedocs.io/en/latest/Status%20File/) status and events.  The associated drop-down menu allows selection of `Raw` or `Processed` telemetry streams.  
  
  In `Raw` mode the JSON data received from the game will be published as-is to the `Telemetry/Dashboard` topic.
  
  In `Processed` mode the data is broken down and published into specific topics, i.e. `Telemetry/Dashboard/FireGroup`, `Telemetry/Dashboard/GuiFocus`, `Telemetry/Dashboard/Flags` and so on.  `Pips` information is further broken down into `Telemetry/Dashboard/Pips/Eng`, `Wep` and `Sys`.  `Fuel` shows up as `Telemetry/Dashboard/Fuel/Main` and `Reservoir`.  Note that all dashboard topics are only published when their associated data changes.

  _(default=checked, Processed)_
  
* **Publish Journal**:

  Use the checkbox to enable/disable publishing of [journal](https://elite-journal.readthedocs.io/en/latest/) events.  The associated drop-down menu allows selection of `Raw` or `Processed` telemetry streams.  
  
  In `Raw` mode, the JSON data received from the game will be published as-is to the `Telemetry/Journal` topic.

  In `Processed` mode, data from journal entries is published to individual topics based on the `Event` key in each entry's JSON data, i.e. `Telemetry/Journal/Docked`, `Telemetry/Journal/FSDJump`, and so on.

  _(default=checked, Processed)_

* **Publish Current System/Station**: Use the checkbox to enable/disable publishing of EDMC's internally-tracked current system and station.  These will be published to `Telemetry/Location/System` and `Telemetry/Location/Station`. _(default=checked)_

* **Publish EDMC State Tracking**: Use the checkbox to enable/disable publishing of EDMC's internal `state` to `Telemetry/Location/State`.  **Note that this generates an almost continuous stream of very large MQTT messages which may bog down your MQTT setup - enabling this option is generally unnecessary and not recommended.**  _(default=unchecked)_


## Custom MQTT Topics

All of EDMC-Telemetry's configuration settings are stored in the `settings.json` file located in the same folder as the plugin.  (This file gets generated with default settings the first time you run EDMC after installing the plugin.)  If you want to customize the MQTT topics that EDMC-Telemetry publishes to, you can do so by editing this file.  

The default configuration looks like this:

```json
{
    "version": "0.3.0",
    "broker": "127.0.0.1",
    "port": 1883,
    "keepalive": 60,
    "qos": 0,
    "username": "",
    "password": "",
    "client_id": "EDMCTelemetryPlugin",
    "dashboard": true,
    "dashboard_format": "Processed",
    "journal": true,
    "journal_format": "Processed",
    "location": true,
    "state": false,
    "lowercase_topics": false,
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
        "fuelmain": "Main"
    }
}
```

MQTT topics can be modified by changing the corresponding entry in the `topics` section.  If you wanted to shorten the `Dashboard` topic, you could do so by modifying the corresponding line in the file to `"dashboard": "db",`, which would result in all dashboard topics being published to `Telemetry/db`.  You can freely adjust the topics in the default configuration file, just make sure that you:

* Only modify the *value* for the desired topic. (i.e. the part **after** the colon!)

* Don't remove any of the lines that exist in the default configuration - the plugin needs these, and will crash without them.

* Avoid doing silly things like specifying the same topic for multiple items.  This will technically work, but likely won't be very useful.

* Don't mess with the other (not topic-related) settings.  Everything else is configurable via the EDMC settings UI, and modifying them here to values that the plugin isn't expecting will just prevent it from running.  

_If you happen to mess up the configuration file and can't figure out how to fix it, just delete or rename it.  A new, default file will be generated the next time you start EDMC._

In addition to the default topics that are created, you can add any other topic you like here in the same `"original_topic": "desired_topic",` format, and EDMC-Telemetry will replace any instance of `original_topic` with `desired_topic`.  If you want to use a custom topic for journal `FighterDestroyed` events, you could add a line like `"fighterdestroyed": "BigBadaBoom",`, and all of those events will get published to `Telemetry/Journal/BigBadaBoom`. (assuming, of course, that you haven't also messed with your `root` and `journal` topics.)  

Note that topic replacement lookups are not case-sensitive.  In the previous example, anything coming from the game as `FighterDestroyed`, `FIGHTERdestroyed`, `FiGhTeRdEsTrOyEd`, and similar would all get published to `BigBadaBoom`.  In order for your topics to get replaced correctly, make sure that the `original_topic` part of the line is all lowercase, regardless of how the journal documentation describes the event.  Incoming topics all get converted to lowercase before comparing them to items in this replacement list.


## Comments and Suggestions

I welcome any comments, suggestions, or criticism (of the constructive nature) that will allow me to improve this plugin.


## License

Copyright © 2021 Edward Wright.

Licensed under the [GNU Public License (GPL)](http://www.gnu.org/licenses/gpl-3.0.html) version 3.