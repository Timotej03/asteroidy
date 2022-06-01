# importy kniznic
import math
import random

import pyglet
from pyglet import gl
from pyglet.window import key

# konstanty a premenne co budeme pouzivat

# konstanty okna
WIDTH = 1200
HEIGHT = 800

# kontstanty hry
ACCELERATION = 120  # Zrýchlenie rakety
ROTATION_SPEED = 0.05  # Rýchlosť otáčania rakety

game_objects = []
batch = pyglet.graphics.Batch()  # ZOZNAM SPRITOV PRE ZJEDNODUŠENÉ VYKRESLENIE
pressed_keyboards = set()  # MNOŽINA ZMAČKNUTÝCH KLÁVES

delay_shooting = 0.4
laserlifetime = 45
laserspeed = 200

# skore counter
score = 0


# funkcie

# vycentrovanie obrazka na stred
def set_anchor_of_image_to_center(img):
    img.anchor_x = img.width // 2
    img.anchor_y = img.height // 2


# vykreslenie kolizneho kolecka, budeme neskor odstranovat
def draw_circle(x, y, radius):
    iterations = 20
    s = math.sin(2 * math.pi / iterations)
    c = math.cos(2 * math.pi / iterations)

    dx, dy = radius, 0

    gl.glBegin(gl.GL_LINE_STRIP)
    gl.glColor3f(1, 1, 1)  # nastav barvu kresleni na bilou
    for i in range(iterations + 1):
        gl.glVertex2f(x + dx, y + dy)
        dx, dy = (dx * c - dy * s), (dy * c + dx * s)
    gl.glEnd()


# triedy hry

# hlavna trieda pre vsetky objekty

class SpaceObject:
    "Konštruktor"

    def __init__(self, sprite, x, y, speed_x=0, speed_y=0):
        self.x_speed = speed_x
        self.y_speed = speed_y
        self.rotation = 1.57  # radiany -> smeruje hore

        self.sprite = pyglet.sprite.Sprite(sprite, batch=batch)
        self.sprite.x = x
        self.sprite.y = y
        self.radius = (self.sprite.height + self.sprite.width) // 4

    # vypocet vzdialenosti medzi dvoma objektami
    def distance(self, other):
        x = abs(self.sprite.x - other.sprite.x)
        y = abs(self.sprite.y - other.sprite.y)
        return (x ** 2 + y ** 2) ** 0.5  # pytagorova veta

    # kolizia s lodou, definujeme v dalsej triede
    def hit_by_spaceship(self, ship):
        pass

    # kolizia s laserom, definujeme v dalsej triede
    def hit_by_laser(self, laser):
        pass

    # vymazanie objektu
    def delete(self, dt=0):
        self.sprite.delete()
        game_objects.remove(self)

    # metoda, ci sa nachadzame na kraji obrazovky
    def checkBoundaries(self):
        if self.sprite.x > WIDTH:
            self.sprite.x = 0

        if self.sprite.x < 0:
            self.sprite.x = WIDTH

        if self.sprite.y < 0:
            self.sprite.y = HEIGHT

        if self.sprite.y > HEIGHT:
            self.sprite.y = 0

    # metoda tick pre vsetky triedy
    def tick(self, dt):
        # posunutie objektu podla rychlosti
        self.sprite.x += dt * self.x_speed
        self.sprite.y += dt * self.y_speed
        self.sprite.rotation = 90 - math.degrees(self.rotation)
        # kontrola ci sme na kraji
        self.checkBoundaries()


