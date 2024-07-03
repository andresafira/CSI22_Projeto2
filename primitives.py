##!/usr/bin/env python3

import math


class GameObject:
    def __init__(self, game):
        self.game = game

    def update(self, dt, events):
        raise NotImplementedError()

    def draw(self, surf, offset=(0, 0)):
        raise NotImplementedError()


class Pose:
    @staticmethod
    def polar(r: float, theta_degree: float, angle: float = 0):
        """Initialize a Pose object using polar coordinates as reference"""
        theta = theta_degree * math.pi / 180
        x = r*math.cos(theta)
        y = -r*math.sin(theta)
        return Pose((x, y), angle)

    def __init__(self, position: tuple[float, float], angle:float = 0):
        """ Initialize the Pose.
            position: two-length tuple (x, y)
            angle: angle, in degrees counterclockwise from right
        """
        self.x: float = 0.0
        self.y: float = 0.0
        self.set_position(position)
        self.angle: float = angle

    def set_x(self, new_x: float):
        self.x = new_x

    def set_y(self, new_y: float):
        self.y = new_y

    def set_position(self, position: tuple[float, float]):
        self.x, self.y = position

    def set_angle(self, angle: float):
        self.angle = angle

    def get_position(self) -> tuple[float, float]:
        return self.x, self.y

    def get_angle_of_position(self) -> float:
        return math.atan2(-self.y, self.x)

    def get_angle_of_position_degrees(self) -> float:
        return math.atan2(-self.y, self.x)*180/math.pi

    def get_angle_radians(self) -> float:
        return self.angle*math.pi/180

    def get_unit_vector(self) -> tuple[float, float]:
        """ Return the unit vector equivalent of the Pose's angle
        ## Note: y component is inverted because of indexing on displays;
        ##       negative y points up, while positive y points down."""
        unit_x = math.cos(self.get_angle_radians())
        unit_y = -math.sin(self.get_angle_radians())
        return unit_x, unit_y

    def get_weighted_position(self, weight: float) -> tuple[float, float]:
        return self.x*weight, self.y*weight

    def add_position(self, position: tuple[float, float]):
        add_x, add_y = position
        self.set_x(self.x + add_x)
        self.set_y(self.y + add_y)

    def add_angle(self, angle: float):
        self.set_angle(self.angle + angle)

    def rotate_position(self, angle: float):
        x = self.x*math.cos(angle*math.pi/180) \
            + self.y*math.sin(angle*math.pi/180)
        y = -self.x*math.sin(angle*math.pi/180) \
            + self.y*math.cos(angle*math.pi/180)
        self.set_position((x, y))

    def add_pose(self, other, weight:float =1, frame=None):
        if frame:
            other = other.copy()
            other.rotate_position(frame.angle)
        self.add_position(other.get_weighted_position(weight))
        self.add_angle(other.angle*weight)

    def distance_to(self, other) -> float:
        return (self - other).magnitude()

    def magnitude(self) -> float:
        distance = math.sqrt(self.x*self.x + self.y*self.y)
        return distance

    def clear(self):
        self.x = 0
        self.y = 0
        self.angle = 0

    def copy(self):
        return Pose(self.get_position(), self.angle)

    def scale_to(self, magnitude: float):
        """ Scale the X and Y components of the Pose to have a particular
            magnitude. Angle is unchanged.
        """
        my_magnitude = self.magnitude()
        if my_magnitude == 0:
            self.x = magnitude
            self.y = 0
            return
        self.x *= magnitude / my_magnitude
        self.y *= magnitude / my_magnitude

    def __add__(self, other):
        copy = self.copy()
        copy.add_pose(other)
        return copy

    def __sub__(self, other):
        copy = self.copy()
        copy.add_pose(other, weight=-1)
        return copy

    def __mul__(self, other):
        copy = self.copy()
        copy.x *= other
        copy.y *= other
        copy.angle *= other
        return copy

    def __pow__(self, other):
        copy = self.copy()
        if copy.x >= 0:
            copy.x = copy.x ** other
        else:
            copy.x = (abs(copy.x) ** other) * -1
        if copy.y >= 0:
            copy.y = copy.y ** other
        else:
            copy.y = (abs(copy.y) ** other) * -1
        return copy

    def __str__(self):
        return f"<Pose x:{self.x} y:{self.y} angle:{self.angle}>"

    def __repr__(self):
        return self.__str__()


class PhysicsObject(GameObject):
    def __init__(self, game, position, angle):
        super().__init__(game)
        self.pose = Pose(position, angle)
        self.velocity = Pose(position=(0, 0), angle=0)
        self.acceleration = Pose(position=(0, 0), angle=0)

    def update(self, dt, events):
        self.velocity.add_pose(self.acceleration, weight=dt)
        self.pose.add_pose(self.velocity, weight=dt)
