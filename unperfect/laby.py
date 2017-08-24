#!/usr/bin/env python3
import turtle, os
from random import choice
from misc import *
# from time import clock


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
        in that area (including the border)"""

        def __init__(self,corner_1,corner_2):
                self.xs = [corner_1[0], corner_2[0]]
                self.xs.sort()
                self.ys = [corner_1[1], corner_2[1]]
                self.ys.sort()

        def _deco(f):
                def f_(self,x,y=None):
                        if y is None :
                                x,y = x
                        return f(self,x,y)
                f_.__name__ = f.__name__
                return f_

        @_deco
        def __contains__(self,x,y) :
                return (self.xs[0] <= x <= self.xs[1]) and  (self.ys[0] <= y <= self.ys[1])

        @_deco
        def is_on_border(self,x,y):
                return ((x in self.xs) or (y in self.ys)) and ((x,y) in self)

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
                #if True, a movement is being done

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
        x,y = next(move)
        #the two following lines can be omitted
        if (x,y) in Area(...):#we want the movement to be
                move.send(True)
        else :#we don't
                move.send(False)
        for child in move :
                children.append(child)"""

        # debug decorator
        # def  _check(f):
        #         def f_(self):
        #                 yield from f(self)
        #                 assert self.left.heading() == self.right.heading()
        #                 assert self.left.distance(self.right) == self.unit
        #                 assert (self.left.xcor()==self.right.xcor())^ (self.left.ycor()==self.right.ycor())
        #         f_.__name__ = f.__name__
        #         return f_

        # @_check
        def forward(self):
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True
                left0, right0 = self.left.pos(), self.right.pos()
                self.up()
                self.left.forward(self.unit)
                self.right.forward(self.unit)
                left1, right1 = self.left.pos(), self.right.pos()
                proceed = (yield Area(left0,right1).middle)
                if proceed is None :
                        proceed = True
                yield self._pending_child
                if not proceed :
                        self.left.undo()
                        self.right.undo()
                        self.down()
                else :
                        if self._pending_child == 3 :
                                self.down()
                                #make a child left
                                yield Path(self.screen,self.unit,*left0,\
                                self.left.heading()+90)
                                #make a child right
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()-90)
                        elif self._pending_child == 2 :
                                #make a true left wall
                                self.left.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                #make a child right
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()-90)
                        elif self._pending_child == 1 :
                                #make a true right wall
                                self.right.undo()
                                self.down()
                                self.walls.add(self.right.forward(self.unit))
                                #make a child left
                                yield Path(self.screen,self.unit,*left0,\
                                self.right.heading()+90)
                        else :
                                #make two true walls
                                self.left.undo()
                                self.right.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                self.walls.add(self.right.forward(self.unit))
                        self.mk_child(0)
                self._lock = False

        # @_check
        def turn_left(self):
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True
                left0, right0 = self.left.pos(), self.right.pos()
                self.up()
                self.right.forward(self.unit)
                left1, right1 = self.left.pos(), self.right.pos()
                proceed = (yield Area(left0,right1).middle)
                if proceed is None :
                        proceed = True
                yield self._pending_child
                if not proceed :
                        self.right.undo()
                        self.down()
                else :
                        if self._pending_child == 3 :
                                self.right.left(90)
                                self.right.forward(self.unit)
                                right2 = self.right.pos()
                                self.down()
                                #make a child
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()+180)
                                #make a child
                                yield Path(self.screen,self.unit,*right2,\
                                self.right.heading()-90)
                        elif self._pending_child == 2 :
                                #make a true wall
                                self.right.undo()
                                self.down()
                                self.walls.add(self.right.forward(self.unit))
                                self.right.left(90)
                                self.up()
                                self.right.forward(self.unit)
                                right2 = self.right.pos()
                                #make a child
                                yield Path(self.screen,self.unit,*right2,\
                                self.right.heading()-90)
                        elif self._pending_child == 1 :
                                #make a true wall
                                self.down()
                                self.right.left(90)
                                self.walls.add(self.right.forward(self.unit))
                                right2 = self.right.pos()
                                #make a child
                                yield Path(self.screen,self.unit,*right1,\
                                self.right.heading()+180)
                        else :
                                #make two true walls
                                self.right.undo()
                                self.down()
                                self.walls.add(self.right.forward(self.unit))
                                self.right.left(90)
                                self.walls.add(self.right.forward(self.unit))
                        self.left.left(90)
                        self.mk_child(0)
                self._lock = False

        # @_check
        def turn_right(self):
                if self._lock :
                        raise RuntimeError("A movement is already being done")
                self._lock = True
                left0, right0 = self.left.pos(), self.right.pos()
                self.up()
                self.left.forward(self.unit)
                left1, right1 = self.left.pos(), self.right.pos()
                proceed = (yield Area(left1,right0).middle)
                if proceed is None :
                        proceed = True
                yield self._pending_child
                if not proceed :
                        self.left.undo()
                        self.down()
                else :
                        if self._pending_child == 3 :
                                self.left.right(90)
                                self.left.forward(self.unit)
                                left2 = self.left.pos()
                                self.down()
                                #make a child
                                yield Path(self.screen,self.unit,*left0,\
                                self.left.heading()-180)
                                #make a child
                                yield Path(self.screen,self.unit,*left1,\
                                self.left.heading()+90)
                        elif self._pending_child == 2 :
                                #make a true wall
                                self.left.undo()
                                self.down()
                                self.walls.add(self.left.forward(self.unit))
                                self.left.right(90)
                                self.up()
                                self.left.forward(self.unit)
                                left2 = self.left.pos()
                                #make a child
                                yield Path(self.screen,self.unit,*left1,\
                                self.left.heading()+90)
                        elif self._pending_child == 1 :
                                #make a true wall
                                self.down()
                                self.left.right(90)
                                self.walls.add(self.left.forward(self.unit))
                                left2 = self.left.pos()
                                #make a child
                                yield Path(self.screen,self.unit,*left0,\
                                self.left.heading()-180)
                        else :
                                #make two true walls
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

        def __iter__(self):
                return self

        def __next__(self):
                """WARNING : infinite loop
                return a random move (to iter on)"""
                return choice(\
                (self.forward, self.turn_left, self.turn_right))()


