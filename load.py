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
try:
    # for Python2
    import Tkinter as tk
    import ttk
except ImportError:
    # for Python3
    import tkinter as tk
    from tkinter import ttk
import myNotebook as nb
from config import config
from ttkHyperlinkLabel import HyperlinkLabel

import paho.mqtt.client as mqtt
import json

TELEMETRY_VERSION = "0.2.0"
TELEMETRY_CLIENTID = "EDMCTelemetryPlugin"

# default values for initial population of configuration
DEFAULT_BROKER_ADDRESS = '127.0.0.1'
DEFAULT_BROKER_PORT = 1883
DEFAULT_BROKER_KEEPALIVE = 60
DEFAULT_BROKER_QOS = 0
DEFAULT_ROOT_TOPIC = 'telemetry'
DEFAULT_BROKER_USERNAME = ""
DEFAULT_BROKER_PASSWORD = ""
DEFAULT_DASHBOARD_FORMAT = 'raw'
DEFAULT_DASHBOARD_TOPIC = 'dashboard'
DEFAULT_DASHBOARD_FILTER_JSON = "{\"Flags\": [1, \"flags\"], \"Pips\": [0, \"pips\"], \"FireGroup\": [0, \"firegroup\"], \"GuiFocus\": [0, \"guifocus\"], \"Latitude\": [0, \"latitude\"], \"Longitude\": [0, \"longitude\"], \"Heading\": [0, \"heading\"], \"Altitude\": [0, \"altitude\"], \"Fuel\": [0, \"fuel\"], \"Cargo\": [0, \"cargo\"]}"
DEFAULT_FLAG_FORMAT = 'combined'
DEFAULT_FLAG_TOPIC = 'flag'
DEFAULT_FLAG_FILTER_JSON = "[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]"
DEFAULT_FLAG_TOPICS_JSON = "[\"docked\", \"landed\", \"landinggear\", \"shields\", \"supercruise\", \"flightassistoff\", \"hardpoints\", \"inwing\", \"lights\", \"cargoscoop\", \"silentrunning\", \"scooping\", \"srvhandbrake\", \"srvusingturret\", \"srvturretretracted\", \"srvdriveassist\", \"fsdmasslocked\", \"fsdcharging\", \"fsdcooldown\", \"lowfuel\", \"overheating\", \"haslatlong\", \"isindanger\", \"beinginterdicted\", \"inmainship\", \"infighter\", \"insrv\", \"hudinanalysis\", \"nightvision\", \"bit29\", \"bit30\", \"bit31\"]"
DEFAULT_FUEL_FORMAT = 'combined'
DEFAULT_FUEL_TOPIC = 'fuel'
DEFAULT_FUEL_MAIN_TOPIC = 'main'
DEFAULT_FUEL_RESERVOIR_TOPIC = 'reservoir'
DEFAULT_PIP_FORMAT = 'combined'
DEFAULT_PIP_TOPIC = 'pips'
DEFAULT_PIP_SYS_TOPIC = 'sys'
DEFAULT_PIP_ENG_TOPIC = 'eng'
DEFAULT_PIP_WEP_TOPIC = 'wep'

DEFAULT_JOURNAL_FORMAT = 'raw'
DEFAULT_JOURNAL_TOPIC = 'journal'

this = sys.modules[__name__] # for holding globals
this._connected = False
this.status: tk.Label = None

# Plugin startup
def plugin_start():
    loadConfiguration()    
    this._connected = False;
    #print "Telemetry: Started"
    return "Telemetry"

def plugin_start3(plugin_dir):
    return plugin_start()


# Plugin shutdown
def plugin_stop():
    stopTelemetry()
    #print "Telemetry: Stopped"

# Show broker connection status on main UI
def plugin_app(parent):
    label = tk.Label(parent, text="Telemetry")
    this.status = tk.Label(parent, anchor=tk.W, text="Offline", state=tk.DISABLED)
    this.status.bind_all('<<BrokerStatus>>',update_status)
    
    #Start telemetry after UI has been created
    initializeTelemetry()
    
    return (label, this.status)
    
