import pyglet
from pyglet.gl import *
from pyglet.window import key
from dataclasses import dataclass
from typing import Optional, List

"""Shooter con pirámide de cristal.

La nave del jugador es una pequeña pirámide roja translúcida con reflejos.
Dispara hacia arriba por carriles; si hay un enemigo en el mismo carril, el
disparo lo alcanza. Las oleadas de cubos azules descienden como en juegos
clásicos: se mueven de lado a lado y, al tocar un borde, bajan una fila.
Cada nueva oleada duplica el número de enemigos.
"""

window = pyglet.window.Window(800, 600, "Pyramid Shooter")

# --- Configuración OpenGL ---
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_POSITION, (GLfloat * 4)(0.5, 1.0, 1.0, 0))
glEnable(GL_COLOR_MATERIAL)
glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

# --- Configuración del jugador y carriles ---
player_size = int(min(window.width, window.height) * 0.04)
num_lanes = 5
lane_spacing = window.width / num_lanes
lane_positions = [-window.width / 2 + lane_spacing * (i + 0.5)
                  for i in range(num_lanes)]
player_lane = num_lanes // 2
player_x = lane_positions[player_lane]
player_y = -window.height // 2 + player_size

# --- Estado del juego ---


@dataclass
class Enemy:
    lane: int
    y: float


@dataclass
class Bullet:
    lane: int
    y: float
    target: Optional[Enemy]


@dataclass
class Boss:
    x: float
    y: float
    size: float
    hp: int
    cooldown: float


@dataclass
class BossBullet:
    lane: int
    y: float


bullets: List[Bullet] = []
enemies: List[Enemy] = []
boss: Optional[Boss] = None
boss_bullets: List[BossBullet] = []
fleet_offset = 0.0
fleet_direction = 1
wave = 1
base_enemy_count = num_lanes


def setup_projection():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-window.width / 2, window.width / 2,
            -window.height / 2, window.height / 2,
            -1000, 1000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def _normal(a, b, c):
    ux, uy, uz = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    vx, vy, vz = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    nx = uy * vz - uz * vy
    ny = uz * vx - ux * vz
    nz = ux * vy - uy * vx
    l = (nx * nx + ny * ny + nz * nz) ** 0.5
    return nx / l, ny / l, nz / l


def draw_pyramid(x, y, size):
    half = size / 2
    h = size
    v0 = (x - half, y - half, 0)
    v1 = (x + half, y - half, 0)
    v2 = (x + half, y + half, 0)
    v3 = (x - half, y + half, 0)
    apex = (x, y, h)
    faces = [
        (v0, v1, v2), (v0, v2, v3),  # base
        (v0, v1, apex),
        (v1, v2, apex),
        (v2, v3, apex),
        (v3, v0, apex),
    ]
    verts, norms = [], []
    for a, b, c in faces:
        nx, ny, nz = _normal(a, b, c)
        verts.extend(a + b + c)
        norms.extend((nx, ny, nz) * 3)
    colors = (1.0, 0.0, 0.0, 0.4) * (len(verts) // 3)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,
                 (GLfloat * 4)(1.0, 1.0, 1.0, 0.8))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 64)
    pyglet.graphics.draw(len(verts) // 3, GL_TRIANGLES,
                         ('v3f', verts), ('n3f', norms), ('c4f', colors))


def draw_fractal_pyramid(x, y, size, level):
    draw_pyramid(x, y, size)
    if level <= 0:
        return
    s = size / 2
    for dx in (-s / 2, s / 2):
        for dy in (-s / 2, s / 2):
            draw_fractal_pyramid(x + dx, y + dy, s, level - 1)


def draw_cube(x, y, size, color):
    s = size / 2
    vertices = [
        x - s, y - s, 0,  x + s, y - s, 0,
        x + s, y + s, 0,  x - s, y + s, 0,
        x - s, y - s, size,  x + s, y - s, size,
        x + s, y + s, size,  x - s, y + s, size,
    ]
    indices = [0, 1, 2, 0, 2, 3,
               4, 5, 6, 4, 6, 7,
               0, 1, 5, 0, 5, 4,
               1, 2, 6, 1, 6, 5,
               2, 3, 7, 2, 7, 6,
               3, 0, 4, 3, 4, 7]
    pyglet.graphics.draw_indexed(8, GL_TRIANGLES, indices,
                                ('v3f', vertices),
                                ('c4f', color * 8))


