import socket
import threading
import json
import pygame
import os
import time
import random

pygame.font.init()

flag = False
WIDTH, HEIGHT = 750, 750
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter Tutorial")

# Load images
RED_SPACE_SHIP = pygame.image.load(
    os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(
    os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(
    os.path.join("assets", "pixel_ship_blue_small.png"))

# Player player
YELLOW_SPACE_SHIP = pygame.image.load(
    os.path.join("assets", "pixel_ship_yellow.png"))

# Lasers
RED_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets",
                                             "pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets", "pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(
    os.path.join("assets", "pixel_laser_yellow.png"))

# Background
BG = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", "background-black.png")),
    (WIDTH, HEIGHT))

# data1 = {'x':0, 'y':0, 'health': 0,'x_e':0, 'y_e':0, 'health_e': 0}
# data2 = {'x':0, 'y':0, 'health': 0,'x_e':0, 'y_e':0, 'health_e': 0}
ready_players = 0
user_count = 0
enemies = []
data = {
    'ready': False,
    'level': 0,
    'user1': '0.0.0.0',
    'user2': '0.0.0.0',
    'x1': 0,
    'y1': 0,
    'health1': 100,
    'lost1': False,
    'x2': 0,
    'y2': 0,
    'health2': 100,
    'lost2': False,
    'win1': False,
    'win2': False
}
wave_length = 10
enemy_vel = 4
level = 0

HEADER = 64
PORT = 5050
# SERVER = "192.168.43.1"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DEISCONNECT_MESSAGE = '!DISCONNECT'
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

a = []
i = 0


# i used this protocl so the client from the other side konws how many bites that are needed to receive
def send_dict(msg, conn):
    msg_str = json.dumps(msg)
    message = msg_str.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)
    #print(client.recv(2048).decode(FORMAT))


def send(msg, conn):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    conn.send(send_length)
    conn.send(message)
    #print(client.recv(2048).decode(FORMAT))


semaphore = threading.Semaphore()
semaphore2 = threading.Semaphore()
semaphore3 = threading.Semaphore()
semaphore4 = threading.Semaphore()
semaphore5 = threading.Semaphore()
semaphore6 = threading.Semaphore()
semaphore7 = threading.Semaphore()
semaphore8 = threading.Semaphore()
semaphore9 = threading.Semaphore()
semaphore10 = threading.Semaphore()


class Laser:

    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)

    def collision(self, obj):
        return collide(self, obj)


class Ship:
    COOLDOWN = 20

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                self.lasers.remove(laser)

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):

    def __init__(
        self,
        x,
        y,
        health=100,
    ):
        super().__init__(
            x,
            y,
            health,
        )
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        if laser in self.lasers:
                            self.lasers.remove(laser)

    def draw(self, window):
        super().draw(window)
        #self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10,
                          self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0),
                         (self.x, self.y + self.ship_img.get_height() + 10,
                          self.ship_img.get_width() *
                          (self.health / self.max_health), 10))


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self, vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x - 20, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


laysers_data = []
lasers_data2 = []
ready = False
flag8 = False
flag9 = False

user1_ready = False
user2_ready = False


def handle_client_disconnect(conn, addr):
    global user_count
    global enemies
    global level
    global enemy_vel
    global wave_length

    data['win1'] = False
    data['win2'] = False
    with semaphore10:
        enemies = []
        with semaphore4:
            user_count -= 1
        level = 0
        enemy_vel = 0
        wave_length = 10
        data['lost1'] = False
        data['lost2'] = False
    if addr == data['user1']:
        data['user1'] = '0.0.0.0'
        data['lost1'] = False
        data['health1'] = 100
        conn.close()
    elif addr == data['user2']:
        data['user2'] = '0.0.0.0'
        data['lost2'] = False
        data['health2'] = 100
        conn.close()
    else:
        conn.close()
    quit()


flag5 = False