class Laby :

        def __init__(self,screen,from_file=None,to_file=None,\
        unit=20, border=None):
                """screen is an instance of turtle.TurtleScreen on witch to draw.
                from_file and to_file are file descriptors :
                - to_file ('wt') is a 'log file' on witch a description of our\
                laby will be written
                - that file can be later used as from_file ('rt') to re-draw the\
                same.
                - unit : see Path documentation
                - border : the whole laby won't override the borders of this Area instance"""

                # we want either None,
                # or a text (not binary) file to read from / write to
                if from_file is not None :
                        assert from_file.readable()
                if to_file is not None :
                        assert to_file.writable()
                self.from_file = from_file
                self.to_file = to_file

                if border is not None :
                        assert isinstance(border,Area)
                else :
                        f = float("inf")
                        border = Area((f,f),(-f,-f))
                self.border = border

                self.unit = unit
                self.screen = screen
                self.walls = set()
                self.out = None
                self.turtles = [Path(self.screen,self.unit)]
                self.turtles[0].ht()
                self.pos_tracker = set() # all the cells we've filled

        def __iter__(self):
                return self

        def __next__(self):
                """Doesn't return anything, just continue to build"""
                if not len(self.turtles):
                        raise StopIteration
                adding = list()
                remove = set()
                for i,path in enumerate(self.turtles) :
                        if self.from_file is None :
                                path.mk_child(choice(range(3)))
                                move = next(path)
                        else :
                                row = next(self.from_file)
                                path.mk_child(int(row[0]))
                                move = getattr(path,row[1:-1])()
                        pos = next(move)
                        if pos in self.pos_tracker or pos not in self.border :
                                print(move.send(False), file=self.to_file, end="")
                                remove.add(i)
                        else :
                                self.pos_tracker.add(pos)
                                print(move.send(True), file=self.to_file, end="")
                        print(move.__name__, file=self.to_file)
                        adding.extend(move)
                        if i in remove :
                                path.terminate()
                        self.walls.update(path.walls)

                self.turtles = [x for i,x in enumerate(self.turtles)\
                                if i not in remove] + adding


if __name__ == '__main__':
        main = turtle.TK.Tk()
        can = turtle.ScrolledCanvas(main)
        can.pack(fill="both",expand=True)
        sc = turtle.TurtleScreen(can)
        sc.tracer(n=60)# this line is MAGIC !!!!
        laby = Laby(sc,unit=10,border=Area((100,100),(-100,-100)),to_file=open(os.devnull,"wt"))
        _ = clock()
        for loop in laby :
                pass
        print(clock()-_)
        sc.update()
