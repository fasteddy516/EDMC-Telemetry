# EDMC-Telemetry
  
  Written by [Edward Wright](mailto:fasteddy@thewrightspace.net) for use with the [Elite: Dangerous Market Connector](https://github.com/Marginal/EDMarketConnector) (EDMC) by Jonathan Harris.


## Description

  This plugin takes the dashboard status and/or player journal updates from Elite: Dangerous as ingested by EDMC and distributes them via the [MQTT connectivity protocol](http://mqtt.org/).  The plugin is highly configurable, allowing individual status items to be enabled/disabled, as well as fully customizable MQTT topics.  


## Prerequisites
  
  In order to use this plugin, a correctly installed and configured MQTT broker is required.  I personally use - and develop EDMC-Telemetry using - the [Eclipse Mosquitto™](https://mosquitto.org/) broker installed on a [Raspberry Pi](http://raspberrypi.org).  

  
## Installation

  * On EDMC's Plugins settings tab press the “Open” button. This reveals the `plugins` folder where EDMC looks for plugins.
  * Download the [latest release](https://github.com/fasteddy516/EDMC-Telemetry/releases/latest) of this plugin.
  * Open the `.zip` archive that you downloaded and move the `EDMC-Telemetry` folder contained inside into the `plugins` folder.

  _You will need to re-start EDMC for it to notice the new plugin._


## Configuration

  After installing the plugin, it can be configured using the "Telemetry" tab in EDMC's "settings" dialog.  The following options are available:

  * **MQTT Tab**
    * **Broker Address**: IP Address / hostname of MQTT broker
    * **Port**: TCP/IP port used by MQTT broker _(default=1883)_
    * **Keepalive**: MQTT keepalive in seconds _(default=60)_
    * **QoS**: MQTT QoS setting _(0=at most once, 1=at least once, 2=exactly once, default=0)_
    * **Root Topic**: Root topic for all MQTT messages from EDMC-Telemetry _(default=telemetry)_

  * **Dashboard Tab**
    * **Publish Format**: Determines how to publish status messages.  Select **none** to disable publishing of dashboard status, **raw** to publish dashboard status as raw JSON, or **processed** to enable selective processing of individual status elements.
    
    * **Topic**: MQTT topic to use for publishing dashboard status  _(default=dashboard)_.  This will be used in conjunction with the specified root topic, i.e. _telemetry/dashboard_.

    * **Status**: Status elements to include when publish format is set to **processed**.
        * Flags (check/topic)
        * Pips (check/topic)
        * FireGroup (check/topic)
        * GuiFocus
        * Latitude
        * Longitude
        * Heading
        * Altitude
        * Flag Format (combined. discrete)
        * Pip Format (combined, discrete)
    * Pip Topics
        * Sys
        * Eng
        * Wep

  * **Flags Tab**
    * Tons!  Each has check/topic

  * **Journal Tab**
    * Publish Format (none, raw)
    * Topic
  

## Comments and Suggestions

  I welcome any comments, suggestions, or criticism (of the constructive nature) that will allow me to improve this plugin.


## License

Copyright © 2018 Edward Wright.

Licensed under the [GNU Public License (GPL)](http://www.gnu.org/licenses/gpl-3.0.html) version 3.