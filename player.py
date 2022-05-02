from multiprocessing.connection import Client
import traceback
import pygame
import sys, os
k = 0
WHITE = (255, 255, 255)
X = 0
Y = 1
SIZE = (700, 526)

LEFT_PLAYER = 0
RIGHT_PLAYER = 1

FPS = 60
ANCHO = 700
ALTO = 526

SIDES = ["left", "right"]
SIDESSTR = ["left", "right"]

class Player():
    def __init__(self, side):
        self.side = side
        self.pos = [None, None]
        self.listaDisparo = []
        self.toco_otro = 0
    
    def get_pos(self):
        return self.pos

    def get_side(self):
        return self.side

    def set_pos(self, pos):
        self.pos = pos
    
    def get_lista(self):
        return self.listaDisparo
    
    def set_lista(self,lista):
        self.listaDisparo = lista
        
    def get_toco(self):
        return self.toco_otro
    
    def set_toco(self, num):
        self.toco_otro = num
        
    def __str__(self):
        return f"P<{SIDES[self.side], self.pos,self.listaDisparo}>"

class Proyectile():
    def __init__(self):
        self.pos=[ None, None ]

    def get_pos(self):
        return self.pos

    def set_pos(self, pos):
        self.pos = pos
    
    def __str__(self):
        return f"P<{self.pos}>"

    
class ProyectileSprite(pygame.sprite.Sprite):
    def __init__(self, bala):
        super().__init__()
        self.bala = bala
        if self.bala.velocidad > 0:
            self.image= pygame.image.load('bala.png')
        else:
            self.image= pygame.image.load('bala1.png')
        self.image = pygame.transform.scale(self.image,(30,30))
        self.rect = self.image.get_rect()
        self.update()

    def update(self):
        pos = self.bala.get_pos()
        self.rect.centerx, self.rect.centery = pos
        
    def __str__(self):
        return f"P<{self.bala.pos,self.bala.velocidad}>"
        
        
class Game():
    def __init__(self):
        self.players = [Player(i) for i in range(2)]
        self.listaDisparo1 = self.players[0].listaDisparo
        self.listaDisparo2 = self.players[1].listaDisparo
        self.lista_posiciones = []
        self.vidas = [5,5]
        self.running = True

    def get_player(self, side):
        return self.players[side]

    def set_pos_player(self, side, pos):
        self.players[side].set_pos(pos)
    
    def get_lista(self,side):
        return self.players[side].get_lista()
    
    def set_lista(self, side,lista):
        self.players[side].set_lista(lista)
    """    
    def get_puntos(self):
        return self.puntos
    def set_puntos(self, puntos):
        self.puntos = puntos
    """    
    def get_vidas(self):
        return self.vidas

    def set_vidas(self, vidas):
        self.vidas = vidas
        
    def get_toco_al_otro(self,side):
        return self.players[side].get_toco()
    
    def set_toco_al_otro(self, side, num):
        self.players[side].set_toco(num)
        
    def update(self, gameinfo):
        self.set_pos_player(LEFT_PLAYER, gameinfo['pos_left_player'])
        self.set_pos_player(RIGHT_PLAYER, gameinfo['pos_right_player'])
        self.set_lista(LEFT_PLAYER,gameinfo['lista_disparos_izquierda'])
        self.set_lista(RIGHT_PLAYER,gameinfo['lista_disparos_derecha'])
        self.set_vidas(gameinfo['vidas'])
        self.set_toco_al_otro(RIGHT_PLAYER, gameinfo['toco_derecha'])
        self.set_toco_al_otro(LEFT_PLAYER, gameinfo['toco_izquierda'])
        self.running = gameinfo['is_running']
        
    def is_running(self):
        return self.running

    def stop(self):
        self.running = False

    def __str__(self):
        return f"G<{self.players[RIGHT_PLAYER]}:{self.players[LEFT_PLAYER]}>"


class Pistolero(pygame.sprite.Sprite):
    def __init__(self,player):
        super().__init__()
        self.player = player
        if self.player.get_side() == RIGHT_PLAYER:
            self.image = pygame.image.load('pistoleroMirandoIzq.png')
        else:
            self.image = pygame.image.load('pistoleroMirandoDerecha.png')
        self.image = pygame.transform.scale(self.image,(66,66))
        self.rect = self.image.get_rect()
        self.update()
    
    def update(self):
        pos = self.player.get_pos()
        self.rect.centerx, self.rect.centery = pos

    def __str__(self):
        return f"S<{self.player}>"


