import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from scipy import constants
from mpl_toolkits.mplot3d import Axes3D
from sympy import *
import re
import os


class FazePortrait2D:
    def __init__(self, variant, b, c):
        self.variant = variant
        self.m = 0.2*self.variant
        self.l = 5/self.variant
        self.b = 0.1 + 0.015*self.variant
        self.g = constants.g
        self.args = (b, c)
        self.x_stroke = 'x'
        self.y_stroke = 'y'
        self.deltaX = 1
        self.deltaDX = 1
        self.startX = 0
        self.stopX = 5
        self.startDX = 0
        self.stopDX = 0
        self.ts = 10
        self.nt = 101
        self.dead_zone_width = 0.2*self.variant+0.2

    def ode(self, Y, t, b, c):
        def dead_zone_scalar(x, width=self.dead_zone_width):
            if np.abs(x) < width:
                return 0
            elif x > 0:
                return x - width
            else:
                return x + width

        def replace_and_eval(line):
            x = x_destructed
            y = y_destructed

            dead_zone = np.vectorize(dead_zone_scalar, otypes=[
                np.float64], excluded=['width'])

            mu = variant = self.variant
            m = self.m
            l = self.l
            b = self.b
            g = self.g

            return eval(line)

        x_destructed, y_destructed = Y

        dydt = [replace_and_eval(self.x_stroke),
                replace_and_eval(self.y_stroke)]
        return dydt

    def calcODE(self, y0, dy0):
        y0 = [y0, dy0]
        t = np.linspace(0, self.ts, self.nt)
        sol = odeint(self.ode, y0, t, self.args)
        return sol

    def draw(self, name, extra_dot=None):
        figure = plt.figure(name)
        ax = figure.add_subplot()

        for y0 in np.arange(self.startX, self.stopX, self.deltaX):
            for dy0 in np.arange(self.startDX, self.stopDX, self.deltaDX):
                sol = self.calcODE(y0, dy0)
                ax.plot(sol[:, 0], sol[:, 1], 'b')

        if (extra_dot is not None):
            circle = plt.Circle(
                extra_dot['dot'], extra_dot['radial'], color='r')

            ax.add_patch(circle)

        plt.xlabel('x')
        plt.ylabel('dx/dt')
        plt.grid()

        Utility.saveFile(figure, name)

    def changeParams(self, params):
        for key in params:
            self.__dict__[key] = params[key]

    def linearize(self):
        for stroke in {'x_stroke', 'y_stroke'}:
            self.__dict__[stroke] = re.sub(
                r'(\*[xy]){2,}', '*0', self.__dict__[stroke])

    def getAllDots(self, params):
        x_stroke = params['x_stroke'].replace(
            'variant', str(self.variant))
        y_stroke = params['y_stroke'].replace(
            'variant', str(self.variant))

        sympy_eq_x = sympify("Eq(" + x_stroke + ", 0)")
        sympy_eq_y = sympify("Eq(" + y_stroke + ", 0)")

        x, y = symbols('x,y')

        sol = solve([sympy_eq_x, sympy_eq_y], [x, y])
        soln = [tuple(v.evalf() for v in s if v.is_real) for s in sol]

        dots = [value for value in soln if value]
        dots.remove((0, 0))

        return dots

    def shiftParams(self, dot, params):
        dimension_list = {0: 'X',  1: 'DX'}
        shift_list = ('start', 'stop')

        for shift in shift_list:
            for dimension in dimension_list:
                params[shift+dimension_list[dimension]] = params[shift +
                                                                 dimension_list[dimension]] + dot[dimension]

        return params


class FazePortrait3D(FazePortrait2D):
    def __init__(self, sigma, r, b):
        self.sigma = sigma
        self.r = r
        self.b = b
        self.args = (sigma, r, b)
        self.x_stroke = 'sigma*(y-x)'
        self.y_stroke = 'x*(r-z)-y'
        self.z_stroke = 'x*y-b*z'
        self.deltaX = 4
        self.deltaY = 4
        self.deltaZ = 4
        self.startX = -10
        self.stopX = 10
        self.startY = -10
        self.stopY = 10
        self.startZ = -10
        self.stopZ = 10
        self.ts = 10
        self.nt = 1001

    def ode(self, Y, t, _sigma, _r, _b):
        def replace_and_eval(line):
            x = x_destructed
            y = y_destructed
            z = z_destructed

            sigma = _sigma
            r = _r
            b = _b

            return eval(line)

        x_destructed, y_destructed, z_destructed = Y

        dxdt = replace_and_eval(self.x_stroke)
        dydt = replace_and_eval(self.y_stroke)
        dzdt = replace_and_eval(self.z_stroke)

        return [dxdt, dydt, dzdt]

    def calcODE(self, x, y, z):
        y0 = [x, y, z]
        t = np.linspace(0, self.ts, self.nt)
        sol = odeint(self.ode, y0, t, self.args)
        return sol

    def draw(self, name):
        figure = plt.figure(name)
        spacing = 0.5
        plt.subplots_adjust(hspace=spacing, wspace=spacing)

        self.args = (self.sigma, self.r, eval(self.b))

        ax = figure.add_subplot(2, 2, 1, projection='3d')
        ax.set_title("3D")
        plt.subplot(2, 2, 2)
        plt.title("X-Y")
        plt.grid()
        plt.subplot(2, 2, 3)
        plt.title("X-Z")
        plt.grid()
        plt.subplot(2, 2, 4)
        plt.title("Y-Z")
        plt.grid()

        for x in range(self.startX, self.stopX, self.deltaX):
            for y in range(self.startY, self.stopY, self.deltaY):
                for z in range(self.startZ, self.stopZ, self.deltaZ):
                    sol = self.calcODE(x, y, z)

                    ax.plot(sol[:, 0], sol[:, 1], sol[:, 2])
                    plt.subplot(2, 2, 2)
                    plt.plot(sol[:, 0], sol[:, 1])
                    plt.subplot(2, 2, 3)
                    plt.plot(sol[:, 0], sol[:, 2])
                    plt.subplot(2, 2, 4)
                    plt.plot(sol[:, 1], sol[:, 2])

        Utility.saveFile(figure, name)

    def changeParams(self, params):
        for key in params:
            self.__dict__[key] = params[key]


class Utility:
    def __init__(self):
        self = self

    def renameImage(name):
        return '-'.join(name.split())

    def saveFile(figure, figure_name):
        path = './LaTeX/body/images/' + \
            Utility.renameImage(figure_name) + '.png'

        if(os.path.isfile(path)):
            os.remove(path)

        figure.savefig(path)

    def star_replacer(mu):
        return re.sub(r'\*', '', mu)
