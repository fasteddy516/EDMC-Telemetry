# -*- coding: utf-8 -*-
#
# Teletry: An EDMC Plugin to relay dashboard status and/or journal entries via MQTT
# 
# Written by Edward Wright (https://github.com/fasteddy516)
# Available at https://github.com/fasteddy516/EDMC-Telemetry
#
# Requires the Elite Dangerous Market Connector: https://github.com/Marginal/EDMarketConnector/wiki
# Uses the MQTT protocol (http://mqtt.org/) and Eclipse Paho MQTT Python Client (https://github.com/eclipse/paho.mqtt.python)

import requests
import sys
import ttk
import Tkinter as tk
import myNotebook as nb
from config import config
from ttkHyperlinkLabel import HyperlinkLabel

import paho.mqtt.client as mqtt
import json

TELEMETRY_VERSION = "0.1.0"
TELEMETRY_CLIENTID = "EDMCTelemetryPlugin"

# default values for initial population of configuration
DEFAULT_BROKER_ADDRESS = "127.0.0.1"
DEFAULT_BROKER_PORT = 1883
DEFAULT_BROKER_KEEPALIVE = 60
DEFAULT_BROKER_QOS = 0
DEFAULT_DASHBOARD_FORMAT = 'raw'
DEFAULT_FLAG_FORMAT = 'combined'
DEFAULT_PIP_FORMAT = 'combined'
DEFAULT_DASHBOARD_FILTER = {'Flags': 1, 'Pips': 0, 'FireGroup': 0, 'GuiFocus': 0, 'Latitude': 0, 'Longitude': 0, 'Heading': 0, 'Altitude': 0}

STATUS_FLAG = ['Docked', 'Landed', 'LandingGear', 'Shields', 'Supercruise', 'FlightAssistOff', 'Hardpoints', 'InWing',
    'Lights', 'CargoScoop', 'SilentRunning', 'Scooping', 'SrvHandbrake', 'SrvTurret', 'SrcUnderShip', 'SrvDriveAssist',
    'FsdMassLocked', 'FsdCharging', 'FsdCooldown', 'LowFuel', 'OverHeating', 'HasLatLong', 'IsInDanger', 'BeingInterdicted',
    'InMainShip', 'InFighter', 'InSrv', 'Bit27', 'Bit28', 'Bit29', 'Bit30', 'Bit31']

this = sys.modules[__name__] # for holding globals

# Plugin startup
def plugin_start():
    loadConfiguration()
    initializeTelemetry()
    print "Telemetry: Started"
    return "Telemetry"

# Plugin shutdown
def plugin_stop():
    stopTelemetry()
    print "Telemetry: Stopped"

def plugin_app(parent):
    label = tk.Label(parent, text="Telemetry")
    this.status = tk.Label(parent, anchor=tk.W, text="Offline", state=tk.DISABLED)
    return (label, this.status)
    

