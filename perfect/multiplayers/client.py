#!/usr/bin/env python3
import turtle, tkinter, socket, io, threading
from select import select
from laby import Laby
from misc import *
from sprite import Sprite

class GUI :
        def __init__(self,log, socket):
                self.log = log
                self.socket = socket

                self.main = tkinter.Tk()
                self.can = tkinter.Canvas(self.main)
                self.can.pack(fill="both",expand=True)
                self.sc = turtle.TurtleScreen(self.can)
                self.sc.tracer(n=120)

                self.laby = Laby(self.sc,\
                unit=20,border=Area((100,100),(-100,-100)),from_file=self.log)
                for loop in self.laby :
                        pass

                self.sc.tracer(n=1)

                self.main.bind("<Right>", self.mkmove(b"r"))
                self.main.bind("<Up>", self.mkmove(b"u"))
                self.main.bind("<Left>", self.mkmove(b"l"))
                self.main.bind("<Down>", self.mkmove(b"d"))


                self.ready = True

        def mkmove(self, letter):
                def f(ev):
                        try :
                                self.socket.send(letter)
                        except :
                                self.main.destroy()
                return f

        def mainloop(self):
                self.main.mainloop()


class ServerOnPhase2(threading.Thread):

        def __init__(self, socket, laby):
                super().__init__()
                self.socket = socket
                self.laby = laby

        def run(self):
                players = list()
                newp = Sprite(self.laby.screen, self.laby.unit//2, self.laby.walls)
                turtle.RawTurtle.forward(newp, newp.step)
                newp.left(90)
                turtle.RawTurtle.forward(newp, newp.step)
                players.append(newp)
                while all(player.pos() in self.laby.border for player in players) :
                        if len(select([self.socket,],list(),list())[0]) :
                                order =self.socket.recv(2)
                                index , order = order[0],order[1:]
                                while index >= len(players) :
                                        newp = Sprite(self.laby.screen, self.laby.unit//2, self.laby.walls)
                                        turtle.RawTurtle.forward(newp, newp.step)
                                        newp.left(90)
                                        turtle.RawTurtle.forward(newp, newp.step)

                                        players.append(newp)
                                if order == b"r" :
                                        players[index].setheading(0)
                                elif order == b"u" :
                                        players[index].setheading(90)
                                elif order == b"l" :
                                        players[index].setheading(180)
                                elif order == b"d" :
                                        players[index].setheading(270)
                                players[index].forward()
                                players[index].forward()

                self.socket.send(b"W")
                self.socket.close()


# downloading the laby's pattern
s = socket.socket()
s.connect(("localhost",65535))

log = io.BytesIO()
while not log.getvalue().endswith(b"\n\n") :
        log.write(s.recv(1024))

log = io.StringIO(log.getvalue().decode())
# generating the laby
gui = GUI(log,s)

server = ServerOnPhase2(s,gui.laby)
server.start()
gui.mainloop()
server.join()
