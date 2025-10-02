# gol

Ejemplo de asistente de tutoriales con IA y realidad aumentada.

Este repositorio incluye un script (`ar_tutorial.py`) que muestra la imagen de la cámara y superpone instrucciones paso a paso obtenidas mediante la API de OpenAI. Se requiere `opencv-python` y una clave de API válida.

Por defecto, el asistente te guía en el uso del editor de nodos de Blender, aunque puedes especificar cualquier otro programa. También es experto en FL Studio y te puede guiar para crear una canción desde cero.

```
python ar_tutorial.py --api-key TU_CLAVE             # Aprende nodos en Blender
python ar_tutorial.py "FL Studio" --api-key TU_CLAVE             # Crea una canción desde cero
python ar_tutorial.py "Nombre del Programa" --api-key TU_CLAVE  # Otro software
```

Presiona `n` para el siguiente paso y `q` para salir.

## Herramientas de audio

El script `guitar_tuner.py` permite:

* Afinar una guitarra en tiempo real (`tune`).
* Analizar un archivo de audio para detectar si hay una guitarra, estimar el género y la tonalidad (`analyze`).

```bash
python guitar_tuner.py tune --duration 0.5
python guitar_tuner.py analyze ejemplo.wav
```

## Visualizador 3D básico

El script `blender_viewer.py` abre una ventana 3D y rota un modelo exportado desde Blender en formato OBJ.

### Requisitos

```bash
pip install pyglet
```

### Ejecución

```bash
python blender_viewer.py
```

Puedes reemplazar `assets/cube.obj` con tu propio modelo `.obj` generado en Blender.

## Aplicación multiplataforma de comunicación

El script `communication_app.py` crea una interfaz de mensajería basada en [Flet](https://flet.dev/) que funciona en
Windows, Linux, macOS, iOS y Android. Permite iniciar sesión con una cuenta de Google mediante OAuth 2.0 y habilita un
chat con un agente inteligente (usa la API de OpenAI si proporcionas la clave, o un modo demo que repite tus mensajes).

Además incorpora un panel de **control remoto** que utiliza `pyautogui` para mover el cursor, realizar clicks y enviar
texto al equipo host desde la misma interfaz, ideal para controlar tu PC desde el móvil o viceversa.

También guarda automáticamente el **historial de conversaciones** por usuario en tu carpeta de configuración y permite
exportarlo a Markdown o borrarlo cuando quieras, de modo que puedes retomar charlas previas sin configuraciones extra.

### Requisitos

```bash
pip install flet google-auth-oauthlib google-auth requests
# Opcional, solo si quieres habilitar respuestas con IA real
pip install openai
# Opcional, para habilitar el control remoto de teclado/ratón
pip install pyautogui
```

Descarga un archivo `client_secrets.json` desde la consola de Google Cloud (tipo "Escritorio") y ejecútalo así:

```bash
python communication_app.py --client-secrets /ruta/al/client_secrets.json --openai-api-key TU_CLAVE
```

En la primera ejecución se abrirá el navegador para autorizar la app. El token se guarda en `~/.config/gol/communication_app_tokens.json` para reutilizarlo.

Si deseas cambiar la ubicación donde se almacena el historial de chat puedes indicar `--history-dir /otra/ruta` al ejecutar
la aplicación. Cada sesión de usuario se serializa en JSON y, opcionalmente, puedes exportar una copia en Markdown desde la
misma interfaz.

Tras autenticarte, verás el panel de control remoto con:

- Un trackpad virtual para mover el cursor.
- Botones para clicks izquierdo y derecho.
- Un control de sensibilidad para ajustar la velocidad del cursor.
- Un campo de texto que envía pulsaciones al sistema cuando lo envías.
- Un bloque de historial con acciones para exportar la conversación como Markdown o limpiarla.

> Nota: si la plataforma donde ejecutes la app no permite controlar teclado/ratón (por ejemplo, algunas builds móviles o entornos sin servidor gráfico), el panel mostrará un aviso indicando que la función no está disponible.

### Validación automática

Para comprobar rápidamente que el panel de control remoto delega correctamente en `pyautogui` (o en sus dobles durante las
pruebas), ejecuta la batería de tests incluida:

```bash
pytest tests/test_input_controller.py
```

Las pruebas funcionan incluso en entornos sin `flet` ni `pyautogui` instalados, ya que emplean dobles de prueba ligeros.