def plugin_prefs(parent):
    frame = nb.Frame(parent)
    frame.columnconfigure(1, weight=1)

    PADX = 10
    PADY = 2
   
    nb.Label(frame, text="MQTT Broker").grid(columnspan=4, padx=PADX, row=10, sticky=tk.W)
    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(columnspan=4, padx=PADX, pady=2, row=11, sticky=tk.EW)
    
    nb.Label(frame, text="Address").grid(row=12, sticky=tk.E)
    this.brokerAddress_entry = nb.Entry(frame, textvariable=this.cfg_brokerAddress)
    this.brokerAddress_entry.grid(padx=PADX, pady=PADY, row=12, column=1, sticky=tk.EW)

    nb.Label(frame, text="Port").grid(row=12, column=2, sticky=tk.E)
    this.brokerPort_entry = nb.Entry(frame, textvariable=this.cfg_brokerPort)
    this.brokerPort_entry.grid(padx=PADX, pady=PADY, row=12, column=3, sticky=tk.EW)

    nb.Label(frame, text="Keepalive").grid(row=13, sticky=tk.E)
    this.brokerKeepalive_entry = nb.Entry(frame, textvariable=this.cfg_brokerKeepalive)
    this.brokerKeepalive_entry.grid(padx=PADX, pady=PADY, row=13, column=1, sticky=tk.EW)

    nb.Label(frame, text=_('QoS')).grid(row=13, column=2, sticky=tk.E)
    this.brokerQoS_button = nb.OptionMenu(frame, this.cfg_brokerQoS, this.cfg_brokerQoS.get(), 0, 1, 2)
    this.brokerQoS_button.configure(width = 15)
    this.brokerQoS_button.grid(padx=PADX, pady=PADY, row=13, column=3, sticky=tk.EW)

    nb.Label(frame).grid(columnspan=4, row=14, sticky=tk.W) # spacer    
    nb.Label(frame, text="Dashboard Status").grid(columnspan=4, padx=PADX, row=15, sticky=tk.W)
    ttk.Separator(frame, orient=tk.HORIZONTAL).grid(columnspan=4, padx=PADX, pady=2, row=16, sticky=tk.EW)
    nb.Label(frame, text=_('Format')).grid(padx=PADX, row=17, column=0, sticky=tk.W)
    options = ['raw', 'processed']
    this.dashboardFormat_button = nb.OptionMenu(frame, this.cfg_dashboardFormat, this.cfg_dashboardFormat.get(), *options, command=prefStateChange)
    this.dashboardFormat_button.configure(width = 15)
    this.dashboardFormat_button.grid(padx=PADX, pady=PADY, row=17, column=1, sticky=tk.W)

    this.dashboardFilter_firegroup_check = nb.Checkbutton(frame, text="FireGroup", variable=this.dashboardFilter['FireGroup'], command=prefStateChange)
    this.dashboardFilter_firegroup_check.grid(padx=PADX, row=17, column=2, sticky=tk.W)
    
    this.dashboardFilter_guifocus_check = nb.Checkbutton(frame, text="GuiFocus", variable=this.dashboardFilter['GuiFocus'], command=prefStateChange)
    this.dashboardFilter_guifocus_check.grid(padx=PADX, row=17, column=3, sticky=tk.W)

    this.dashboardFilter_flags_check = nb.Checkbutton(frame, text="Flags", variable=this.dashboardFilter['Flags'], command=prefStateChange)
    this.dashboardFilter_flags_check.grid(padx=PADX, row=18, sticky=tk.W)
    
    this.dashboardFlagFormat_button = nb.OptionMenu(frame, this.cfg_dashboardFlagFormat, this.cfg_dashboardFlagFormat.get(), 'combined', 'discrete')
    this.dashboardFlagFormat_button.configure(width = 15)
    this.dashboardFlagFormat_button.grid(padx=PADX, pady=PADY, row=18, column=1, sticky=tk.W)

    this.dashboardFilter_latitude_check = nb.Checkbutton(frame, text="Latitude", variable=this.dashboardFilter['Latitude'], command=prefStateChange)
    this.dashboardFilter_latitude_check.grid(padx=PADX, row=18, column=2, sticky=tk.W)
    
    this.dashboardFilter_longitude_check = nb.Checkbutton(frame, text="Longitude", variable=this.dashboardFilter['Longitude'], command=prefStateChange)
    this.dashboardFilter_longitude_check.grid(padx=PADX, row=18, column=3, sticky=tk.W)
    
    
    this.dashboardFilter_pips_check = nb.Checkbutton(frame, text="Pips", variable=this.dashboardFilter['Pips'], command=prefStateChange)
    this.dashboardFilter_pips_check.grid(padx=PADX, row=19, sticky=tk.W)
    
    this.dashboardPipFormat_button = nb.OptionMenu(frame, this.cfg_dashboardPipFormat, this.cfg_dashboardPipFormat.get(), 'combined', 'discrete')
    this.dashboardPipFormat_button.configure(width = 15)
    this.dashboardPipFormat_button.grid(padx=PADX, pady=PADY, row=19, column=1, sticky=tk.W)
    
    this.dashboardFilter_heading_check = nb.Checkbutton(frame, text="Heading", variable=this.dashboardFilter['Heading'], command=prefStateChange)
    this.dashboardFilter_heading_check.grid(padx=PADX, row=19, column=2, sticky=tk.W)
    
    this.dashboardFilter_altitude_check = nb.Checkbutton(frame, text="Altitude", variable=this.dashboardFilter['Altitude'], command=prefStateChange)
    this.dashboardFilter_altitude_check.grid(padx=PADX, row=19, column=3, sticky=tk.W)
            

    nb.Label(frame).grid(columnspan=4, row=24, sticky=tk.W) # spacer
    HyperlinkLabel(frame, text='https://github.com/fasteddy516/EDMC-Telemetry/', background=nb.Label().cget('background'), url='https://github.com/fasteddy516/DataRelay/', underline=True).grid(padx=PADX, row=25, columnspan=2, sticky=tk.W)
    nb.Label(frame, text="Telemetry Plugin Version " + TELEMETRY_VERSION).grid(padx=PADX, row=25, column=2, columnspan=2, sticky=tk.E)

    prefStateChange()

    return frame



