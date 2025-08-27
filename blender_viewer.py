"""Simple 3D viewer using pyglet.

Loads a model exported from Blender in Wavefront OBJ format and rotates it.
Run with `python blender_viewer.py` after installing pyglet:

    pip install pyglet
"""

import pyglet
from pyglet.gl import *  # noqa: F401, F403

# Configure resource path to find models inside the assets directory
pyglet.resource.path = ['assets']
pyglet.resource.reindex()

# Load the model (cube.obj provided as an example)
model = pyglet.resource.model('cube.obj')

window = pyglet.window.Window(800, 600, "Blender Model Viewer", resizable=True)
rotation = 0.0


@window.event
def on_draw():
    global rotation
    window.clear()
    glEnable(GL_DEPTH_TEST)

    # Set projection
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(65, window.width / float(window.height), 0.1, 100.0)

    # Set modelview
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -5.0)
    glRotatef(rotation, 0.0, 1.0, 0.0)

    model.draw()


def update(dt):
    global rotation
    rotation += 50 * dt


pyglet.clock.schedule(update)
pyglet.app.run()
