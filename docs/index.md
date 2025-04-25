<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Modbus to MQTT SparkplugB</title>
    <link rel="icon" href="favicon.ico" type="image/x-icon">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
      tailwind.config = {
        theme: {
          extend: {
            colors: {
              primary: '#01A2D9',
              accent: '#32FF00',
              dark: '#121212',
              muted: '#1E1E1E',
            }
          }
        }
      }
    </script>
  </head>
  <body class="bg-dark text-white font-sans">
    <header class="p-6 bg-muted shadow-md">
      <div class="max-w-5xl mx-auto flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <img src="assets/logo-placeholder.png" alt="Logo" class="h-10 w-10 rounded-full" />
          <h1 class="text-2xl font-bold">Modbus MQTT Transmitter</h1>
        </div>
        <nav class="space-x-6">
          <a href="#overview" class="hover:underline">Overview</a>
          <a href="#features" class="hover:underline">Features</a>
          <a href="#architecture" class="hover:underline">Architecture</a>
          <a href="#roadmap" class="hover:underline">Roadmap</a>
        </nav>
      </div>
    </header>

    <main class="max-w-5xl mx-auto p-6">
      <section id="overview" class="text-center py-12">
        <h2 class="text-4xl font-bold mb-4">Modbus to MQTT SparkplugB Transmitter</h2>
        <p class="text-lg">Python-based edge application that reads Modbus data and publishes it via MQTT SparkplugB with buffering and deadband logic.</p>
        <div class="mt-6">
          <a href="https://github.com/jacob-ramirez-2020/modbus-mqtt-sparkplugb" class="bg-primary hover:bg-blue-700 px-4 py-2 rounded">View on GitHub</a>
        </div>
      </section>

      <section id="features" class="py-12">
        <h3 class="text-2xl font-semibold mb-4 text-primary">Features</h3>
        <ul class="list-disc list-inside space-y-2">
          <li>Modbus RTU & TCP support</li>
          <li>MQTT SparkplugB publishing</li>
          <li>Deadband filtering</li>
          <li>Buffered publishing with SQLite</li>
          <li>Reconnect logic & historical resend</li>
          <li>API-based logging configuration</li>
        </ul>
      </section>

      <section id="architecture" class="py-12">
        <h3 class="text-2xl font-semibold mb-4 text-primary">System Architecture</h3>
        <img src="docs/assets/architecture_diagram.png" alt="Architecture Diagram" class="rounded shadow-md" />
      </section>

      <section id="roadmap" class="py-12">
        <h3 class="text-2xl font-semibold mb-4 text-primary">Roadmap</h3>
        <ul class="list-disc list-inside space-y-2">
          <li>Web-based configuration editor</li>
          <li>TLS cert file upload support</li>
          <li>Switch from SQLite to file-based configs (TOML/JSON/YAML)</li>
          <li>Docker support and systemd service</li>
          <li>Siemens S7 and OPC-UA integration</li>
        </ul>
      </section>
    </main>

    <footer class="bg-muted p-4 text-center text-sm text-gray-400">
      &copy; 2025 Jacob Ramirez. All rights reserved.
    </footer>
  </body>
</html>
