from multiprocessing.connection import Listener
from multiprocessing import Process, Manager, Value, Lock
import traceback
import sys
import time

LEFT_PLAYER = 0
RIGHT_PLAYER = 1
SIDESSTR = ["left", "right"]
SIZE = (700, 526)
X=0
Y=1
DELTA = 30

class Player():
    def __init__(self, side):
        self.side = side
        self.toco_otro = 0
        self.tiempo_espera = 0
        self.listaDisparo = []
        if side == LEFT_PLAYER:
            self.pos = [33, SIZE[Y]//2]
        else:
            self.pos = [SIZE[X] - 33, SIZE[Y]//2]

    def enfriar_disparo(self):
        self.temporizador = 10
        if self.tiempo_espera >= self.temporizador:
            self.tiempo_espera = 0
        elif self.tiempo_espera > 0:
            self.tiempo_espera +=1
        
    def get_pos(self):
        return self.pos

    def get_side(self):
        return self.side
    
    def get_lista(self):
        return self.listaDisparo
    
    def get_toco_al_otro(self):
        return self.toco_otro
    
    def moveDown(self):
        self.pos[Y] += DELTA
        if self.pos[Y] > SIZE[Y] - 33:
            self.pos[Y] = SIZE[Y] - 33

    def moveUp(self):
        self.pos[Y] -= DELTA
        if self.pos[Y] <  33:
            self.pos[Y] = 33
    
    def moveLeft(self):
        side = self.side
        if side == LEFT_PLAYER:
            self.pos[X] -= DELTA
            if self.pos[X] < 33:
                self.pos[X] =  33
        else:
            self.pos[X] -= DELTA
            if self.pos[X] <(SIZE[X]//2) +33:
                self.pos[X] = (SIZE[X]//2) +33
                
    def moveRight(self):
        side = self.side
        if side == LEFT_PLAYER:
            self.pos[X] += DELTA
            if self.pos[X] > (SIZE[X]//2) -33:
                self.pos[X] = (SIZE[X]//2) -33
        else:
            self.pos[X] += DELTA
            if self.pos[X] > SIZE[X] - 33:
                self.pos[X] = SIZE[X] - 33 
                
    def shoot(self):
        x = self.pos[X]
        y = self.pos[Y]
        self.tiempo_espera = 1
        bala = Proyectile(x,y)
        self.listaDisparo.append(bala)
    
    def restablecer(self):
        if self.side == LEFT_PLAYER:
            self.pos = [33, SIZE[Y]//2]
        else:
            self.pos = [SIZE[X] - 33, SIZE[Y]//2]
            
    def borrar_bala(self, pos):
        for bala in self.listaDisparo:
            if abs(bala.pos[X] - pos[X]) <= 48:
                if abs(bala.pos[Y] - pos[Y]) <= 48:
                    self.listaDisparo.remove(bala)
                    self.toco_otro = 1
            
    def update(self):
        self.toco_otro = 0
        for bala in self.listaDisparo:
            if bala.pos[X] < 0 or bala.pos[X] > SIZE[X]:
                self.listaDisparo.remove(bala)
        
    def __str__(self):
        return f"P<{SIDESSTR[self.side]}, {self.pos}>"

class Proyectile():
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.pos = [self.x , self.y]
        if self.x > (SIZE[X]//2):
            self.velocidad = -10
        else:
            self.velocidad = 10
        
    def get_pos(self):
        return self.pos

    def update(self):
        self.pos[X] += self.velocidad
        
    def __str__(self):
        return f"P<{self.pos, self.velocidad}>"
        
    
    

class Game():
    def __init__(self, manager):
        self.players = manager.list( [Player(LEFT_PLAYER), Player(RIGHT_PLAYER)] )
        self.score = manager.list( [0,0] )
        self.vidas = manager.list([5,5])
        self.running = Value('i', 1) # 1 running
        self.lock = Lock()
        
    def get_player(self, side):
        return self.players[side]
    """
    def get_score(self):
        return list(self.score)
    """
    def get_vidas(self):
        return list(self.vidas)
    
    def get_toco_al_otro(self,player):
        return self.players[player].toco_otro

    def is_running(self):
        return self.running.value == 1

    def stop(self):
        vidas = self.get_vidas()
        if vidas[0] <= 0 or vidas[1] <= 0:
            time.sleep(10)
            self.running.value = 0
    
    def finish(self):
        self.running.value = 0
        
    def moveUp(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.moveUp()
        self.players[player] = p
        self.lock.release()

    def moveDown(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.moveDown()
        self.players[player] = p
        self.lock.release()

    def moveRight(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.moveRight()
        self.players[player] = p
        self.lock.release()
            
    def moveLeft(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.moveLeft()
        self.players[player] = p
        self.lock.release()
        
    def shoot(self,player):
       self.lock.acquire()
       p = self.players[player]
       if p.tiempo_espera == 0:
           p.shoot()
       self.players[player] = p
       self.lock.release()
       
    def check(self,player):
       self.lock.acquire()
       p = self.players[player]
       if  p.side == RIGHT_PLAYER and self.players[LEFT_PLAYER].get_toco_al_otro() >0 :
           p.restablecer()
       elif  p.side == LEFT_PLAYER and self.players[RIGHT_PLAYER].get_toco_al_otro() > 0:
           p.restablecer()
       self.players[player] = p
       self.lock.release()
        
    def actualizar(self, player):
        self.lock.acquire()
        p = self.players[player]
        p.enfriar_disparo()
        p.update()
        for bala in p.listaDisparo:
            bala.update()
        self.players[player] = p
        self.lock.release()
        
    def collide_player(self,player):
        self.lock.acquire()
        p = self.players[player]
        if p.side == RIGHT_PLAYER:
            pos = self.players[LEFT_PLAYER].pos
            p.borrar_bala(pos)
            self.toco_otro = 1
            self.vidas[LEFT_PLAYER] -= 1
            """
            if self.vidas[LEFT_PLAYER] <=0:
                self.vidas[LEFT_PLAYER] =3
                self.vidas[RIGHT_PLAYER] =3
                self.score[RIGHT_PLAYER] += 1
                self.players[LEFT_PLAYER].restablecer()
                self.players[RIGHT_PLAYER].restablecer()
            """
        else:
            pos = self.players[RIGHT_PLAYER].pos
            p.borrar_bala(pos)
            self.toco_otro = 1
            self.vidas[RIGHT_PLAYER] -= 1
            """
            if self.vidas[RIGHT_PLAYER] <=0:
                self.vidas[RIGHT_PLAYER] =3
                self.vidas[RIGHT_PLAYER] =3
                #self.score[LEFT_PLAYER] += 1
                self.players[LEFT_PLAYER].restablecer()
                self.players[RIGHT_PLAYER].restablecer()
            """
        self.players[player] = p
        self.lock.release()
   

    def get_info(self):
        info = {
            'pos_left_player': self.players[LEFT_PLAYER].get_pos(),
            'pos_right_player': self.players[RIGHT_PLAYER].get_pos(),
            'lista_disparos_derecha': self.players[RIGHT_PLAYER].get_lista(),
            'lista_disparos_izquierda':self.players[LEFT_PLAYER].get_lista(),
            #'score': list(self.score),
            'vidas': list(self.vidas),
            'toco_derecha': self.get_toco_al_otro(RIGHT_PLAYER),
            'toco_izquierda': self.get_toco_al_otro(LEFT_PLAYER),
            'is_running': self.running.value == 1
            
        }
        return info
   
    def __str__(self):
        return f"G<{self.players[RIGHT_PLAYER]}:{self.players[LEFT_PLAYER]}:{self.running.value}>"

            
def player(side, conn, game):
    try:
        print(f"starting player {SIDESSTR[side]}:{game.get_info()}")
        conn.send( (side, game.get_info()) )
        while game.is_running():
            command = ""
            while command != "next":
                command = conn.recv()
                if command == "up":
                    game.moveUp(side)
                elif command == "down":
                    game.moveDown(side)
                elif command == "left":
                    game.moveLeft(side)
                elif command == "right" :
                    game.moveRight(side)
                elif command == "space":
                    game.shoot(side)
                elif command == "collide_jugador":
                    game.collide_player(side)
                elif command == "quit":
                    game.finish()
                    
            if side == 1:
                game.check(LEFT_PLAYER)
                game.check(RIGHT_PLAYER)
                game.actualizar(LEFT_PLAYER)   
                game.actualizar(RIGHT_PLAYER)
                if game.stop():
                    return f"GAME OVER"
            conn.send(game.get_info())
    except:
        traceback.print_exc()
        conn.close()
    finally:
        print(f"Game ended {game}")


def main(ip_address,port):
    manager = Manager()
    try:
        with Listener((ip_address, port),
                      authkey=b'secret password') as listener:
            n_player = 0
            players = [None, None]
            game = Game(manager)
            while True:
                print(f"accepting connection {n_player}")
                conn = listener.accept()
                players[n_player] = Process(target=player,
                                            args=(n_player, conn, game))
                n_player += 1
                if n_player == 2:
                    players[0].start()
                    players[1].start()
                    n_player = 0
                    players = [None, None]
                    game = Game(manager)

    except Exception as e:
        traceback.print_exc()

if __name__=='__main__':
    ip_address = "127.0.0.1"
    if len(sys.argv)>2:
        ip_address = sys.argv[1]
        port = int(sys.argv[2])
    main(ip_address,port)