# Settings tab for plugin
def plugin_prefs(parent,cmdr,is_beta):
    
    # set up the primary frame for our assigned notebook tab
    frame = nb.Frame(parent) 
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(1, weight=1)

    # create a style that will be used for telemetry's settings notebook
    style = ttk.Style()
    style.configure('TNB.TNotebook', background=nb.Label().cget('background'))
    style.configure('TNB.TLabelFrame', background=nb.Label().cget('background'))
    PADX = 10
    PADY = 2

    # add our own notebook to hold all the telemetry options
    tnb = ttk.Notebook(frame, style='TNB.TNotebook')
    tnb.grid(columnspan=2, padx=8, sticky=tk.NSEW)
    tnb.columnconfigure(1, weight=1)
    
    # telemetry settings tab for mqtt options
    tnbMain = nb.Frame(tnb)
    tnbMain.columnconfigure(1, weight=1)
    nb.Label(tnbMain, text="Broker Address").grid(padx=PADX, row=1, sticky=tk.W)
    nb.Entry(tnbMain, textvariable=this.cfg_brokerAddress).grid(padx=PADX, pady=PADY, row=1, column=1, sticky=tk.EW)
    nb.Label(tnbMain, text="Port").grid(padx=PADX, row=2, sticky=tk.W)
    nb.Entry(tnbMain, textvariable=this.cfg_brokerPort).grid(padx=PADX, pady=PADY, row=2, column=1, sticky=tk.EW)
    nb.Label(tnbMain, text="Keepalive").grid(padx=PADX, row=3, sticky=tk.W)
    nb.Entry(tnbMain, textvariable=this.cfg_brokerKeepalive).grid(padx=PADX, pady=PADY, row=3, column=1, sticky=tk.EW)
    nb.Label(tnbMain, text='QoS').grid(padx=PADX, row=4, sticky=tk.W)
    nb.OptionMenu(tnbMain, this.cfg_brokerQoS, this.cfg_brokerQoS.get(), 0, 1, 2).grid(padx=PADX, pady=PADY, row=4, column=1, sticky=tk.W)
    nb.Label(tnbMain, text="Root Topic").grid(padx=PADX, row=5, sticky=tk.W)
    nb.Entry(tnbMain, textvariable=this.cfg_rootTopic).grid(padx=PADX, pady=PADY, row=5, column=1, sticky=tk.EW)    
    nb.Label(tnbMain, text="Username").grid(padx=PADX, row=6, sticky=tk.W)
    nb.Entry(tnbMain, textvariable=this.cfg_brokerUsername).grid(padx=PADX, pady=PADY, row=6, column=1, sticky=tk.EW)
    nb.Label(tnbMain, text="Password").grid(padx=PADX, row=7, sticky=tk.W)
    nb.Entry(tnbMain, textvariable=this.cfg_brokerPassword).grid(padx=PADX, pady=PADY, row=7, column=1, sticky=tk.EW)

    # telemetry settings tab for dashboard status items    
    tnbDashboard = nb.Frame(tnb) 
    tnbDashboard.columnconfigure(1, weight=1)
    nb.Label(tnbDashboard, text='Publish Format').grid(padx=PADX, row=1, column=0, sticky=tk.W)
    dbOptions = ['none', 'raw', 'processed']
    nb.OptionMenu(tnbDashboard, this.cfg_dashboardFormat, this.cfg_dashboardFormat.get(), *dbOptions, command=prefStateChange).grid(padx=PADX, row=1, column=1, sticky=tk.W)
    dbTopic_label = nb.Label(tnbDashboard, text='Topic')
    dbTopic_label.grid(padx=PADX, row=1, column=2, sticky=tk.W)
    dbTopic_entry = nb.Entry(tnbDashboard, textvariable=this.cfg_dashboardTopic)
    dbTopic_entry.grid(padx=PADX, row=1, column=3, sticky=tk.W)

    this.tnbDbStatus = tk.LabelFrame(tnbDashboard, text='Status', bg=nb.Label().cget('background'))
    tnbDbStatus.grid(padx=PADX, row=2, column=0, columnspan=4, sticky=tk.NSEW)
    
    nb.Checkbutton(tnbDbStatus, text="Flags", variable=this.cfg_dashboardFilters['Flags'], command=prefStateChange).grid(padx=PADX, row=1, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Flags']).grid(padx=PADX, row=1, column=1, sticky=tk.W)
    nb.Checkbutton(tnbDbStatus, text="GuiFocus", variable=this.cfg_dashboardFilters['GuiFocus'], command=prefStateChange).grid(padx=PADX, row=1, column=2, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['GuiFocus']).grid(padx=PADX, row=1, column=3, sticky=tk.W)

    nb.Label(tnbDbStatus, text="Flag Format").grid(padx=PADX, row=2, sticky=tk.W)
    dbFlagOptions = ['combined', 'discrete']
    nb.OptionMenu(tnbDbStatus, this.cfg_dashboardFlagFormat, this.cfg_dashboardFlagFormat.get(), *dbFlagOptions, command=prefStateChange).grid(padx=PADX, row=2, column=1, sticky=tk.W)
    nb.Checkbutton(tnbDbStatus, text="Latitude", variable=this.cfg_dashboardFilters['Latitude'], command=prefStateChange).grid(padx=PADX, row=2, column=2, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Latitude']).grid(padx=PADX, row=2, column=3, sticky=tk.W)

    nb.Checkbutton(tnbDbStatus, text="Pips", variable=this.cfg_dashboardFilters['Pips'], command=prefStateChange).grid(padx=PADX, row=3, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Pips']).grid(padx=PADX, row=3, column=1, sticky=tk.W)
    nb.Checkbutton(tnbDbStatus, text="Longitude", variable=this.cfg_dashboardFilters['Longitude'], command=prefStateChange).grid(padx=PADX, row=3, column=2, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Longitude']).grid(padx=PADX, row=3, column=3, sticky=tk.W)

    nb.Label(tnbDbStatus, text="Pip Format").grid(padx=PADX, row=4, sticky=tk.W)
    dbPipOptions = ['combined', 'discrete']
    nb.OptionMenu(tnbDbStatus, this.cfg_dashboardPipFormat, this.cfg_dashboardPipFormat.get(), *dbPipOptions, command=prefStateChange).grid(padx=PADX, row=4, column=1, sticky=tk.W)
    nb.Checkbutton(tnbDbStatus, text="Heading", variable=this.cfg_dashboardFilters['Heading'], command=prefStateChange).grid(padx=PADX, row=4, column=2, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Heading']).grid(padx=PADX, row=4, column=3, sticky=tk.W)
    
    nb.Checkbutton(tnbDbStatus, text="Fuel", variable=this.cfg_dashboardFilters['Fuel'], command=prefStateChange).grid(padx=PADX, row=5, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Fuel']).grid(padx=PADX, row=5, column=1, sticky=tk.W)
    nb.Checkbutton(tnbDbStatus, text="FireGroup", variable=this.cfg_dashboardFilters['FireGroup'], command=prefStateChange).grid(padx=PADX, pady=(0,8), row=5, column=2, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['FireGroup']).grid(padx=PADX, pady=(0,8), row=5, column=3, sticky=tk.W)
    
    nb.Label(tnbDbStatus, text="Fuel Format").grid(padx=PADX, row=6, sticky=tk.W)
    dbFuelOptions = ['combined', 'discrete']
    nb.OptionMenu(tnbDbStatus, this.cfg_dashboardFuelFormat, this.cfg_dashboardFuelFormat.get(), *dbFuelOptions, command=prefStateChange).grid(padx=PADX, row=6, column=1, sticky=tk.W)
    nb.Checkbutton(tnbDbStatus, text="Altitude", variable=this.cfg_dashboardFilters['Altitude'], command=prefStateChange).grid(padx=PADX, pady=(0,8), row=6, column=2, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Altitude']).grid(padx=PADX, pady=(0,8), row=6, column=3, sticky=tk.W)

    nb.Checkbutton(tnbDbStatus, text="Cargo", variable=this.cfg_dashboardFilters['Cargo'], command=prefStateChange).grid(padx=PADX, row=7, sticky=tk.W)
    nb.Entry(tnbDbStatus, textvariable=this.cfg_dashboardTopics['Cargo']).grid(padx=PADX, row=7, column=1, sticky=tk.W)

    this.tnbDbPips = tk.LabelFrame(tnbDashboard, text='Pip Topics', bg=nb.Label().cget('background'))
    tnbDbPips.grid(padx=PADX, pady=(8,0), row=8, column=0, columnspan=4, sticky=tk.NSEW)
    tnbDbPips.columnconfigure(1, weight=1)

    nb.Label(tnbDbPips, text="Sys").grid(padx=PADX, pady=(0,8), row=1, sticky=tk.W)
    nb.Entry(tnbDbPips, textvariable=this.cfg_dashboardPipSysTopic).grid(padx=PADX, pady=(0,8), row=1, column=1, sticky=tk.W)
    nb.Label(tnbDbPips, text="Eng").grid(padx=PADX, pady=(0,8), row=1, column=2, sticky=tk.W)
    nb.Entry(tnbDbPips, textvariable=this.cfg_dashboardPipEngTopic).grid(padx=PADX, pady=(0,8), row=1, column=3, sticky=tk.W)
    nb.Label(tnbDbPips, text="Wep").grid(padx=PADX, pady=(0,8), row=1, column=4, sticky=tk.W)
    nb.Entry(tnbDbPips, textvariable=this.cfg_dashboardPipWepTopic).grid(padx=PADX, pady=(0,8), row=1, column=5, sticky=tk.W)

    this.tnbDbFuel = tk.LabelFrame(tnbDashboard, text='Fuel Topics', bg=nb.Label().cget('background'))
    tnbDbFuel.grid(padx=PADX, pady=(8,0), row=9, column=0, columnspan=4, sticky=tk.NSEW)
    tnbDbFuel.columnconfigure(1, weight=1)

    nb.Label(tnbDbFuel, text="Main").grid(padx=PADX, pady=(0,8), row=1, sticky=tk.W)
    nb.Entry(tnbDbFuel, textvariable=this.cfg_dashboardFuelMainTopic).grid(padx=PADX, pady=(0,8), row=1, column=1, sticky=tk.W)
    nb.Label(tnbDbFuel, text="Reservoir").grid(padx=PADX, pady=(0,8), row=1, column=2, sticky=tk.W)
    nb.Entry(tnbDbFuel, textvariable=this.cfg_dashboardFuelReservoirTopic).grid(padx=PADX, pady=(0,8), row=1, column=3, sticky=tk.W)

    # telemetry settings tab for discrete flags
    tnbFlags = nb.Frame(tnb)
    this.tnbFlagsLF = tk.LabelFrame(tnbFlags, text='Discrete Flag Settings', bg=nb.Label().cget('background'))
    tnbFlagsLF.grid(padx=PADX, row=2, column=0, columnspan=4, sticky=tk.NSEW)
    for i in range(4):
        tnbFlags.grid_columnconfigure(i, weight=1, uniform="telemetry_flags")
    flagLabels = [ 'Docked (Landing Pad)', 'Landed (Planet)', 'Landing Gear Down', 'Shields Up', 'Supercruise', 'FlightAssist Off', 'Hardpoints Deployed', 'In Wing', 'Lights On', 'Cargo Scoop Deployed', 'Silent Running', 'Scooping Fuel', 'SRV Handbrake', 'SRV Using Turret', 'SRV Turret Retracted', 'SRV DriveAssist', 'FSD Mass Locked', 'FSD Charging', 'FSD Cooldown', 'Low Fuel (<25%)', 'Overheating (>100%)', 'Has Lat Long', 'Is In Danger', 'Being Interdicted', 'In Main Ship', 'In Fighter', 'In SRV', 'HUD in Analysis mode', 'Night Vision', 'Bit 29', 'Bit 30', 'Bit 31' ] 
    for i in range(16):
        for j in range(2):
            nb.Checkbutton(tnbFlagsLF, text=flagLabels[i + (16 * j)], variable=this.cfg_dashboardFlagFilters[i + (16 * j)]).grid(padx=PADX, pady=PADY, row=i, column=(0 + (2 * j)), sticky=tk.W)
            nb.Entry(tnbFlagsLF, textvariable=this.cfg_dashboardFlagTopics[i + (16 * j)]).grid(padx=PADX, pady=PADY, row=i, column=(1 + (2 * j)), sticky=tk.W)

    # telemetry settings tab for journal entry items    
    tnbJournal = nb.Frame(tnb)
    tnbJournal.columnconfigure(1, weight=1)
    nb.Label(tnbJournal, text='Publish Format').grid(padx=PADX, row=1, column=0, sticky=tk.W)
    jOptions = ['none', 'raw'] #, 'processed'] # note that the 'processed' setting will be added at a later time
    nb.OptionMenu(tnbJournal, this.cfg_journalFormat, this.cfg_journalFormat.get(), *jOptions, command=prefStateChange).grid(padx=PADX, row=1, column=1, sticky=tk.W)
    jTopic_label = nb.Label(tnbJournal, text='Topic')
    jTopic_label.grid(padx=PADX, row=1, column=2, sticky=tk.W)
    jTopic_entry = nb.Entry(tnbJournal, textvariable=this.cfg_journalTopic)
    jTopic_entry.grid(padx=PADX, row=1, column=3, sticky=tk.W)
    
    # add the preferences tabs we've created to our assigned EDMC settings tab
    tnb.add(tnbMain, text = "MQTT")
    tnb.add(tnbDashboard, text = "Dashboard")
    tnb.add(tnbFlags, text = "Flags")
    tnb.add(tnbJournal, text = "Journal")
            
    # footer with github link and plugin version
    HyperlinkLabel(frame, text='https://github.com/fasteddy516/EDMC-Telemetry/', background=nb.Label().cget('background'), url='https://github.com/fasteddy516/EDMC-Telemetry/', underline=True).grid(padx=PADX, pady=(1,4), row=2, column=0, sticky=tk.W)
    nb.Label(frame, text="Plugin Version " + TELEMETRY_VERSION).grid(padx=PADX, pady=(1, 4), row=2, column=1, sticky=tk.E)

    prefStateChange()

    return frame


# Update enabled/disabled states of configuration elements
def prefStateChange(format='processed'):
    if format == 'raw':
        this.currentStatus = {}

    newState = (this.cfg_dashboardFormat.get() == 'processed') and tk.NORMAL or tk.DISABLED
    for element in this.tnbDbStatus.winfo_children():
        element['state'] = newState

    newState = (this.cfg_dashboardPipFormat.get() == 'discrete' and this.cfg_dashboardFormat.get() == 'processed' and this.cfg_dashboardFilters['Pips'].get()) and tk.NORMAL or tk.DISABLED
    for element in this.tnbDbPips.winfo_children():
        element['state'] = newState

    newState = (this.cfg_dashboardFuelFormat.get() == 'discrete' and this.cfg_dashboardFormat.get() == 'processed' and this.cfg_dashboardFilters['Fuel'].get()) and tk.NORMAL or tk.DISABLED
    for element in this.tnbDbFuel.winfo_children():
        element['state'] = newState

    newState = (this.cfg_dashboardFlagFormat.get() == 'discrete' and this.cfg_dashboardFormat.get() == 'processed' and this.cfg_dashboardFilters['Flags'].get()) and tk.NORMAL or tk.DISABLED
    for element in this.tnbFlagsLF.winfo_children():
        element['state'] = newState
    

# save user settings
def prefs_changed(cmdr, is_beta):
    # broker
    config.set("Telemetry-BrokerAddress", this.cfg_brokerAddress.get())
    config.set("Telemetry-BrokerPort", this.cfg_brokerPort.get())
    config.set("Telemetry-BrokerKeepalive", this.cfg_brokerKeepalive.get())
    config.set("Telemetry-BrokerQoS", this.cfg_brokerQoS.get())
    config.set("Telemetry-RootTopic", this.cfg_rootTopic.get())
    config.set("Telemetry-BrokerUsername", this.cfg_brokerUsername.get())
    config.set("Telemetry-BrokerPassword", this.cfg_brokerPassword.get())

    # dashboard    
    config.set("Telemetry-DashboardFormat", this.cfg_dashboardFormat.get())
    config.set("Telemetry-DashboardTopic", this.cfg_dashboardTopic.get())
    dfTemp = {}
    for key in this.cfg_dashboardFilters:
        dfTemp[key] = (this.cfg_dashboardFilters[key].get() and 1, this.cfg_dashboardTopics[key].get())
    config.set("Telemetry-DashboardFilterJSON", json.dumps(dfTemp))    
    
    # dashboard - status flags
    config.set("Telemetry-DashboardFlagFormat", this.cfg_dashboardFlagFormat.get())
    config.set("Telemetry-DashboardFlagTopic", this.cfg_dashboardFlagTopic.get())    
    dffTemp = []
    dftTemp = []
    for bit in range(32):
        dffTemp.append(this.cfg_dashboardFlagFilters[bit].get() and 1)
        dftTemp.append(this.cfg_dashboardFlagTopics[bit].get())
    config.set("Telemetry-DashboardFlagFilterJSON", json.dumps(dffTemp))
    config.set("Telemetry-DashboardFlagTopicsJSON", json.dumps(dftTemp))    
    
    # dashboard - fuel
    config.set("Telemetry-DashboardFuelFormat", this.cfg_dashboardFuelFormat.get())
    config.set("Telemetry-DashboardFuelTopic", this.cfg_dashboardFuelTopic.get())    
    config.set("Telemetry-DashboardFuelMainTopic", this.cfg_dashboardFuelMainTopic.get())    
    config.set("Telemetry-DashboardFuelReservoirTopic", this.cfg_dashboardFuelReservoirTopic.get())    
    
    # dashboard - pips
    config.set("Telemetry-DashboardPipFormat", this.cfg_dashboardPipFormat.get())
    config.set("Telemetry-DashboardPipTopic", this.cfg_dashboardPipTopic.get())
    config.set("Telemetry-DashboardPipSysTopic", this.cfg_dashboardPipSysTopic.get())    
    config.set("Telemetry-DashboardPipEngTopic", this.cfg_dashboardPipEngTopic.get())    
    config.set("Telemetry-DashboardPipWepTopic", this.cfg_dashboardPipWepTopic.get())    

    # journal    
    config.set("Telemetry-JournalFormat", this.cfg_journalFormat.get())
    config.set("Telemetry-JournalTopic", this.cfg_journalTopic.get())

    # restart mqtt connections using new settings
    stopTelemetry()
    startTelemetry()


# load user settings using defaults if necessary
def loadConfiguration():
    # broker
    this.cfg_brokerAddress = tk.StringVar(value=config.get_str("Telemetry-BrokerAddress"))
    if not cfg_brokerAddress.get():
        cfg_brokerAddress.set(DEFAULT_BROKER_ADDRESS)
    this.cfg_brokerPort = tk.IntVar(value=config.get_int("Telemetry-BrokerPort"))
    if not cfg_brokerPort.get():
        cfg_brokerPort.set(DEFAULT_BROKER_PORT)
    this.cfg_brokerKeepalive = tk.IntVar(value=config.get_int("Telemetry-BrokerKeepalive"))
    if not cfg_brokerKeepalive.get():
        cfg_brokerKeepalive.set(DEFAULT_BROKER_KEEPALIVE)
    this.cfg_brokerQoS = tk.IntVar(value=config.get_int("Telemetry-BrokerQoS"))
    if cfg_brokerQoS.get() < 0 or cfg_brokerQoS.get() > 2:
        cfg_brokerQoS.set(DEFAULT_BROKER_QOS)
    this.cfg_rootTopic = tk.StringVar(value=config.get_str("Telemetry-RootTopic"))
    if not cfg_rootTopic.get():
        cfg_rootTopic.set(DEFAULT_ROOT_TOPIC)
    this.cfg_brokerUsername = tk.StringVar(value=config.get_str("Telemetry-BrokerUsername"))
    if not cfg_brokerUsername.get():
        cfg_brokerUsername.set(DEFAULT_BROKER_USERNAME)
    this.cfg_brokerPassword = tk.StringVar(value=config.get_str("Telemetry-BrokerPassword"))
    if not cfg_brokerPassword.get():
        cfg_brokerPassword.set(DEFAULT_BROKER_PASSWORD)

    # dashboard
    this.cfg_dashboardFormat = tk.StringVar(value=config.get_str("Telemetry-DashboardFormat"))
    if not cfg_dashboardFormat.get():
        cfg_dashboardFormat.set(DEFAULT_DASHBOARD_FORMAT)
    this.cfg_dashboardTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardTopic"))
    if not cfg_dashboardTopic.get():
        cfg_dashboardTopic.set(DEFAULT_DASHBOARD_TOPIC)
    this.cfg_dashboardFilters = {}
    this.cfg_dashboardTopics = {}
    jsonTemp = config.get_str("Telemetry-DashboardFilterJSON")
    if not jsonTemp:
        dfTemp = json.loads(DEFAULT_DASHBOARD_FILTER_JSON)
    else:
        dfTemp = json.loads(jsonTemp)
    for key in dfTemp:
        this.cfg_dashboardFilters[key] = tk.IntVar(value=int(dfTemp[key][0]) and 1)
        this.cfg_dashboardTopics[key] = tk.StringVar(value=str(dfTemp[key][1]))
    
    # dashboard - status flags
    this.cfg_dashboardFlagFormat = tk.StringVar(value=config.get_str("Telemetry-DashboardFlagFormat"))
    if not cfg_dashboardFlagFormat.get():
        cfg_dashboardFlagFormat.set(DEFAULT_FLAG_FORMAT)
    this.cfg_dashboardFlagTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardFlagTopic"))
    if not cfg_dashboardFlagTopic.get():
        cfg_dashboardFlagTopic.set(DEFAULT_FLAG_TOPIC)
    
    jsonTemp = config.get_str("Telemetry-DashboardFlagFilterJSON")
    if not jsonTemp:
        dffTemp = json.loads(DEFAULT_FLAG_FILTER_JSON)
    else:
        dffTemp = json.loads(jsonTemp)
    this.cfg_dashboardFlagFilters = []
    for flag in dffTemp:
        this.cfg_dashboardFlagFilters.append(tk.IntVar(value=int(flag) and 1))
    jsonTemp = config.get_str("Telemetry-DashboardFlagTopicsJSON")
    if not jsonTemp:
        dftTemp = json.loads(DEFAULT_FLAG_TOPICS_JSON)
    else:
        dftTemp = json.loads(jsonTemp)
    this.cfg_dashboardFlagTopics = []
    for topic in dftTemp:
        this.cfg_dashboardFlagTopics.append(tk.StringVar(value=str(topic)))

    # dashboard - fuel
    this.cfg_dashboardFuelFormat = tk.StringVar(value=config.get_str("Telemetry-DashboardFuelFormat"))
    if not cfg_dashboardFuelFormat.get():
        cfg_dashboardFuelFormat.set(DEFAULT_FUEL_FORMAT)
    this.cfg_dashboardFuelTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardFuelTopic"))
    if not cfg_dashboardFuelTopic.get():
        cfg_dashboardFuelTopic.set(DEFAULT_FUEL_TOPIC)
    this.cfg_dashboardFuelMainTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardFuelMainTopic"))
    if not cfg_dashboardFuelMainTopic.get():
        cfg_dashboardFuelMainTopic.set(DEFAULT_FUEL_MAIN_TOPIC)
    this.cfg_dashboardFuelReservoirTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardFuelReservoirTopic"))
    if not cfg_dashboardFuelReservoirTopic.get():
        cfg_dashboardFuelReservoirTopic.set(DEFAULT_FUEL_RESERVOIR_TOPIC)

    # dashboard - pips
    this.cfg_dashboardPipFormat = tk.StringVar(value=config.get_str("Telemetry-DashboardPipFormat"))
    if not cfg_dashboardPipFormat.get():
        cfg_dashboardPipFormat.set(DEFAULT_PIP_FORMAT)
    this.cfg_dashboardPipTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardPipTopic"))
    if not cfg_dashboardPipTopic.get():
        cfg_dashboardPipTopic.set(DEFAULT_PIP_TOPIC)
    this.cfg_dashboardPipSysTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardPipSysTopic"))
    if not cfg_dashboardPipSysTopic.get():
        cfg_dashboardPipSysTopic.set(DEFAULT_PIP_SYS_TOPIC)
    this.cfg_dashboardPipEngTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardPipEngTopic"))
    if not cfg_dashboardPipEngTopic.get():
        cfg_dashboardPipEngTopic.set(DEFAULT_PIP_ENG_TOPIC)
    this.cfg_dashboardPipWepTopic = tk.StringVar(value=config.get_str("Telemetry-DashboardPipWepTopic"))
    if not cfg_dashboardPipWepTopic.get():
        cfg_dashboardPipWepTopic.set(DEFAULT_PIP_WEP_TOPIC)

    # journal 
    this.cfg_journalFormat = tk.StringVar(value=config.get_str("Telemetry-JournalFormat"))
    if not cfg_journalFormat.get():
        cfg_journalFormat.set(DEFAULT_JOURNAL_FORMAT)
    this.cfg_journalTopic = tk.StringVar(value=config.get_str("Telemetry-JournalTopic"))
    if not cfg_journalTopic.get():
        cfg_journalTopic.set(DEFAULT_JOURNAL_TOPIC)


# process player journal entries 
def journal_entry(cmdr, is_beta, system, station, entry, state):
    
    # if 'raw' journal status has been requested, publish the whole json string using the specified topic
    if this.cfg_journalFormat.get() == 'raw':
        telemetry.publish(cfg_rootTopic.get() + "/" + cfg_journalTopic.get(), payload=json.dumps(entry), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
    

# process dashboard status entries
def dashboard_entry(cmdr, is_beta, entry):

    # start building message topic
    dbTopic = cfg_rootTopic.get() + "/" + cfg_dashboardTopic.get()

    # if 'raw' dashboard status has been requested, publish the whole json string using the specified topic
    if this.cfg_dashboardFormat.get() == 'raw':
        telemetry.publish(dbTopic, payload=json.dumps(entry), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
    
    # if 'processed' dashboard status has been requested, format with topics and filter as specified 
    elif this.cfg_dashboardFormat.get() == 'processed':
        for key in entry: # scan through each key/value pair in the journal entry
            # always ignore these keys
            if key == 'timestamp' or key == 'event':
                continue
        
            # publish any updated data that has been requested via configuration options
            if this.cfg_dashboardFilters.has_key(key) and this.cfg_dashboardFilters[key].get() == 1 and (not this.currentStatus.has_key(key) or this.currentStatus[key] != entry[key]):
                
                # update topic for this particular status item
                myTopic = dbTopic + "/" + this.cfg_dashboardTopics[key].get()
                
                # additional processing for discrete flag states
                if key == 'Flags' and this.cfg_dashboardFlagFormat.get() == 'discrete':
                    if not this.currentStatus.has_key(key):
                        oldFlags = ~entry[key] & 0x07FFFFFF
                    else:
                        oldFlags = this.currentStatus[key]
                    newFlags = entry[key]
                    for bit in range(32):
                        mask = 1 << bit
                        if ((oldFlags ^ newFlags) & mask) and this.cfg_dashboardFlagFilters[bit].get():
                            telemetry.publish(myTopic + "/" + this.cfg_dashboardFlagTopics[bit].get(), payload=str((newFlags & mask) and 1), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()        
                
                # additional processing for discrete pip updates
                elif key == 'Pips' and this.cfg_dashboardPipFormat.get() == 'discrete':
                    telemetry.publish(myTopic + "/" + this.cfg_dashboardPipSysTopic.get(), payload=str(entry[key][0]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                    telemetry.publish(myTopic + "/" + this.cfg_dashboardPipEngTopic.get(), payload=str(entry[key][1]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                    telemetry.publish(myTopic + "/" + this.cfg_dashboardPipWepTopic.get(), payload=str(entry[key][2]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()                    
                              
                # additional processing for discrete pip updates
                elif key == 'Fuel':
                    if this.cfg_dashboardFuelFormat.get() == 'discrete':
                        telemetry.publish(myTopic + "/" + this.cfg_dashboardFuelMainTopic.get(), payload=str(entry[key]['FuelMain']), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                        telemetry.publish(myTopic + "/" + this.cfg_dashboardFuelReservoirTopic.get(), payload=str(entry[key]['FuelReservoir']), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                    else:
                        telemetry.publish(myTopic, payload=str(entry[key]['FuelMain']) + ", " + str(entry[key]['FuelReservoir']), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()                        

                # standard processing for most status updates
                else:                
                    telemetry.publish(myTopic, payload=str(entry[key]), qos=this.cfg_brokerQoS.get(), retain=False).wait_for_publish()
                
                # update internal tracking variable (used to filter unnecessary updates)
                this.currentStatus[key] = entry[key] 


def update_status(event=None) -> None:
    if this._connected == True:
        this.status['text'] = 'Connected'
        this.status['state'] = tk.NORMAL
    else:
        this.status['text'] = 'Offline'
        this.status['state'] = tk.DISABLED    


def telemetryCallback_on_connect(client, userdata, flags, rc):
    this._connected = True;
    this.status.event_generate('<<BrokerStatus>>', when="tail")
    #print("Connected with result code "+str(rc))

def telemetryCallback_on_disconnect(client, userdata, rc):
    if not config.shutting_down:
        this._connected = False;
        this.status.event_generate('<<BrokerStatus>>', when="tail")
    #print("Disconnected with result code "+str(rc))

def telemetryCallback_on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    pass

def telemetryCallback_on_publish(client, userdata, mid):
    #print("> Published Message ID "+str(mid))
    pass

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
    telemetry.on_disconnect = telemetryCallback_on_disconnect
    telemetry.username_pw_set(this.cfg_brokerUsername.get(),this.cfg_brokerPassword.get())
    telemetry.connect_async(this.cfg_brokerAddress.get(), this.cfg_brokerPort.get(), this.cfg_brokerKeepalive.get())
    telemetry.loop_start()

def stopTelemetry():
    this._connected = False;
    this.status.event_generate('<<BrokerStatus>>', when="tail")
    telemetry.on_disconnect = None
    telemetry.disconnect()
    telemetry.loop_stop()