# trieda pre lod, (hrac)
class Spaceship(SpaceObject):

    # konstruktor
    def __init__(self, sprite, x, y):
        super().__init__(sprite, x, y)
        self.laser_ready = True

        # naloadovanie obrazku flamu
        flame_sprite = pyglet.image.load("Assetss/PNG/Effects/fire05.png")
        set_anchor_of_image_to_center(flame_sprite)
        self.flame = pyglet.sprite.Sprite(flame_sprite, batch=batch)
        self.flame.visible = False

    # metoda vystrelenia laseru
    def shoot(self):
        img = pyglet.image.load("Assetss/PNG/Lasers/laserBlue04.png")
        set_anchor_of_image_to_center(img)

        laser_x = self.sprite.x + math.cos(self.rotation) * self.radius
        laser_y = self.sprite.y + math.sin(self.rotation) * self.radius

        laser = Laser(img, laser_x, laser_y)
        laser.rotation = self.rotation

        game_objects.append(laser)

    # vykona sa metoda tick 60x za sekundu
    def tick(self, dt):
        super().tick(dt)

        # zrychlenie podla konstant pri zmacknuti W
        if 'W' in pressed_keyboards:
            self.x_speed = self.x_speed + dt * ACCELERATION * math.cos(self.rotation)
            self.y_speed = self.y_speed + dt * ACCELERATION * math.sin(self.rotation)

            # flame pozicia a zobrazenie
            self.flame.x = self.sprite.x - math.cos(self.rotation) * self.radius
            self.flame.y = self.sprite.y - math.sin(self.rotation) * self.radius
            self.flame.rotation = self.sprite.rotation
            self.flame.visible = True
        # ak nie je W v pressed_keyboards tak flame neni vidno
        else:
            self.flame.visible = False

        # pri zmacknuti S sa rychlost znizuje
        if 'S' in pressed_keyboards:
            self.x_speed = self.x_speed - dt * ACCELERATION * math.cos(self.rotation)
            self.y_speed = self.y_speed - dt * ACCELERATION * math.sin(self.rotation)

        # otocenie dolava pri zmacknuti A
        if 'A' in pressed_keyboards:
            self.rotation += ROTATION_SPEED

        # otocenie doprava pri zmacknuti D
        if 'D' in pressed_keyboards:
            self.rotation -= ROTATION_SPEED

        # "rucna brzda" pri zmacknuti Shift
        if 'SHIFT' in pressed_keyboards:
            self.x_speed = 0
            self.y_speed = 0

        # vystrelenie laseru pri zmacknuti Space + zapnutie "cooldownu na laser"
        if "SPACE" in pressed_keyboards and self.laser_ready:
            self.shoot()
            self.laser_ready = False
            pyglet.clock.schedule_once(self.reload, delay_shooting)

        # vyberie vsetky objekty okrem seba
        for obj in [o for o in game_objects if o != self]:
            # d = distance medzi objektami
            d = self.distance(obj)
            if d < self.radius + obj.radius:
                obj.hit_by_spaceship(self)
                break

    # metoda zodpovedna za reset pozicie
    def reset(self):
        self.sprite.x = WIDTH // 2
        self.sprite.y = HEIGHT // 2
        self.rotation = 1.57  # radiany -> smeruje hore
        self.x_speed = 0
        self.y_speed = 0

    def reload(self, dt):
        self.laser_ready = True


# trieda Asteroid
class Asteroid(SpaceObject):
    # metoda pri kolizi lode a asteroidu
    def hit_by_spaceship(self, ship):
        pressed_keyboards.clear()
        ship.reset()
        self.delete()

    # metoda pri kolizi asteroidu a laseru
    def hit_by_laser(self, laser):
        global score
        self.delete()
        laser.delete()
        score += 10


# trieda Laser
class Laser(SpaceObject):
    # konstruktor
    def __init__(self, sprite, x, y):
        super().__init__(sprite, x, y)
        self.laserlifetime = laserlifetime

    # metoda tick preberana z hlavnej triedy + znizenie lifetime
    def tick(self, dt):
        super().tick(dt)
        self.laserlifetime -= 0.5
        if self.laserlifetime == 0:
            self.delete()
        # vypocet rychlosti laseru
        self.y_speed = laserspeed * math.sin(self.rotation)
        self.x_speed = laserspeed * math.cos(self.rotation)
        # vyberie vsetky objekty okrem lode
        for obj in [o for o in game_objects if o != self and o != Spaceship]:
            d = self.distance(obj)
            if d < self.radius + obj.radius:
                obj.hit_by_laser(self)
                break


