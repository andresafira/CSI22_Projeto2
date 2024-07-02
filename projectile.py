from primitives import Pose
import pygame
import math
import random
import constants as c

from pyracy.sprite_tools import Sprite, Animation
from particle import Puff, SparkParticle, Casing


class Projectile:

    surf_cache = {}

    def __init__(self, position, velocity):
        self.position = Pose(position)
        self.velocity = Pose(velocity)
        self.destroyed = False
        self.age = 0
        self.radius = 10
        self.damage = 60
        self.slowdown = 1.0
        self.z = 0

    def update(self, dt, events):
        self.position += self.velocity * dt
        self.age += dt

    def draw(self, surface, offset=(0, 0)):
        pass

    @classmethod
    def load_surf(cls, path):
        if not path in cls.surf_cache:
            cls.surf_cache[path] = pygame.image.load(path)
        return cls.surf_cache[path]

    def on_impact(self):
        pass

    def hit(self, enemy):
        self.destroyed = True


class PistolBullet(Projectile):

    def __init__(self, position, direction, frame):
        self.frame = frame
        self.pose_adjustment = 0.25
        self.player_adjustment = 0.75
        self.random_angle_factor = math.pi/15
        self.angle_constant = math.pi/30
        self.sheet_size = (3, 1)
        self.number_of_frames = 3
        self.sprite_fps = 12
        self.position_limit = 2000
        self.velocity_decay_factor = 0.1
        self.particles_number = 12

        super().__init__(position, direction)

        casing_position = Pose(position) * self.pose_adjustment + self.frame.player.position * self.player_adjustment
        self.frame.particles.append(Casing(casing_position.get_position()))

        if self.velocity.magnitude() == 0:
            self.velocity = Pose((1, 0))
        angle = self.velocity.get_angle_of_position()
        angle += random.random() * self.random_angle_factor - self.angle_constant
        self.velocity = Pose((math.cos(angle), -math.sin(angle)))
        self.velocity.scale_to(4000)
        self.surf = self.load_surf("assets/images/bullet.png")
        anim = Animation(self.surf, self.sheet_size, self.number_of_frames)
        self.sprite = Sprite(self.sprite_fps, self.position.get_position())
        self.sprite.add_animation({"Bullet": anim}, loop=True)
        self.sprite.start_animation("Bullet")
        angle = self.velocity.get_angle_of_position_degrees()
        self.sprite.set_angle(angle)
        self.radius = 25
        self.damage = 60

    def draw(self, surface, offset=(0, 0)):
        x = self.position.x
        y = self.position.y
        self.sprite.set_position((x, y))
        self.sprite.draw(surface, offset)

    def update(self, dt, events):
        super().update(dt, events)
        self.sprite.update(dt, events)
        if self.position.x < -self.position_limit or self.position.x > c.WINDOW_WIDTH + self.position_limit:
            self.destroyed = True
        if self.position.y < -self.position_limit or self.position.y > c.WINDOW_HEIGHT + self.position_limit:
            self.destroyed = True

    def hit(self, enemy):
        super().hit(enemy)
        for i in range(self.particles_number):
            self.frame.particles.append(SparkParticle(self.position.get_position(), velocity=(self.velocity * -1).get_position(), duration=0.25, color=(255, 255, 255), scale=30))
        enemy.velocity += (self.velocity - enemy.velocity) * self.velocity_decay_factor