@window.event
def on_draw():
    window.clear()
    setup_projection()
    glEnable(GL_LIGHTING)
    draw_pyramid(player_x, player_y, player_size)
    glDisable(GL_LIGHTING)
    for b in bullets:
        draw_cube(lane_positions[b.lane], b.y, player_size * 0.2,
                  (1.0, 1.0, 0.0, 1.0))
    for e in enemies:
        x = lane_positions[e.lane] + fleet_offset
        draw_cube(x, e.y, player_size, (0.0, 0.0, 1.0, 1.0))
    if boss:
        glEnable(GL_LIGHTING)
        draw_fractal_pyramid(boss.x, boss.y, boss.size, 1)
        glDisable(GL_LIGHTING)
        for bb in boss_bullets:
            draw_cube(lane_positions[bb.lane], bb.y, player_size * 0.3,
                      (1.0, 0.0, 0.0, 1.0))


@window.event
def on_key_press(symbol, modifiers):
    global player_lane, player_x
    if symbol == key.LEFT and player_lane > 0:
        player_lane -= 1
        player_x = lane_positions[player_lane]
    elif symbol == key.RIGHT and player_lane < num_lanes - 1:
        player_lane += 1
        player_x = lane_positions[player_lane]
    elif symbol == key.SPACE:
        target = None
        for e in sorted((e for e in enemies if e.lane == player_lane and e.y > player_y),
                        key=lambda e: e.y):
            target = e
            break
        bullets.append(Bullet(lane=player_lane,
                              y=player_y + player_size,
                              target=target))


def update(dt):
    global fleet_offset, fleet_direction, boss
    bullet_speed = 400
    fleet_speed = 60
    boss_bullet_speed = 250

    # Actualizar balas
    for b in bullets[:]:
        b.y += bullet_speed * dt
        if b.target not in enemies:
            b.target = None
        if b.target and b.y >= b.target.y:
            enemies.remove(b.target)
            bullets.remove(b)
        elif boss and b.y >= boss.y:
            boss.hp -= 1
            bullets.remove(b)
            if boss.hp <= 0:
                boss = None
                spawn_wave()
        elif b.y > window.height / 2:
            bullets.remove(b)

    # Movimiento de la flota
    if enemies:
        fleet_offset += fleet_direction * fleet_speed * dt
        left = min(lane_positions[e.lane] + fleet_offset for e in enemies)
        right = max(lane_positions[e.lane] + fleet_offset for e in enemies)
        if right > window.width / 2 - player_size or left < -window.width / 2 + player_size:
            fleet_direction *= -1
            fleet_offset += fleet_direction * fleet_speed * dt
            for e in enemies:
                e.y -= player_size

    # Actualizar jefe
    if boss:
        boss.cooldown -= dt
        if boss.cooldown <= 0:
            boss_bullets.append(BossBullet(lane=player_lane, y=boss.y - boss.size))
            boss.cooldown = 2.5
    for bb in boss_bullets[:]:
        bb.y -= boss_bullet_speed * dt
        if bb.lane == player_lane and bb.y <= player_y + player_size:
            print("Game Over")
            pyglet.app.exit()
        if bb.y < -window.height / 2:
            boss_bullets.remove(bb)

    # Nueva oleada cuando no quedan enemigos ni jefe
    if not enemies and not boss:
        spawn_wave()


def spawn_wave():
    global wave, enemies, fleet_offset, fleet_direction, boss
    enemies = []
    fleet_offset = 0.0
    fleet_direction = 1
    if wave % 10 == 0:
        boss = Boss(x=0.0,
                    y=window.height / 2 - player_size,
                    size=player_size * 3,
                    hp=10,
                    cooldown=1.0)
    else:
        count = base_enemy_count * (2 ** (wave - 1))
        rows = (count + num_lanes - 1) // num_lanes
        y_start = window.height / 2 - player_size
        n = 0
        for r in range(rows):
            for lane in range(num_lanes):
                if n >= count:
                    break
                enemies.append(Enemy(lane, y_start + r * player_size))
                n += 1
    wave += 1


spawn_wave()
pyglet.clock.schedule_interval(update, 1 / 60.0)
pyglet.app.run()

