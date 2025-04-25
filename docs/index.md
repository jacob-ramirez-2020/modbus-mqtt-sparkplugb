---
title: Modbus to MQTT SparkplugB
layout: default
---

# Modbus to MQTT SparkplugB

This is the documentation site for the **Modbus to MQTT SparkplugB Transmitter**.

## Overview

This tool collects Modbus RTU/TCP data and publishes SparkplugB-compliant payloads to an MQTT broker.

## Features

- Modbus RTU & TCP support
- MQTT SparkplugB publishing
- Deadband filtering
- Historical buffering with SQLite
- Reconnect and replay logic
- Secure MQTT (TLS planned)
- Configurable via API and future web UI

## Roadmap

Refer to the [README](../README.md) for detailed roadmap items and project status.

## Getting Started

```bash
pip install -r requirements.txt
python main.py
```

Make sure your `config.db` contains MQTT broker settings and tag definitions.

---

© 2025 Jacob Ramirez
