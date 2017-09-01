#!/usr/bin/env python3
from misc import PreciseTurtle

class Sprite(PreciseTurtle) :

        def __init__(self,screen,step,forbidden,*args):
                """screen and args are passed to turtle.RawTurtle  constructor.
                Use step (int) to specify how long a step should be (i.e. how much a key-press makes you move)
                Forbidden is a set of (x,y) coordinates that are forbidden to go to.
                """
                super().__init__(screen,*args)
                self.step = step
                self.forbidden = forbidden

                self.up()
                self.st()

        def forward(self):
                #no parameter any more

                # we go forward one step at a time, until we go to a forbidden point
                super().forward(self.step)
                if self.pos() in self.forbidden :
                        self.undo()