class Display():
    def __init__(self, game):
        self.game = game
        self.pistol = [Pistolero(self.game.get_player(i)) for i in range(2)]
        self.all_sprites = pygame.sprite.Group()
        self.pistoleros_group = pygame.sprite.Group()
        self.bala_group = pygame.sprite.Group()
        for p in self.pistol:
            self.all_sprites.add(p)
            self.pistoleros_group.add(p)
        self.screen = pygame.display.set_mode(SIZE)
        self.clock =  pygame.time.Clock()  #FPS
        self.background = pygame.image.load('desierto.png')
        self.vidas_izq = pygame.image.load('vidas.png')
        self.vidas_izq = pygame.transform.scale(self.vidas_izq,(66,66))
        self.rect_izq = self.vidas_izq.get_rect()
        self.rect_izq.centerx, self.rect_izq.centery = [50,10]
        self.vidas_der = pygame.image.load('vidas.png')
        self.vidas_der = pygame.transform.scale(self.vidas_der,(66,66))
        self.rect_der = self.vidas_der.get_rect()
        self.rect_der.centerx, self.rect_der.centery = [SIZE[X]-50,10]
        self.win = pygame.image.load('ganador.png')
        self.win = pygame.transform.scale(self.win,(250,140))
        self.lose = pygame.image.load('perdedor.png')
        self.lose = pygame.transform.scale(self.lose,(250,140))
        pygame.init()
        pygame.mixer.init()
        self.musica = pygame.mixer.Sound('musica.wav')
        pygame.mixer.Sound(self.musica, -1)

    def analyze_events(self, side):
        events = []
        self.side = side
        self.balas_izq = self.game.get_lista(LEFT_PLAYER)
        self.balas_dch = self.game.get_lista(RIGHT_PLAYER)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    events.append("quit")
                elif event.key == pygame.K_UP:
                    events.append("up")
                elif event.key == pygame.K_DOWN:
                    events.append("down")
                elif event.key == pygame.K_LEFT:
                    events.append("left")
                elif event.key == pygame.K_RIGHT:
                    events.append("right")
                elif event.key == pygame.K_SPACE:
                    events.append("space")
            elif event.type == pygame.QUIT:
                events.append("quit")
        if side == RIGHT_PLAYER:
            for bala in self.balas_dch:
                bala_dib = ProyectileSprite(bala)
                if pygame.sprite.collide_rect(bala_dib, self.pistol[LEFT_PLAYER]):
                    events.append("collide_jugador")
        else:
            for bala in self.balas_izq:
                bala_dib = ProyectileSprite(bala)
                if pygame.sprite.collide_rect(bala_dib, self.pistol[RIGHT_PLAYER]):
                    events.append("collide_jugador")
        return events


    def refresh(self):
        self.all_sprites.update()
        self.bala_group.update()
        self.balas_izq = self.game.get_lista(LEFT_PLAYER)
        self.balas_dch = self.game.get_lista(RIGHT_PLAYER)
        for bala in self.balas_izq:
            bala_dib = ProyectileSprite(bala)
            self.bala_group.add(bala_dib)
        for bala in self.balas_dch:
            bala_dib = ProyectileSprite(bala)
            self.bala_group.add(bala_dib)
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.vidas_izq, (70,10))
        self.screen.blit(self.vidas_der, (SIZE[X]-136,10))
        #puntos = self.game.get_puntos()
        vidas = self.game.get_vidas()
        font = pygame.font.Font(None, 48)
        text = font.render(f"{vidas[LEFT_PLAYER]}", -1, WHITE)
        self.screen.blit(text, (94, 28))
        text = font.render(f"{vidas[RIGHT_PLAYER]}", -1, WHITE)
        self.screen.blit(text, (SIZE[X]-112, 28))
        self.bala_group.draw(self.screen)
        self.bala_group.empty()
        if vidas[0] <= 0:
            self.screen.blit(self.lose, (50,100))
            self.screen.blit(self.win, (SIZE[X]//2+50,100))
        elif vidas[1] <= 0:
            self.screen.blit(self.win, (50,100))
            self.screen.blit(self.lose, (SIZE[X]//2+50,100))
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

    def tick(self):
        self.clock.tick(FPS)

    @staticmethod
    def quit():
        pygame.quit()


def main(ip_address,port):
    try:
        with Client((ip_address, port), authkey=b'secret password') as conn:
            game = Game()
            side,gameinfo = conn.recv()
            print(f"I am playing {SIDESSTR[side]}")
            game.update(gameinfo)
            display = Display(game)
            while game.is_running():
                events = display.analyze_events(side)
                for ev in events:
                    conn.send(ev)
                    if ev == 'quit':
                        game.stop()
                conn.send("next")
                gameinfo = conn.recv()
                game.update(gameinfo)
                display.refresh()
                display.tick()
    except:
        traceback.print_exc()
    finally:
        pygame.quit()


if __name__=="__main__":
    ip_address = "127.0.0.1"
    if len(sys.argv)>2:
        ip_address = sys.argv[1]
        port = int(sys.argv[2])
    main(ip_address,port)