class Bread(Projectile):

    def __init__(self, position, direction, frame):
        self.random_angle_factor = math.pi / 15
        self.angle_constant = math.pi / 30
        self.sprite_fps = 12
        self.sheet_size = (7, 1)
        self.number_of_frames = 1
        self.frame = frame
        self.spin_speed_factor = 100
        self.spin_direction_factor = 260
        self.velocity_decay_factor = 0.5
        self.zvel_factor = 1200
        self.updated_angle = -30
        self.max_age = 20
        self.bounce_velocity_factor = 0.8
        self.bounce_zvel = -200
        self.age_limit_for_size = 10
        self.scale_shrink_rate = 5
        self.particles_number = 7

        super().__init__(position, direction)
        if self.velocity.magnitude() == 0:
            self.velocity = Pose((1, 0))
        angle = self.velocity.get_angle_of_position()
        angle += random.random() * self.random_angle_factor - self.angle_constant
        self.velocity = Pose((math.cos(angle), -math.sin(angle)))
        self.velocity.scale_to(600)
        self.surf = self.load_surf("assets/images/bread.png")
        anim = Animation(self.surf, self.sheet_size, self.number_of_frames)
        self.sprite = Sprite(self.sprite_fps, self.position.get_position())
        self.sprite.add_animation({"Bread": anim}, loop=True)
        self.sprite.start_animation("Bread")
        self.angle = self.velocity.get_angle_of_position_degrees()
        if self.velocity.x < 0:
            self.angle += 180
        self.sprite.set_angle(angle)
        self.spin_speed = random.random()*self.spin_speed_factor + self.spin_direction_factor * random.choice([-1, 1])
        self.zvel = -500
        self.z = 0
        self.radius = 25
        self.landed = False
        self.bounced = False
        self.damage = 0

    def update(self, dt, events):
        super().update(dt, events)
        self.angle -= self.spin_speed*dt
        self.sprite.set_angle(self.angle)
        self.sprite.update(dt, events)
        self.velocity *= self.velocity_decay_factor**dt
        self.zvel += self.zvel_factor*dt
        self.z += self.zvel*dt
        if self.z > 0:
            self.z = 0
            if self.velocity.magnitude() > 0:
                self.velocity = Pose((0, 0))
                for i in range(self.particles_number):
                    self.frame.particles.append(Puff((self.position + Pose((0, -20))).get_position()))
                self.landed = True
                random.choice(self.frame.player.breads).play()
            self.spin_speed = 0
            self.angle = self.updated_angle

            if self.age > self.max_age:
                self.destroyed = True

    def bounce(self):
        if self.bounced:
            return
        self.bounced = True
        self.velocity *= -self.bounce_velocity_factor
        self.zvel = self.bounce_zvel
        random.choice(self.frame.player.breads).play()

    def draw(self, surface, offset=(0, 0)):
        img = self.sprite.get_image()
        if self.age > self.age_limit_for_size:
            scale = 1 - ((self.age - self.age_limit_for_size) * self.scale_shrink_rate)
            if scale < 0:
                return
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))

        x = self.position.x - img.get_width()//2 - offset[0]
        y = self.position.y + self.z - img.get_height()//2 - offset[1]
        surface.blit(img, (x, y))

    def hit(self, enemy):
        self.bounce()


class Shuriken(Projectile):

    def __init__(self, position, direction, frame):
        self.frame = frame
        self.sheet_size = (1, 1)
        self.number_of_frames = 1
        self.age_for_velocity_limit = 3
        self.velocity_decay_factor = 0.0001
        self.spin_speed_decay = 0.001
        self.alpha_subtracting_factor = 500
        self.particles_number = 12

        super().__init__(position, direction)
        if self.velocity.magnitude() == 0:
            self.velocity = Pose((1, 0))
        angle = self.velocity.get_angle_of_position()
        self.velocity = Pose((math.cos(angle), -math.sin(angle)))
        self.velocity.scale_to(2000)
        self.surf = self.load_surf("assets/images/shuriken.png")
        anim = Animation(self.surf, self.sheet_size, self.number_of_frames)
        self.sprite = Sprite(12, self.position.get_position())
        self.sprite.add_animation({"Bullet": anim}, loop=True)
        self.sprite.start_animation("Bullet")
        angle = self.velocity.get_angle_of_position_degrees()
        self.sprite.set_angle(angle)
        self.radius = 20
        self.angle = angle
        self.spin_speed = 1000
        self.alpha = 255
        self.slowdown = 0.0
        self.damage = 30

    def draw(self, surface, offset=(0, 0)):
        x = self.position.x
        y = self.position.y
        self.sprite.set_position((x, y))
        self.sprite.draw(surface, offset)

    def update(self, dt, events):
        self.velocity *= self.velocity_decay_factor**dt
        super().update(dt, events)
        self.sprite.update(dt, events)
        self.angle += self.spin_speed*dt
        if self.age > self.age_for_velocity_limit:
            self.spin_speed *= self.spin_speed_decay**dt
            self.alpha -= self.alpha_subtracting_factor*dt
        self.sprite.set_angle(self.angle)
        self.sprite.image.set_alpha(self.alpha)
        if self.alpha < 0:
            self.destroyed = True

    def hit(self, enemy):
        super().hit(enemy)
        for i in range(self.particles_number):
            self.frame.particles.append(SparkParticle(self.position.get_position(), duration=0.25, color=(128, 135, 160), scale=20))