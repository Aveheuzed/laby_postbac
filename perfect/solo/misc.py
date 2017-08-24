# !/usr/bin/env python3
import turtle, os
from random import choice

"""Classes used by the rest of the programm"""

class Converter :
        """This class' function turn Cells or Walls to Cells or Walls,
        returnning sets containing the closest cells/walls"""

        def ctoc(unit,x,y):
                return {\
                (x-unit,y),(x+unit,y),\
                (x,y-unit),(x,y+unit)\
                }

        def ctow(unit,x,y):
                return {\
                (x-unit/2,y),(x+unit/2,y),\
                (x,y-unit/2),(x,y+unit/2)\
                }

        def wtoc(unit,x,y):
                if y%unit :
                        return {(x-unit/2,y), (x+unit/2,y)}
                else :
                        return {(x, y-unit/2),(x, y+unit/2)}

        def wtow(unit,x,y):
                walls = set()
                if x%unit :
                        # the wall is horizontal
                        walls.update({(x-unit,y),(x+unit,y)})
                else :
                        # the wall is vertical
                        walls.update({(x,y-unit),(x,y+unit)})
                unit /= 2
                walls.update({\
                (x-unit,y-unit),(x-unit,y+unit),\
                (x+unit,y-unit),(x+unit,y+unit)})
                return walls


class PreciseTurtle(turtle.RawTurtle):
        """Just rounding the coordinates
        (turtle's coordinates system being not accurate)"""

        def xcor(self):
                return round(super().xcor())

        def ycor(self):
                return round(super().ycor())

        def pos(self):
                return (self.xcor(),self.ycor())

        def distance(self,*other):
                return round(super().distance(*other))

        def forward(self,dist):
                """now returns the coordinates of the middle of the line\
                drawn (i.e. if turtle down)
                See turtle.RawTurtle.forward for more help"""
                pos0 = self.pos()
                super().forward(dist)
                if self.isdown() :
                        return Area(pos0,self.pos()).middle


class Area:
        """This class represents a 2-D area (possibly flat).
        Use it to determine wether a dot is, or not,
        in that area (not including the border)"""

        def __init__(self,corner_1,corner_2):
                self.xs = [corner_1[0], corner_2[0]]
                self.xs.sort()
                self.ys = [corner_1[1], corner_2[1]]
                self.ys.sort()

        def __contains__(self,x) :
                x,y = x
                return (self.xs[0] < x < self.xs[1]) and  (self.ys[0] < y < self.ys[1])

        # def is_on_border(self,x,y=None):
        #         if y is None :
        #                 x,y = x
        #         return ((x in self.xs) or (y in self.ys)) and ((x,y) in self)

        middle = property(lambda self:(sum(self.xs)/2,sum(self.ys)/2))


