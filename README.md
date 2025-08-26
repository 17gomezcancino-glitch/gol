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