# Update enabled/disabled states of configuration elements
def prefStateChange(format='processed'):
    if format == 'raw':
        this.currentStatus = {}

    this.dashboardFlagFormat_button['state'] = this.dashboardFilter_flags_check['state'] = this.dashboardFilter_pips_check['state'] = this.dashboardFilter_firegroup_check['state'] = this.dashboardFilter_guifocus_check['state'] = (this.cfg_dashboardFormat.get() == 'processed') and tk.NORMAL or tk.DISABLED
    this.dashboardPipFormat_button['state'] = this.dashboardFilter_latitude_check['state'] = this.dashboardFilter_longitude_check['state'] = this.dashboardFilter_heading_check['state'] = this.dashboardFilter_altitude_check['state'] = (this.cfg_dashboardFormat.get() == 'processed') and tk.NORMAL or tk.DISABLED



def prefs_changed():
    print "Telemetry: Prefs Changed"

    config.set("Telemetry-BrokerAddress", this.cfg_brokerAddress.get())
    config.set("Telemetry-BrokerPort", this.cfg_brokerPort.get())
    config.set("Telemetry-BrokerKeepalive", this.cfg_brokerKeepalive.get())
    config.set("Telemetry-BrokerQoS", this.cfg_brokerQoS.get())
    config.set("Telemetry-DashboardFormat", this.cfg_dashboardFormat.get())
    config.set("Telemetry-DashboardFlagFormat", this.cfg_dashboardFlagFormat.get())
    config.set("Telemetry-DashboardPipFormat", this.cfg_dashboardPipFormat.get())

    df = {}
    for key in this.dashboardFilter:
        df[key] = this.dashboardFilter[key].get() and 1
    config.set("Telemetry-DashboardFilter", json.dumps(df))

    stopTelemetry()
    startTelemetry()


def journal_entry(cmdr, system, station, entry):
    telemetry.publish("edmc/journal", payload=json.dumps(entry), qos=0, retain=False)
    print "Telemetry: Journal Entry Received"