class Path :
        """This represents a corridor (with the left and right walls)"""

        def __init__(self,screen,unit=20,x=0,y=0,heading=0):
                """screen is an instance of turtle.TurtleScreen
                unit is the width of the corridor
                x and y are the spawn coordinates for the left walls
                heading (in degrees) is the corridor's heading"""
                self.unit = unit
                self.screen = screen

                self.left = PreciseTurtle(self.screen,undobuffersize=1,\
                visible=False)
                self.left.speed(0)
                self.left.setheading(heading)
                self.left.up()
                self.left.goto(x,y)

                self.right = self.left.clone()
                self.right.right(90)
                self.right.forward(self.unit)
                self.right.left(90)

                self.down()

                self.walls = set()
                # this contains the coordinates of the middles
                # of the walls of this corridor

                self._pending_child = 0
                # see mk_child doc

                self._lock = False
                # if True, a movement is being done

        def _redirect(funcname):
                """Methods builder used to redirect method calls
                 to self.left and self.right"""
                def f_(self,*args,**kwargs):
                        getattr(self.left,funcname)(*args,**kwargs)
                        getattr(self.right,funcname)(*args,**kwargs)
                f_.__name__ = funcname
                return f_

        for name in ["up","down","st","ht","clear","speed","color"] :
                exec("{0} = _redirect('{0}')".format(name))
        del name

        def pos(self):
                """Returns the coordinates of the middle of [self.left ; self.right]"""
                return Area(self.left.pos(), self.right.pos()).middle

        __del__ = ht

        """Movement methods :
        they are coroutines, working as follow :
        - first, they do a dummy move, and yield the coordinates
        of the middle of the square they filled
        - then, a boolean should be sent, telling wether the move should
        really be done (if not, it is assumed True)
        - dummy yieling, to allow the user to enter properly into a loop
        (it is the children code, as defined in mk_child)
        - if that boolean is True, the move is proceeded,
        and children may be yielded

        example :

        children = list()
        move = path.forward()
        landing_point = next(move)
        x,y = next(move)
        # the two following lines can be omitted
        if (x,y) in Area(...):# we want the movement to be
                move.send(True)
        else :# we don't
                move.send(False)
        for child in move :
                children.append(child)"""

        def forward(self):
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True

                left0, right0 = self.left.pos(), self.right.pos()
                self.up()
                self.left.forward(self.unit)
                self.right.forward(self.unit)
                left1, right1 = self.left.pos(), self.right.pos()

                yield Area(left1,right1).middle
                proceed = (yield Area(left0,right1).middle)
                if proceed is None :
                        proceed = True
                yield self._pending_child

                if not proceed :
                        # cancelling
                        self.left.undo()
                        self.right.undo()
                        self.down()
                else :
                        if self._pending_child == 3 :
                                self.down()
                                # make a child left
                                yield Path(self.screen,self.unit,*left0,\
                                self.left.heading()+90)
                                # make a child right
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()-90)
                        elif self._pending_child == 2 :
                                # make a true left wall
                                self.left.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                # make a child right
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()-90)
                        elif self._pending_child == 1 :
                                # make a true right wall
                                self.right.undo()
                                self.down()
                                self.walls.add(self.right.forward(self.unit))
                                # make a child left
                                yield Path(self.screen,self.unit,*left0,\
                                self.right.heading()+90)
                        else :
                                # make two true walls
                                self.left.undo()
                                self.right.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                self.walls.add(self.right.forward(self.unit))
                        self.mk_child(0)
                self._lock = False

        def turn_left(self):
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True

                left0, right0 = self.left.pos(), self.right.pos()
                self.up()
                self.right.forward(self.unit)
                self.left.forward(self.unit)
                left1, right1 = self.left.pos(), self.right.pos()

                self.left.undo()
                yield Area(left0,left1).middle
                proceed = (yield Area(left0,right1).middle)
                if proceed is None :
                        proceed = True
                yield self._pending_child

                if not proceed :
                        # cancelling
                        self.right.undo()
                        self.down()
                else :
                        if self._pending_child == 3 :
                                self.right.left(90)
                                self.right.forward(self.unit)
                                right2 = self.right.pos()
                                self.down()
                                # make a child
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()+180)
                                # make a child
                                yield Path(self.screen,self.unit,*right2,\
                                self.right.heading()-90)
                        elif self._pending_child == 2 :
                                # make a true wall
                                self.right.undo()
                                self.down()
                                self.walls.add(self.right.forward(self.unit))
                                self.right.left(90)
                                self.up()
                                self.right.forward(self.unit)
                                right2 = self.right.pos()
                                # make a child
                                yield Path(self.screen,self.unit,*right2,\
                                self.right.heading()-90)
                        elif self._pending_child == 1 :
                                # make a true wall
                                self.down()
                                self.right.left(90)
                                self.walls.add(self.right.forward(self.unit))
                                right2 = self.right.pos()
                                # make a child
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()+180)
                        else :
                                # make two true walls
                                self.right.undo()
                                self.down()
                                self.walls.add(self.right.forward(self.unit))
                                self.right.left(90)
                                self.walls.add(self.right.forward(self.unit))
                        self.left.left(90)
                        self.mk_child(0)
                self._lock = False

        def turn_right(self):
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True

                left0, right0 = self.left.pos(), self.right.pos()
                self.up()
                self.left.forward(self.unit)
                self.right.forward(self.unit)
                left1, right1 = self.left.pos(), self.right.pos()

                self.right.undo()
                yield Area(right0,right1).middle
                proceed = (yield Area(left1,right0).middle)
                if proceed is None :
                        proceed = True
                yield self._pending_child

                if not proceed :
                        # cancelling
                        self.left.undo()
                        self.down()
                else :
                        if self._pending_child == 3 :
                                self.left.right(90)
                                self.left.forward(self.unit)
                                left2 = self.left.pos()
                                self.down()
                                # make a child
                                yield Path(self.screen,self.unit,*left0,\
                                self.left.heading()-180)
                                # make a child
                                yield Path(self.screen,self.unit,*left1,\
                                self.left.heading()+90)
                        elif self._pending_child == 2 :
                                # make a true wall
                                self.left.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                self.left.right(90)
                                self.up()
                                self.left.forward(self.unit)
                                left2 = self.left.pos()
                                # make a child
                                yield Path(self.screen,self.unit,*left1,\
                                self.left.heading()+90)
                        elif self._pending_child == 1 :
                                # make a true wall
                                self.down()
                                self.left.right(90)
                                self.walls.add(self.left.forward(self.unit))
                                left2 = self.left.pos()
                                # make a child
                                yield Path(self.screen,self.unit,*left0,\
                                self.left.heading()-180)
                        else :
                                # make two true walls
                                self.left.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                self.left.right(90)
                                self.walls.add(self.left.forward(self.unit))
                        self.right.right(90)
                        self.mk_child(0)
                self._lock = False

        def terminate(self):
                """Makes a bag-end"""
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True

                self.left.right(90)
                self.walls.add(self.left.forward(self.unit))
                self.ht()

        def mk_child(self,side=0):
                """The next movement will make a fork \
                (an other instance of Path) and return it.
                onmove can be either 1 (left/first movement),
                2 (right/second movement), or 3 (both)
                Let side=0 to cancel a pending child."""
                assert side in range(4)
                self._pending_child = side

        def get_child_state(self):
                return self._pending_child

        def __iter__(self):
                return self

        def __next__(self):
                """WARNING : infinite loop
                return a random move (to iter on)"""
                return choice(\
                (self.forward, self.turn_left, self.turn_right))()