def handle_client(conn, addr):
    
    print("[NEW CONNECTION] {addr} connected.")
    global semaphore, semaphore2, semaphore3, semaphore4, semaphore5, semaphore6, semaphore7
    global user1_ready
    global user2_ready
    global ready
    global lasers_data
    global lasers_data2
    global i
    global ready_players
    global user_count
    global enemies
    global wave_length
    global enemy_vel
    global level
    global flag
    global flag8
    global flag5
    global flag9
    run = True
    FPS = 60

    player_vel = 10
    laser_vel = 10

    # player2_vel = 5
    # laser_vel = 5
    if addr == data['user1']:
        player = Player(220, 630)
    if addr == data['user2']:
        player = Player(400, 630)
    # player2 = Player(350, 630)

    clock = pygame.time.Clock()

    lost = False
    lost_count = 0

    msg_length = conn.recv(HEADER).decode(FORMAT)

    if msg_length:
        msg_length = int(msg_length)
        ready_msg = conn.recv(msg_length).decode(FORMAT)
        if ready_msg == 'hello':
            addr_dict = {"ip": addr[0], "port": addr[1]}
            # addr_str = json.dumps(addr_dict)
            # conn.send(addr_str.encode(FORMAT))
            send_dict(addr_dict, conn)

    time2 = 2.0
    time1 = 2.0

    while run:
        pygame.event.pump()
        clock.tick(FPS)

        while True:
            try:
                msg_length = conn.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = conn.recv(msg_length).decode(FORMAT)
                    if msg == DEISCONNECT_MESSAGE:
                        #msg_dict = json.loads(msg)
                        break
                    else:
                        user_data = json.loads(msg)
                        break
            except Exception:
                handle_client_disconnect(conn, addr)

        if addr == data['user1']:
            user1_ready = user_data['ready']
            if user_data['connection'] == False:
                handle_client_disconnect(conn, addr)
        elif addr == data['user2']:
            user2_ready = user_data['ready']
            if user_data['connection'] == False:
                handle_client_disconnect(conn, addr)
            #print(user_data)

        if user1_ready and user2_ready:
            if not data['ready']:
                enemies = []
                if addr == data['user1']:
                    player = Player(220, 630)
                if addr == data['user2']:
                    player = Player(400, 630)

            data['ready'] = True
            user1_ready = False  # baraye nobat dehi bar haye ba'di bayad False konimeshoon ke darja naran too
            user2_ready = False
            data['lost1'] = False
            data['lost2'] = False
            data['win1'] = False
            data['win2'] = False

        if not data['ready']:
            level = 0
            #enemies = []
            enemy_vel = 0
            player_vel = 0
            wave_length = 10
            data['lost1'] = False
            data['lost2'] = False

        elif data['user1'] == '0.0.0.0' or data['user2'] == '0.0.0.0' or data[
                'lost1'] or data['lost2']:
            with semaphore8:  # reset everything in case of lost of one of the player
                flag8 = not flag8
                if (flag8):
                    data['lost1'] = False
                    data['lost2'] = False
                    data['ready'] = False

                    level = 0
                    enemy = []
                    enemy_vel = 0
                    player_vel = 0
                    wave_length = 10
                    user_data['ready'] = False
            if addr == data['user1']:
                player = Player(220, 630)
            if addr == data['user2']:
                player = Player(400, 630)

        # enemy_vel = int(80.0 * (time2-time1))
        # player_vel = int(550.0 * (time2-time1))
        else:
            # enemy_vel = 4
            # player_vel = 10
            enemy_vel = int(140.0 * (time2 - time1))
            player_vel = int(200.0 * (time2 - time1))
        # redraw_window()

        time1 = time.time()
        # if lives <= 0 or player.health <= 0:
        if addr == data['user1'] and player.health <= 0:
            data['lost1'] = True
            data['win2'] = True
            lost_count += 1

        if addr == data['user2'] and player.health <= 0:
            data['lost2'] = True
            data['win1'] = True
            lost_count += 1

        with semaphore2:
            flag5 = not (flag5)
            if flag5:
                if len(enemies) == 0:
                    level += 1
                    wave_length += 10
                    for i in range(wave_length):
                        enemy = Enemy(random.randrange(50, WIDTH - 100),
                                      random.randrange(-1500, -100),
                                      random.choice(["red", "blue", "green"]))
                        enemies.append(enemy)

        while True:
            try:
                msg_length = conn.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    msg = conn.recv(msg_length).decode(FORMAT)
                    if msg == DEISCONNECT_MESSAGE:
                        #msg_dict = json.loads(msg)
                        break
                    else:
                        keys = json.loads(msg)
                        break
            except Exception:
                handle_client_disconnect(conn, addr)

        #keys = pygame.key.get_pressed()
        #player.x -= player_vel
        # for i in range(0, len(keys)):
        #     if keys[i]:
        #         print(i)

        if keys[(pygame.K_a) - 93] and player.x - player_vel > 0:  # left
            player.x -= player_vel
        if keys[pygame.K_d - 93] and player.x + player_vel + player.get_width(
        ) < WIDTH:  # right
            player.x += player_vel
        if keys[pygame.K_w - 93] and player.y - player_vel > 0:  # up
            player.y -= player_vel
        if keys[pygame.K_s - 93] and player.y + player_vel + player.get_height(
        ) + 15 < HEIGHT:  # down
            player.y += player_vel
        if keys[pygame.K_SPACE + 12]:
            player.shoot()
            # print("hello")

        with semaphore2:
            flag = not flag
            if flag:
                for enemy in enemies[:]:
                    enemy.move(enemy_vel)
                    # enemy.move_lasers(laser_vel, player)

                    # if random.randrange(0, 2*60) == 1:
                    #     enemy.shoot()

                    if collide(enemy, player):
                        player.health -= 10
                        enemies.remove(enemy)
                    elif enemy.y + enemy.get_height() > HEIGHT:
                        #     lives -= 1
                        enemies.remove(enemy)

            player.move_lasers(-laser_vel, enemies)

        #connected = True

        data["level"] = level

        if addr == data["user1"]:
            data["x1"] = player.x
            data["y1"] = player.y
            data["health1"] = player.health

        elif addr == data["user2"]:
            data["x2"] = player.x
            data["y2"] = player.y
            data["health2"] = player.health

        # data_str = json.dumps(data)
        # conn.send(data_str.encode(FORMAT))
        send_dict(data, conn)

        if addr == data["user1"]:
            with semaphore5:
                lasers_data = []
                for laser in player.lasers:
                    lasers_data.append({'x': laser.x, 'y': laser.y})
                #print(lasers_data)

                #conn.send("hello".encode(FORMAT))
        elif addr == data["user2"]:
            with semaphore6:
                lasers_data2 = []
                for laser in player.lasers:
                    lasers_data2.append({'x': laser.x, 'y': laser.y})

            #print(lasers_data)

        lasers_data_str = json.dumps(lasers_data)
        send(lasers_data_str, conn)
        # conn.send(lasers_data_str.encode(FORMAT))

        lasers_data_str2 = json.dumps(lasers_data2)
        send(lasers_data_str2, conn)

        enemies_data = []
        for i in range(len(enemies)):
            if enemies[i].ship_img == RED_SPACE_SHIP:
                color = "red"
            elif enemies[i].ship_img == GREEN_SPACE_SHIP:
                color = "green"
            else:
                color = "blue"

            enemies_data.append({
                'ex': enemies[i].x,
                'ey': enemies[i].y,
                'ecolor': color
            })

        enemies_data_str = json.dumps(enemies_data)
        send(enemies_data_str, conn)
        # conn.send(enemies_data_str.encode(FORMAT))
        #print(a)
        #print(i)
        time2 = time.time()


def start():
    global user_count
    global semaphore4

    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        if user_count < 2:
            conn, addr = server.accept()
            if (data["user1"] == '0.0.0.0'):
                data["user1"] = addr
            elif (data["user2"] == '0.0.0.0'):
                data["user2"] = addr
            with semaphore4:
                user_count += 1
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            #thread.join()
            print(f"[ACTIVE CONNECTIONS]{threading.activeCount()- 1}")
        else:
            pass


if __name__ == "__main__":
    print("[STARTING] server is starting...")
    start()
