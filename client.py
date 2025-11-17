import socket
import json
import pygame
import os
import time
import random

pygame.font.init()

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

# network
ready = False
HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

data = {}


def send_dict(msg):
    msg_str = json.dumps(msg)
    message = msg_str.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    #print(client.recv(2048).decode(FORMAT))


def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    #print(client.recv(2048).decode(FORMAT))


# send_dict(data)

#send(DISCONNECT_MESSAGE)

#---------------------------------------------game body---------------------------------------------


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
    COOLDOWN = 30

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

    # def shoot(self):
    #     if self.cool_down_counter == 0:
    #         laser = Laser(self.x, self.y, self.laser_img)
    #         self.lasers.append(laser)
    #         self.cool_down_counter = 1

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):

    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
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
        self.healthbar(window)

    def laser_render(self, layser_list):
        self.lasers = []
        for i in range(len(layser_list)):
            laser = Laser(layser_list[i]['x'], layser_list[i]['y'],
                          YELLOW_LASER)
            # laser = Laser(self.x, self.y, YELLOW_LASER)
            self.lasers.append(laser)

        #self.cool_down_counter = 1

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

    # def shoot(self):
    #     if self.cool_down_counter == 0:
    #         laser = Laser(self.x-20, self.y, self.laser_img)
    #         self.lasers.append(laser)
    #         self.cool_down_counter = 1


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


enemies = []
data_dict = {
    'ready': False,
    'level': 0,
    'user1': '0.0.0.0',
    'user2': '0.0.0.0',
    'x1': 0,
    'y1': 0,
    'heahlth1': 100,
    'lost1': False,
    'x2': 0,
    'y2': 0,
    'health2': 100,
    'lost2': False
}


