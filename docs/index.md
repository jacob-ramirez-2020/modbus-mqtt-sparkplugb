<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Modbus to MQTT SparkplugB</title>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <style>
    body {
      font-family: Arial, sans-serif;
      background-color: #111;
      color: #eee;
      margin: 0;
      padding: 2rem;
      line-height: 1.6;
    }
    h1, h2, h3 {
      color: #32FF00;
    }
    a {
      color: #01A2D9;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
    }
    img {
      max-width: 100%;
      height: auto;
      margin: 1rem 0;
    }
    code {
      background-color: #222;
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-family: monospace;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Modbus to MQTT SparkplugB</h1>
    <p>This lightweight Python application reads data from Modbus RTU/TCP devices and publishes it to an MQTT broker using the SparkplugB protocol. It's designed for industrial edge deployments, with buffering, reconnect logic, and deadband support built in.</p>

    <h2>🚀 Features</h2>
    <ul>
      <li>Modbus RTU & TCP support</li>
      <li>MQTT SparkplugB publishing</li>
      <li>Deadband filtering</li>
      <li>Historical buffering with SQLite</li>
      <li>Reconnect and replay logic</li>
      <li>API-based logging control</li>
    </ul>

    <h2>🧠 Architecture Diagram</h2>
    <img src="docs/assets/architecture_diagram.png" alt="Architecture Diagram" />

    <h2>🛠 Roadmap</h2>
    <ul>
      <li>Web-based config editor</li>
      <li>TLS cert file upload support</li>
      <li>Switch to config files for Git tracking</li>
      <li>Docker + service deployment</li>
      <li>Siemens S7 and OPC-UA support</li>
    </ul>

    <h2>📄 Documentation</h2>
    <p>The full documentation is available in the <a href="https://github.com/jacob-ramirez-2020/modbus-mqtt-sparkplugb">GitHub repository</a>.</p>

    <h2>👨‍💻 Author</h2>
    <p><strong>Jacob Ramirez</strong><br>
    SCADA & IIoT Developer | Cloud Architect<br>
    <a href="https://github.com/jacob-ramirez-2020">GitHub Profile</a></p>
  </div>
</body>
</html>