# trieda "hra"
class Game:
    # kontruktor
    def __init__(self):
        self.window = None
        game_objects = []

    # nacitanie obrazkov hry
    def load_resources(self):
        self.playerShip_image = pyglet.image.load('Assetss/PNG/playerShip1_blue.png')
        set_anchor_of_image_to_center(self.playerShip_image)
        self.background_image = pyglet.image.load('Assetss/Backgrounds/purple.png')
        self.asteroid_images = ['Assetss/PNG/Meteors/meteorGrey_big1.png',
                                'Assetss/PNG/Meteors/meteorGrey_med1.png',
                                'Assetss/PNG/Meteors/meteorGrey_small1.png',
                                'Assetss/PNG/Meteors/meteorGrey_tiny1.png']

    # vytvorenie objektu hry
    def init_objects(self):
        # Vytvorenie lode
        spaceShip = Spaceship(self.playerShip_image, WIDTH // 2, HEIGHT // 2)
        game_objects.append(spaceShip)

        # Nastavenie pozadia a prescalovanie
        self.background = pyglet.sprite.Sprite(self.background_image)
        self.background.scale_x = 6
        self.background.scale_y = 4

        # Vytvorenie Meteoritov
        self.create_asteroids(count=7)
        # Pridavanie novych asteroidoch každych 10 sekund
        pyglet.clock.schedule_interval(self.create_asteroids, 6, 1)

    def create_asteroids(self, dt=0, count=1):
        # vytvorenie poctu asteroidov
        for i in range(count):
            # Výber asteroidu náhodne
            img = pyglet.image.load(random.choice(self.asteroid_images))
            set_anchor_of_image_to_center(img)

            # Nastavenie pozície na okraji obrazovky náhodne
            position = [0, 0]
            dimension = [WIDTH, HEIGHT]
            axis = random.choice([0, 1])
            position[axis] = random.uniform(0, dimension[axis])

            # Nastavenie rýchlosti
            tmp_speed_x = random.uniform(-100, 100)
            tmp_speed_y = random.uniform(-100, 100)

            # Temp asteroid object
            asteroid = Asteroid(img, position[0], position[1], tmp_speed_x, tmp_speed_y)
            game_objects.append(asteroid)

    # metoda ktora sa vola n a "on_draw" stale a vykresluje vsetko v hre
    def draw_game(self):
        global score, scoreLabel
        # Vymaže aktualny obsah okna
        self.window.clear()
        # Vykreslenie pozadia
        self.background.draw()
        scoreLabel = pyglet.text.Label(text=str(score), font_size=40, x=1150, y=760, anchor_x='right',
                                       anchor_y='center')
        scoreLabel.draw()

        # vykreslenie pomocnych koliecok
        for o in game_objects:
            draw_circle(o.sprite.x, o.sprite.y, o.radius)

        # Táto časť sa stará o to aby bol prechod cez okraje okna plynulý a nie skokový
        for x_offset in (-self.window.width, 0, self.window.width):
            for y_offset in (-self.window.height, 0, self.window.height):
                # Remember the current state
                gl.glPushMatrix()
                # Move everything drawn from now on by (x_offset, y_offset, 0)
                gl.glTranslatef(x_offset, y_offset, 0)

                # Draw !!! -> Toto vykreslí všetky naše sprites
                batch.draw()

                # Restore remembered state (this cancels the glTranslatef)
                gl.glPopMatrix()

    # spracovanie klavesovych zmacknuti
    def key_press(self, symbol, modifikatory):
        if symbol == key.W:
            pressed_keyboards.add('W')
        if symbol == key.S:
            pressed_keyboards.add('S')
        if symbol == key.A:
            pressed_keyboards.add('A')
        if symbol == key.D:
            pressed_keyboards.add('D')
        if symbol == key.LSHIFT:
            pressed_keyboards.add('SHIFT')
        if symbol == key.SPACE:
            pressed_keyboards.add("SPACE")

    # spracovanie klavesovych "vystupov"
    def key_release(self, symbol, modifikatory):
        if symbol == key.W:
            pressed_keyboards.discard('W')
        if symbol == key.S:
            pressed_keyboards.discard('S')
        if symbol == key.A:
            pressed_keyboards.discard('A')
        if symbol == key.D:
            pressed_keyboards.discard('D')
        if symbol == key.LSHIFT:
            pressed_keyboards.discard('SHIFT')
        if symbol == key.SPACE:
            pressed_keyboards.discard("SPACE")

    # metoda update
    def update(self, dt):
        for obj in game_objects:
            obj.tick(dt)

    # metoda startu hry
    def start(self):
        # vytvorenie okna hry
        self.window = pyglet.window.Window(width=WIDTH, height=HEIGHT)

        # nastavenie eventov, zaznamenanie klavesovych zmacknuti, "odmacknuti" a callovanie on_draw
        self.window.push_handlers(
            on_draw=self.draw_game,
            on_key_press=self.key_press,
            on_key_release=self.key_release
        )

        # load resources
        self.load_resources()

        # inicializacia objektov
        self.init_objects()

        # nastavenie timeru na 1/60 sekundy,
        pyglet.clock.schedule_interval(self.update, 1. / 60)

        pyglet.app.run()  # vsetko je hotove, runnujeme hru


# zaciatok hry
Game().start()