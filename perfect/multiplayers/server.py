#!/usr/bin/env python3
import turtle, tkinter, socket, io, time
from select import select
from laby import Laby
from misc import *

# laby generation
log = io.StringIO()

main = tkinter.Tk()
l = tkinter.Label(main,text="Generating... Please wait.")
l.pack(fill="both",expand=True)
can = tkinter.Canvas(main)
sc = turtle.TurtleScreen(can)
sc.tracer(n=120)

laby = Laby(sc,unit=20, border=Area((100,100),(-100,-100)),to_file=log)
for loop in laby :
        pass

main.destroy()

log.write("\n")
log = log.getvalue().encode()

# socket part
s = socket.socket()
s.bind(("",65535))
s.listen()
players = list()
t = time.time()
while time.time() - t < 10 : # phase 1 lasts 10 sec
        asked = select([s,],list(),list(),0)[0]
        for co in asked :
                client, info = co.accept()
                print(info)
                players.append(client)
                client.sendall(log)

print("______________phase 2__________________")
while True :
        ordering = select(players,list(),list(),0)[0]
        for orderer in ordering :
                order = orderer.recv(1)
                if order == b"W" : # W for Win
                        s.close()
                        exit(0)
                order = bytes([players.index(orderer), order[0]])
                for player in players :
                        player.send(order)
