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

## Shooter 3D mínimo

El script `pyramid_shooter.py` crea una pequeña pirámide de cristal (≈4 % de la
pantalla) que refleja la luz y es parcialmente transparente. La nave se mueve
por carriles con las flechas y cada disparo viaja por el mismo carril para
alcanzar al enemigo más cercano. Los cubos azules descienden en oleadas que se
mueven de lado a lado, bajan al tocar los bordes y duplican su número en cada
nivel. Cada décimo nivel aparece un jefe: una gran pirámide fractal que ocupa
varios carriles, dispara un cañón poderoso pero lento y requiere múltiples
impactos para ser derrotada.

### Ejecución

```bash
python pyramid_shooter.py
```

Controles: flechas para moverte y `espacio` para disparar.