def main(addr):
    win2 = False  # for printing it
    lost2 = False
    user_data = {'connection': True, 'ready': False}
    global data_dict
    global enemies
    global data
    run = True
    FPS = 60
    level = 0

    small_font = pygame.font.SysFont("comicsans", 13)
    main_font = pygame.font.SysFont("comicsans", 30)
    lost_font = pygame.font.SysFont("comicsans", 60)
    title_font = pygame.font.SysFont("comicsans", 70)
    waiting_font = pygame.font.SysFont("comicsans", 35)

    player = Player(220, 630)
    player2 = Player(350, 630)

    clock = pygame.time.Clock()

    lost = False
    win = False

    def redraw_window():
        global win2, lost2
        WIN.blit(BG, (0, 0))
        # draw text
        user1 = small_font.render(
            f"User1: {data_dict['user1'][0]}: {data_dict['user1'][1]}", 1,
            (0, 255, 100))
        user2 = small_font.render(
            f"User2: {data_dict['user2'][0]}:{data_dict['user2'][1]}", 1,
            (0, 255, 100))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))

        WIN.blit(user1, (10, 10))
        WIN.blit(user2, (10, 28))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

        for enemy in enemies:
            enemy.draw(WIN)

        player.draw(WIN)
        player2.draw(WIN)

        # if lost:
        #     lost2 = lost
        #     # lost_label = lost_font.render("You Lost!!", 1, (255,255,255))
        #     # WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))

        # if win:
        #     win2 = win
        #     lost_label = lost_font.render("You Won!!", 1, (255,255,255))
        #     WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 350))

        pygame.display.update()

    while True:
        #print(user_data['ready'])
        #global enemies
        clock.tick(FPS)
        #print(data_dict['lost1'], data_dict['lost2'])

        if data_dict['lost1'] or data_dict['lost2'] or data_dict[
                'user1'] == '0.0.0.0' or data_dict['user2'] == '0.0.0.0':
            user_data[
                'ready'] = False  # rest it to False to stop it to send the previous not valid ready again in this new round

        if data_dict['ready']:
            #pygame.event.pump()
            keys = pygame.key.get_pressed()
            #pygame.event.pump()
            redraw_window()
        elif data_dict['user1'] == '0.0.0.0' or data_dict['user2'] == '0.0.0.0':
            # keys = [False for _ in range(512+1)]
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                pass
            # print(len(keys))
            WIN.blit(BG, (0, 0))
            waiting_label = waiting_font.render(
                "Waiting for another player...(1 online player)", 1,
                (255, 255, 255))
            WIN.blit(waiting_label,
                     (WIDTH / 2 - waiting_label.get_width() / 2, 350))
            pygame.display.update()
            win = False
            lost = False
        else:
            # print("Whaaaaahhhhh!!!!")
            # pygame.event.pump()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                user_data['ready'] = True
                #keys[pygame.K_SPACE] = False
            #pygame.event.pump()
            WIN.blit(BG, (0, 0))

            if lost:
                title_label = waiting_font.render(
                    "You Lost!!!, Press space to ready again", 1,
                    (255, 255, 255))
            elif win:
                title_label = waiting_font.render(
                    "You Won!!!, Press space to ready again", 1,
                    (255, 255, 255))
            else:
                title_label = title_font.render("Press space to ready", 1,
                                                (255, 255, 255))

            WIN.blit(title_label,
                     (WIDTH / 2 - title_label.get_width() / 2, 350))

            pygame.display.update()
            win = False
            lost = False

        #pygame.event.pump()
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                user_data['connection'] = False
                send_dict(user_data)
                #quit()

        send_dict(user_data)

        # for i in range(0, len(keys)):
        #     if keys[i]:
        #         print(i)

        data_str = json.dumps(keys)
        send(data_str)

        while True:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                data_received = client.recv(msg_length).decode(FORMAT)
                break

        # data_received = client.recv(4096).decode(FORMAT)
        data_dict = json.loads(data_received)
        #print(data_str)

        pygame.event.pump()

        level = data_dict['level']

        if addr == data_dict['user1']:
            player.x = data_dict['x1']
            player.y = data_dict['y1']
            player.health = data_dict['health1']
            if data_dict['win1']:
                win = True
            player2.x = data_dict['x2']
            player2.y = data_dict['y2']
            player2.health = data_dict['health2']
            if data_dict['win2']:
                lost = True

        elif addr == data_dict['user2']:
            player.x = data_dict['x2']
            player.y = data_dict['y2']
            player.health = data_dict['health2']
            if data_dict['win2']:
                win = True
            player2.x = data_dict['x1']
            player2.y = data_dict['y1']
            player2.health = data_dict['health1']
            if data_dict['win1']:
                lost = True

        #send("hello")

        pygame.event.pump()
        if addr == data_dict['user1']:

            # laser_str = client.recv(4096).decode(FORMAT)
            while True:
                msg_length = client.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    laser_str = client.recv(msg_length).decode(FORMAT)
                    break
            laser_list = json.loads(laser_str)
            player.laser_render(laser_list)

            # send("hello")

            # laser_str = client.recv(4096).decode(FORMAT)
            while True:
                msg_length = client.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    laser_str = client.recv(msg_length).decode(FORMAT)
                    break
            laser_list = json.loads(laser_str)
            player2.laser_render(laser_list)

        elif addr == data_dict['user2']:
            # laser_str = client.recv(4096).decode(FORMAT)
            while True:
                msg_length = client.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    laser_str = client.recv(msg_length).decode(FORMAT)
                    break
            laser_list = json.loads(laser_str)
            player2.laser_render(laser_list)

            # send("hello")

            # laser_str = client.recv(4096).decode(FORMAT)
            while True:
                msg_length = client.recv(HEADER).decode(FORMAT)
                if msg_length:
                    msg_length = int(msg_length)
                    laser_str = client.recv(msg_length).decode(FORMAT)
                    break
            laser_list = json.loads(laser_str)
            player.laser_render(laser_list)

        #laser_list = json.loads(laser_str)
        #player.shoot(laser_list)
        pygame.event.pump()

        # enmies_data_str = client.recv(65536).decode(FORMAT)
        while True:
            msg_length = client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                enmies_data_str = client.recv(msg_length).decode(FORMAT)
                break

        enemies_data = json.loads(enmies_data_str)
        enemies = []
        for i in range(len(enemies_data)):
            enemy = Enemy(enemies_data[i]['ex'], enemies_data[i]['ey'],
                          enemies_data[i]['ecolor'])
            enemies.append(enemy)


def main_menu():

    send("hello")
    # addr_str = client.recv(2048).decode(FORMAT)
    while True:
        msg_length = client.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            addr_str = client.recv(msg_length).decode(FORMAT)
            break

    addr_dict = json.loads(addr_str)
    addr = [addr_dict['ip'], addr_dict['port']]
    title_font = pygame.font.SysFont("comicsans", 70)
    run = True
    while run:

        main(addr)

    pygame.quit()


main_menu()
