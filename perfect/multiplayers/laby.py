#!/usr/bin/env python3
from misc import *


class Laby :

        def __init__(self,screen,from_file=None,to_file=None,\
        unit=20, border=None):
                """screen is an instance of turtle.TurtleScreen on witch to draw. To work
                speed enough, I advice you to set 'screen.tracer(n=60)' and to often perform updates ;
                from_file and to_file are file descriptors :
                - to_file ('wt') is a 'log file' on witch a description of our\
                laby will be written
                - that file can be later used as from_file ('rt') to re-draw the\
                same ;
                unit : see Path documentation ;
                border : if specified, we will fill that Area without overflowing"""

                # from_file : None, or  a readable file
                # to_file : /dev/null, or a writable file
                if from_file is not None :
                        assert from_file.readable()
                if to_file is not None :
                        assert to_file.writable()
                else :
                        to_file = open(os.devnull,"wt")
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

                self.walls = set() # this is containing the middles of each wall we will draw
                self.turtles = [Path(self.screen,self.unit)]
                self.turtles[0].ht()
                self.pos_tracker = set() # there are the centers of the cells we will fill
                self.pos_turtle = {self.turtles[0]:self.turtles[0].pos()} # we define this
                # to get a fast access to the position of each Path  we have

                self.out = None # the only exit

        def __iter__(self):
                return self

        def __next__(self):
                """Doesn't return anything, just continue to build"""
                if not len(self.turtles):
                        raise StopIteration
                        # work finished !

                adding = list() # the Path that will be created on this round
                remove = set()# the Path that will be deleted on this round
                for i,path in enumerate(self.turtles) :
                        del self.pos_turtle[path]
                        start = path.pos()

                        # defining the movement to be done
                        if self.from_file is not None :
                                try :
                                        row = next(self.from_file)
                                except StopIteration :
                                        self.from_file = None
                                else :
                                        path.mk_child(int(row[0]))
                                        move = getattr(path,row[1:-1])()
                        if self.from_file is None :
                                path.mk_child(choice(range(3)))
                                move = next(path)

                        stop = next(move)
                        pos = next(move)

                        if pos in self.pos_tracker or pos not in self.border :
                                # we can't do the movement
                                print(move.send(False), file=self.to_file, end="")
                                remove.add(i)
                        else :
                                self.pos_tracker.add(pos)
                                # in order not to let holes but to fill the whole of self.border,
                                # we sometimes have to make 2 forks (childing state=3)
                                if self.from_file is None :
                                        if stop in self.walls or \
                                        stop in self.pos_turtle.values() or \
                                        not all(x in self.border for x in Converter.wtoc(self.unit,*stop)) :
                                                path.mk_child(3)
                                        elif self.is_isolated(Converter.ctow(self.unit,*pos)-{start,stop}):
                                                # we have separated this case because is_isolated is veeery slow :
                                                # i.e. the least it is called, the best
                                                path.mk_child(3)
                                print(move.send(True), file=self.to_file, end="")
                        print(move.__name__, file=self.to_file)

                        for m in move :
                                # getting the children
                                adding.append(m)
                                self.pos_turtle[m] = m.pos()
                        if i in remove :
                                if pos in self.border :
                                        path.terminate()
                                else :
                                        # making the exit ;
                                        # we keep the last possible one,
                                        #  so that it is the farthest from the center (from (self.unit/2 ; self.unit/2))
                                        if self.out is not None :
                                                self.out.terminate()
                                                self.walls.update(self.out.walls)
                                        self.out = path
                        else :
                                self.pos_turtle[path] = stop # i.e., path.pos()
                        self.walls.update(path.walls)

                # cleaning before the next loop
                self.turtles = [x for i,x in enumerate(self.turtles)\
                                if i not in remove] + adding

        def is_isolated(self,walls):
                """Given the 2 walls a Path is about to draw (including the forks),
                tells wether that Path should make 2 forks to keep the Laby perfect."""
                # We parse the cells bordering the walls ; if they are going to be enclosed,
                #  then forks must be done
                # Moreover, to avoid large holes (more than 2 cells), we search then a path
                # to the void for those cells ; if we don't find one, forks must be done
                # note : the second test is sufficient alone (I think), but it is very slow,
                # so that the first one saves time in most cases
                allwalls = self.walls|walls
                for wall in walls :
                        for cell in Converter.wtoc(self.unit,*wall):
                                # first test
                                i = 0
                                # the 3 following lines make sure the whole available space is being filled
                                # by counting the borders as walls
                                for neighbour in Converter.ctoc(self.unit,*cell):
                                        if neighbour not in self.border :
                                                i += 1
                                if len(Converter.ctow(self.unit,*cell)&allwalls)+i >= 4 :
                                        return True

                                # second test
                                for neighbour in Converter.ctoc(self.unit,*cell):
                                        if neighbour not in self.pos_tracker and neighbour in self.border :
                                                self._done = set()
                                                if not self.find_out(cell):
                                                        return True

                return False

        def find_out(self,cell, _limits=None):
                """Try to find a path to the void, running recursively ;
                If returns False, there is no path ; If returns True, one has been found"""
                # how far did we build yet ?
                if _limits is None :
                        xm,xM,ym,yM = 0,0,0,0
                        for x,y in self.pos_tracker :
                                if x < xm :
                                        xm = x
                                elif x > xM :
                                        xM = x
                                if y < ym :
                                        ym = y
                                elif y > yM :
                                        yM = y
                        built = Area((xm,ym),(xM,yM))
                else :
                        built = _limits

                for c in Converter.ctoc(self.unit, *cell) :
                        if c in self.pos_tracker or c in self._done : # no way / way already processed
                                continue
                        elif c not in built : # void reached
                                return True
                        else :
                                # spreading over
                                self._done.add(c)
                                if self.find_out(c,built) :
                                        return True
                return False


if __name__ == '__main__':
        # we make an example
        main = turtle.TK.Tk()
        can = turtle.ScrolledCanvas(main)
        can.pack(fill="both",expand=True)
        sc = turtle.TurtleScreen(can)
        sc.tracer(n=120)# this line is MAGIC !!!!
        out = open("out.txt","wt")
        laby = Laby(sc,unit=40,border=Area((100,100),(-100,-100)),from_file=open("/home/aveheuzed/out2.txt"), to_file=out)
        # _ = clock()
        for loop in laby :
                pass
        # print(clock()-_)
        out.close()
        sc.update()
        main.mainloop()