# dashboard status
def dashboard_entry(cmdr, is_beta, entry):
    # if 'raw' dashboard status has been requested, publish the whole json string
    if this.cfg_dashboardFormat.get() == 'raw':
        telemetry.publish("edmc/dashboard", payload=json.dumps(entry), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
    
    # if 'processed' dashboard status has been requested, format with topics and filter as specified 
    else:
        for key in entry:
            # always ignore these keys
            if key == 'timestamp' or key == 'event':
                continue
        
            # publish any updated data that has been requested via configuration options
            if this.dashboardFilter.has_key(key) and this.dashboardFilter[key].get() == 1 and (not this.currentStatus.has_key(key) or this.currentStatus[key] != entry[key]):
                if key == 'Flags' and this.cfg_dashboardFlagFormat.get() == 'discrete':
                    if not this.currentStatus.has_key(key):
                        oldFlags = ~entry[key] & 0x07FFFFFF
                    else:
                        oldFlags = this.currentStatus[key]
                    newFlags = entry[key]
                    for bit in xrange(32):
                        mask = 1 << bit
                        if (oldFlags ^ newFlags) & mask:
                            telemetry.publish("edmc/dashboard/Flags/" + STATUS_FLAG[bit], payload=(newFlags & mask) and 1, qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()        
                elif key == 'Pips' and this.cfg_dashboardPipFormat.get() == 'discrete':
                    telemetry.publish("edmc/dashboard/Pips/sys", payload=str(entry[key][0]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                    telemetry.publish("edmc/dashboard/Pips/eng", payload=str(entry[key][1]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                    telemetry.publish("edmc/dashboard/Pips/wep", payload=str(entry[key][2]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()                    
                else:                
                    telemetry.publish("edmc/dashboard/" + str(key), payload=str(entry[key]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                this.currentStatus[key] = entry[key]


def loadConfiguration():
    this.cfg_brokerAddress = tk.StringVar(value=config.get("Telemetry-BrokerAddress"))
    if not cfg_brokerAddress.get():
        cfg_brokerAddress.set(DEFAULT_BROKER_ADDRESS)
    this.cfg_brokerPort = tk.IntVar(value=config.getint("Telemetry-BrokerPort"))
    if not cfg_brokerPort.get():
        cfg_brokerPort.set(DEFAULT_BROKER_PORT)
    this.cfg_brokerKeepalive = tk.IntVar(value=config.getint("Telemetry-BrokerKeepalive"))
    if not cfg_brokerKeepalive.get():
        cfg_brokerKeepalive.set(DEFAULT_BROKER_KEEPALIVE)
    this.cfg_brokerQoS = tk.IntVar(value=config.getint("Telemetry-BrokerQoS"))
    if not cfg_brokerQoS.get() or cfg_brokerQos.get() < 0 or cfg_brokerQoS.get() > 2:
        cfg_brokerQoS.set(DEFAULT_BROKER_QOS)
    this.cfg_dashboardFormat = tk.StringVar(value=config.get("Telemetry-DashboardFormat"))
    if not cfg_dashboardFormat.get():
        cfg_dashboardFormat.set(DEFAULT_DASHBOARD_FORMAT)
    this.cfg_dashboardFlagFormat = tk.StringVar(value=config.get("Telemetry-DashboardFlagFormat"))
    if not cfg_dashboardFlagFormat.get():
        cfg_dashboardFlagFormat.set(DEFAULT_FLAG_FORMAT)
    this.cfg_dashboardPipFormat = tk.StringVar(value=config.get("Telemetry-DashboardPipFormat"))
    if not cfg_dashboardPipFormat.get():
        cfg_dashboardPipFormat.set(DEFAULT_PIP_FORMAT)
    this.cfg_dashboardFilter = tk.StringVar(value=config.get("Telemetry-DashboardFilter"))
    if not cfg_dashboardFilter.get():
        cfg_dashboardFilter.set(json.dumps(DEFAULT_DASHBOARD_FILTER))
    this.dashboardFilter = json.loads(this.cfg_dashboardFilter.get())
    for key in this.dashboardFilter:
        this.dashboardFilter[key] = tk.IntVar(value=int(this.dashboardFilter[key]) and 1)


def telemetryCallback_on_connect(client, userdata, flags, rc):
    this.status['text'] = 'Connected'
    this.status['state'] = tk.NORMAL
    print("Connected with result code "+str(rc))

def telemetryCallback_on_disconnect(client, userdata, rc):
    this.status['text'] = 'Offline'
    this.status['state'] = tk.DISABLED
    print("Disconnected with result code "+str(rc))

def telemetryCallback_on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def telemetryCallback_on_publish(client, userdata, mid):
    print("> Published Message ID "+str(mid))

def initializeTelemetry():
    this.currentStatus = {}
    #this.currentStatus['Flags'] = 0
    this.telemetry = mqtt.Client(TELEMETRY_CLIENTID)
    telemetry.on_connect = telemetryCallback_on_connect
    telemetry.on_disconnect = telemetryCallback_on_disconnect
    telemetry.on_message = telemetryCallback_on_message
    telemetry.on_publish = telemetryCallback_on_publish
    startTelemetry()

def startTelemetry():
    telemetry.connect_async(this.cfg_brokerAddress.get(), this.cfg_brokerPort.get(), this.cfg_brokerKeepalive.get())
    telemetry.loop_start()

def stopTelemetry():
    telemetry.disconnect()
    telemetry.loop_stop()