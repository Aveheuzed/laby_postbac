#!/usr/bin/env python3

import turtle, tkinter
from laby import Laby, Area
from sprite import Sprite

#preparing the environment...
main = tkinter.Tk()
can = turtle.ScrolledCanvas(main)
can.pack(fill="both",expand=True)
screen = turtle.TurtleScreen(can)

# we now can make a laby, and put a sprite on it
laby = Laby(screen, border=Area((100,100),(-100,-100)))
for loop in laby :
        pass
# politics about player :
# we proceed in two halves, this way, if a wall is hit, it will impeach twice the move
# This all is to keep a step of one cell (not one half)
player = Sprite(screen,step=laby.unit//2,forbidden=laby.walls)

# go to the middle of one cell
turtle.RawTurtle.forward(player, player.step)
player.left(90)
turtle.RawTurtle.forward(player, player.step)
# we have to use turtle.RawTurtle.forward to avoid collision checking

def move(sprite,heading):
        """General movement function """
        sprite.setheading(heading)
        sprite.forward()
        sprite.forward()

def deco(f,sprite,heading):
        """We will decorate the move function in order not to need parameter on call"""
        def f_():
                return f(sprite,heading)
        f_.__name__ = f.__name__
        return f_

screen.onkey(deco(move,player,0),"Right")
screen.onkey(deco(move,player,90),"Up")
screen.onkey(deco(move,player,180),"Left")
screen.onkey(deco(move,player,270),"Down")
screen.listen()# to catch the events

main.mainloop()
