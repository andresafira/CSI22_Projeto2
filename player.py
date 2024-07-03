from pyracy.sprite_tools import Sprite, Animation
from primitives import Pose
import pygame
import constants as c
import math
from camera import Camera
from particle import Puff, MuzzleFlash, SparkParticle
from projectile import PistolBullet, Bread, Shuriken
import random
from sound_manager import SoundManager
from enemy import Grunt, BossMan, Hand

class Player:
    def __init__(self, frame):
        self.frame = frame
        self.position = c.INITIAL_PLAYER_POSE
        Camera.position = c.INITIAL_CAMERA_POSE
        self.velocity = Pose((0, 0))
        self.sprite = Sprite(12, (0, 0))
        self.hand_sprite = Sprite(12, (0, 0))
        self.populate_hand_sprite(self.hand_sprite)

        self.since_damage = c.SINCE_DAMAGE
        self.dead = False

        self.health = c.INITIAL_HEALTH
        self.max_health = c.MAX_HEALTH

        self.init_sprites()

        self.animation_state = c.IDLE
        self.last_lr_direction = c.RIGHT
        self.rolling = False
        self.firing = False
        self.last_fire = c.LAST_FIRE
        self.weapon_mode = c.GUN
        self.aim_angle = 0
        self.arm_angle = 0
        self.aim_distance = c.INITIAL_AIM_DISTANCE
        self.aim_knockback = 0
        self.knockback_velocity = 0
        self.radius = c.PLAYER_RADIUS
        
        self.init_sound_manager()

        self.shadow = pygame.Surface((self.radius*2, self.radius*2))
        self.shadow.fill((255, 255, 0))
        self.shadow.set_colorkey((255, 255, 0))
        pygame.draw.circle(self.shadow, (0, 0, 0), (self.radius, self.radius), self.radius)
        self.shadow.set_alpha(60)
    
    @staticmethod
    def get_animation(file_name: str, sheet_size: tuple[int, int], frame_count: int,
                      reverse_x: bool = False, start_frame: int = 0) -> Animation:
        path = "assets/images/" + file_name
        animation = Animation.from_path(path, sheet_size=sheet_size,
                                        frame_count=frame_count,
                                        reverse_x=reverse_x)
        return animation

    def init_sprites(self):
        walk_right = Player.get_animation("walk_right.png", (8, 1), 8)
        walk_left = Player.get_animation("walk_right.png", (8, 1), 8, reverse_x=True)
        idle_right = Player.get_animation("forward_idle.png", (8, 1), 8)
        idle_left = Player.get_animation("forward_idle.png", (8, 1), 8, reverse_x=True)
        walk_back_right = Player.get_animation("walk_right_back.png", (8, 1), 8)
        walk_back_left = Player.get_animation("walk_right_back.png", (8, 1), 8, reverse_x=True)
        rolling = Player.get_animation("roll.png", (6, 1), 6)
        dead = Player.get_animation("player death.png", (10, 1), 10)
        take_damage_right = Player.get_animation("player_take_damage.png", (6, 1), 3)
        take_damage_left = Player.get_animation("player_take_damage.png", (6, 1), 3, reverse_x=True)

        self.sprite.add_animation(
            {
                "WalkRight": walk_right,
                "WalkLeft": walk_left,
                "IdleRight": idle_right,
                "IdleLeft": idle_left,
                "WalkBackRight": walk_back_right,
                "WalkBackLeft": walk_back_left,
            },
            loop=True
        )
        self.sprite.add_animation(
            {
                "Dead": dead,
                "TakeDamageRight": take_damage_right,
                "TakeDamageLeft": take_damage_left,
            },
            loop=False
        )

        self.number_surfs = {
            mode: pygame.image.load(f"assets/images/{mode}.png") for mode in c.VALID_MODES
        }

        self.since_roll_finish = c.SINCE_ROLL_FINISH

        self.sprite.add_animation({"Rolling": rolling})
        self.sprite.add_callback("Rolling", self.stop_rolling)
        self.sprite.add_callback("TakeDamageRight", self.stop_taking_damage)
        self.sprite.add_callback("TakeDamageLeft", self.stop_taking_damage)
        self.sprite.start_animation("WalkRight")
        
        self.stamina_sprite = Sprite(16)
        stamina = Player.get_animation("stam wheel.png", (16, 1), 15)
        stamina_idle = Player.get_animation("stam wheel.png", (16, 1), 1)
        self.stamina_sprite.add_animation({"Stamina": stamina, "StaminaIdle": stamina_idle})
        self.stamina_sprite.start_animation("StaminaIdle")
        self.stamina_sprite.add_callback("Stamina", self.hide_stamina)

        self.stamina_visible = False

    def init_sound_manager(self):
        self.death_sound = SoundManager.load("assets/sounds/Player-Death.mp3")
        self.take_damage = SoundManager.load("assets/sounds/Taking-Damage.ogg")
        self.since_kick = 0
        self.roll_sound = SoundManager.load("assets/sounds/die_roll.mp3")

        self.footsteps = [SoundManager.load(f"assets/sounds/Footstep-{rel+1}.mp3") for rel in range(3)]
        self.shots = [SoundManager.load(f"assets/sounds/Gatling-Gun-{rel+1}.mp3") for rel in range(3)]
        self.shurikens = [SoundManager.load(f"assets/sounds/Shuriken-{rel+1}.mp3") for rel in range(3)]
        self.pistols = [SoundManager.load(f"assets/sounds/Pistol_v2.mp3") for rel in range(3)]
        self.flame_bursts = [SoundManager.load(f"assets/sounds/Flame-Burst_v2.ogg") for rel in range(3)]
        self.breads = [SoundManager.load(f"assets/sounds/Bread-{rel+1}.mp3") for rel in range(3)]
        
        for step in self.footsteps:
            step.set_volume(0.1)
        for shot in self.shots:
            shot.set_volume(0.3)
        for shuriken in self.shurikens:
            shuriken.set_volume(0.3)
        for shot in self.pistols:
            shot.set_volume(0.5)
        for shot in self.flame_bursts:
            shot.set_volume(1)
        for shot in self.breads:
            shot.set_volume(0.2)

    def hide_stamina(self):
        self.stamina_visible = False

    def reset_stamina(self):
        self.stamina_visible = True
        self.stamina_sprite.start_animation("Stamina")

    def stop_taking_damage(self):
        self.animation_state = c.IDLE

    def get_hurt(self, direction=None):
        if self.since_damage < 1.25:
            return
        for enemy in self.frame.enemies[:]:
            if not isinstance(enemy, BossMan) and not isinstance(enemy, Hand) and not enemy.lethal and not enemy.destroyed and not self.rolling:
                enemy.lethal = True
                enemy.destroy()
        if direction:
            if not direction.magnitude():
                direction = Pose((1, 0))
            direction.scale_to(1600)
            self.velocity += direction
        self.take_damage.play()
        self.frame.damage_flash_alpha = 255
        self.frame.shake(direction, amt=30)
        self.since_damage = 0
        self.health -= c.HEALTH_LOSS
        self.animation_state = c.TAKING_DAMAGE
        if self.last_lr_direction == c.RIGHT:
            self.sprite.start_animation("TakeDamageRight")
        else:
            self.sprite.start_animation("TakeDamageLeft")

    def update(self, dt, events):
        self.stamina_sprite.update(dt, events)
        self.since_damage += dt
        self.health = min(self.health + 2*dt, self.max_health)

        if self.rolling:
            self.since_roll_finish = 0
        else:
            self.since_roll_finish += dt

        self.last_fire += dt
        self.process_inputs(dt, events)
        self.sprite.set_position(self.position.get_position())
        was_firing = self.firing
        was_rolling = self.rolling
        self.sprite.update(dt, events)
        self.hand_sprite.update(dt, events)
        self.update_hand(dt, events)

        if not self.firing and was_firing:
            self.hand_sprite.update(0, events)
        elif not self.rolling and was_rolling:
            self.hand_sprite.update(0, events)

        mpos = Camera.screen_to_world(pygame.mouse.get_pos())
        Camera.target = self.position.copy() * 0.8 + mpos * 0.2
        if self.animation_state == c.WALKING:
            self.since_kick += dt
        if self.since_kick > 1/3 and self.velocity.magnitude() > 0:
            self.since_kick -= 1 / 3
            for i in range(3):
                start_position = self.position + self.velocity * (1/self.velocity.magnitude()) * 30
                start_position += Pose((random.random() * 10 - 5, random.random() * 10 - 5))
                start_velocity = self.velocity * -0.3
                start_velocity.rotate_position(20 * (i-1))
                self.frame.particles.append(Puff(start_position.get_position(), start_velocity.get_position()))
                random.choice(self.footsteps).play()
        if self.position.x - self.radius < 0:
            self.position.x = self.radius
        if self.position.y - self.radius < 0:
            self.position.y = self.radius
        
        if self.position.x + self.radius > c.ARENA_WIDTH:
            self.position.x = c.ARENA_WIDTH - self.radius
        if self.position.y + self.radius > c.ARENA_HEIGHT:
            self.position.y = c.ARENA_HEIGHT - self.radius

        hurt = False
        for enemy in self.frame.enemies:
            if self.rolling or self.dead:
                continue
            if not enemy.damaging or enemy.lethal or enemy.destroyed:
                continue
            if (enemy.position - self.position).magnitude() < enemy.radius + self.radius:
                self.get_hurt(self.position - enemy.position)
                hurt = True
                break
            if isinstance(enemy, BossMan):
                if enemy.boss_mode == c.BOSS_FIRING_LASER and abs(enemy.position.x - self.position.x) < 40:
                    self.get_hurt(Pose(((self.position - enemy.position).x, 0)))
                    enemy.swoop_above_player()
                    break

        if self.health < 0:
            if not self.dead:
                self.die()

    def die(self):
        self.dead = True
        self.death_sound.play()

    def process_inputs(self, dt, events):
        direction = Pose((0, 0))
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_w]:
            direction += Pose((0, -1))
        if pressed[pygame.K_s]:
            direction += Pose((0, 1))
        if pressed[pygame.K_a]:
            direction += Pose((-1, 0))
        if pressed[pygame.K_d]:
            direction += Pose((1, 0))

        if (self.firing and self.weapon_mode == c.FIRE) or self.dead:
            direction = Pose((0, 0))

        old_state = self.animation_state

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not self.rolling and not self.dead and not self.stamina_visible:
                        self.roll(direction)
                if event.key == pygame.K_r and self.dead:
                    self.frame.restart()
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            if not self.rolling and not self.firing and not self.dead:
                self.fire()

        if self.rolling or self.animation_state == c.TAKING_DAMAGE:
            pass
        else:
            if direction.magnitude() > 0:
                direction.scale_to(1)
                self.velocity += direction * dt * 7500
                self.animation_state = c.WALKING
            elif not self.frame.damage_flash_alpha > 0:
                self.velocity *= 0.0001**dt
            if direction.magnitude() == 0:
                self.animation_state = c.IDLE

            if direction.x > 0:
                self.last_lr_direction = c.RIGHT
            elif direction.x < 0:
                self.last_lr_direction = c.LEFT

        if self.animation_state == c.WALKING:
            clear_time = old_state != c.WALKING
            if clear_time:
                self.since_kick = 0
            animation = "Walk"
            if direction.y < 0:
                animation += "Back"
            if self.last_lr_direction == c.RIGHT:
                animation += "Right"
            else:
                animation += "Left"

            self.sprite.start_animation(animation, restart_if_active=False, clear_time=clear_time)

        elif self.animation_state == c.IDLE:
            if self.dead:
                self.sprite.start_animation("Dead", restart_if_active=False)
            elif self.last_lr_direction == c.RIGHT:
                self.sprite.start_animation("IdleRight", restart_if_active=False, clear_time=False)
            else:
                self.sprite.start_animation("IdleLeft", restart_if_active=False, clear_time=False)
        elif self.animation_state == c.TAKING_DAMAGE:
            if self.last_lr_direction == c.RIGHT:
                self.sprite.start_animation("TakeDamageRight", restart_if_active=False)
            else:
                self.sprite.start_animation("TakeDamageLeft", restart_if_active=False)

        if self.velocity.magnitude() > c.MAX_RUN_SPEED and not self.rolling and not self.frame.damage_flash_alpha > 0:
            self.velocity.scale_to(c.MAX_RUN_SPEED)

        self.position += self.velocity * dt

    def roll(self, direction):
        self.last_fire = c.LAST_FIRE
        self.rolling = True
        self.animation_state = c.ROLLING
        animation = "Rolling"
        self.sprite.start_animation(animation, True, clear_time=True)
        if direction.magnitude() == 0:
            direction.y = 0
            direction.x = 1 if self.last_lr_direction == c.RIGHT else -1
        self.velocity = direction * c.ROLL_MULT_FACTOR
        self.firing = False
        self.roll_sound.play()


    def stop_rolling(self):
        self.rolling = False

        self.reset_stamina()
        self.animation_state = c.IDLE
        self.sprite.start_animation("IdleRight")
        for i in range(20):
            self.frame.particles.append(Puff(self.position.get_position()))
        modes_to_roll = [mode for mode in c.VALID_MODES if mode is not self.weapon_mode]
        if not len(modes_to_roll):
            modes_to_roll = c.VALID_MODES
        self.weapon_mode = random.choice(modes_to_roll)
        self.frame.shake(self.velocity,15)

    def draw(self, surface, offset=(0, 0)):
        if self.since_roll_finish < 0.5 and not self.rolling:
            if self.weapon_mode in self.number_surfs:
                num = self.number_surfs[self.weapon_mode]
                num.set_colorkey((255, 0, 255))
                scale = 1
                alpha = 1
                if self.since_roll_finish < 0.1:
                    scale = 1.5 - self.since_roll_finish*5
                    alpha = self.since_roll_finish*10
                elif self.since_roll_finish > 0.4:
                    scale = 1 - (self.since_roll_finish - 0.4) * 5
                    alpha = 1 - (self.since_roll_finish - 0.4) * 10
                w = int(num.get_width() * scale)
                h = int(num.get_height() * scale)
                num = pygame.transform.scale(num, (w, h))
                x = self.position.x - offset[0] - w//2
                y = self.position.y - offset[1] - h//2 - 90
                num.set_alpha(alpha*255)
                surface.blit(num, (x, y))

        surface.blit(self.shadow, (self.position.x - offset[0] - self.shadow.get_width()//2,
                                   self.position.y - offset[1] - self.shadow.get_height()//2 + 20))
        self.draw_hand(surface, offset, up=True)
        self.sprite.draw(surface, offset)
        self.draw_hand(surface, offset, up=False)

        if self.stamina_visible:
            stamina_offset = Pose((-50, -40))
            self.stamina_sprite.set_position((self.position + stamina_offset).get_position())
            self.stamina_sprite.draw(surface, offset)

    def populate_hand_sprite(self, hand_sprite):
        gun_idle_right = Player.get_animation("gun.png", (4, 1), 1)
        gun_idle_left = Player.get_animation("gun.png", (4, 1), 1, reverse_x=True)
        gun_fire_right = Player.get_animation("gun.png", (4, 1), 4, start_frame=1)
        gun_fire_left = Player.get_animation("gun.png", (4, 1), 4, reverse_x=True, start_frame=1)

        gatling_idle_right = Player.get_animation("gatling_arm.png", (2, 1), 1)
        gatling_idle_left = Player.get_animation("gatling_arm.png", (2, 1), 1, reverse_x=True)
        gatling_fire_right = Player.get_animation("gatling_arm.png", (2, 1), 2)
        gatling_fire_left = Player.get_animation("gatling_arm.png", (2, 1), 2, reverse_x=True)

        bread_idle_right = Player.get_animation("bread_arm.png", (4, 1), 1)
        bread_idle_left = Player.get_animation("bread_arm.png", (4, 1), 1, reverse_x=True)
        bread_fire_right = Player.get_animation("bread_arm.png", (4, 1), 4, start_frame=1)
        bread_fire_left = Player.get_animation("bread_arm.png", (4, 1), 4, reverse_x=True, start_frame=1)

        shuriken_idle_right = Player.get_animation("shuriken_arm.png", (5, 1), 1)
        shuriken_idle_left = Player.get_animation("shuriken_arm.png", (5, 1), 1, reverse_x=True)
        shuriken_fire_right = Player.get_animation("shuriken_arm.png", (5, 1), 4, start_frame=1)
        shuriken_fire_left = Player.get_animation("shuriken_arm.png", (5, 1), 4, reverse_x=True, start_frame=1)

        knife_idle_right = Player.get_animation("knife arm final.png", (6, 1), 1)
        knife_idle_left = Player.get_animation("knife arm final.png", (6, 1), 1, reverse_x=True)
        knife_fire_right = Player.get_animation("knife arm final.png", (6, 1), 6, start_frame=1)
        knife_fire_left = Player.get_animation("knife arm final.png", (6, 1), 6, reverse_x=True, start_frame=1)

        fire_idle_right = Player.get_animation("fire_arm.png", (14, 1), 2)
        fire_idle_left = Player.get_animation("fire_arm.png", (14, 1), 2, reverse_x=True)
        fire_fire_right = Player.get_animation("fire_arm.png", (14, 1), 10, start_frame=0)
        fire_fire_left = Player.get_animation("fire_arm.png", (14, 1), 10, reverse_x=True, start_frame=0)

        hand_sprite.add_animation(
            {
                "GunIdleLeft": gun_idle_left,
                "GunIdleRight": gun_idle_right,
                "BreadIdleRight": bread_idle_right,
                "BreadIdleLeft": bread_idle_left,
                "ShurikenIdleRight": shuriken_idle_right,
                "ShurikenIdleLeft": shuriken_idle_left,
                "FireIdleLeft": fire_idle_left,
                "FireIdleRight": fire_idle_right,
                "GatlingIdleRight": gatling_idle_right,
                "GatlingIdleLeft": gatling_idle_left,
                "KnifeIdleLeft": knife_idle_left,
                "KnifeIdleRight": knife_idle_right,
             },
            loop=True
        )
        hand_sprite.add_animation(
            {
                "GunFireLeft": gun_fire_left,
                "GunFireRight": gun_fire_right,
                "BreadFireRight": bread_fire_right,
                "BreadFireLeft": bread_fire_left,
                "ShurikenFireRight": shuriken_fire_right,
                "ShurikenFireLeft": shuriken_fire_left,
                "FireFireRight": fire_fire_right,
                "FireFireLeft": fire_fire_left,
            },
            loop=False
        )
        hand_sprite.add_animation(
            {
                "GatlingFireRight": gatling_fire_right,
                "GatlingFireLeft": gatling_fire_left,
            },
            fps_override=24,
            loop=True
        )
        hand_sprite.add_animation({"KnifeFireRight": knife_fire_right,
                "KnifeFireLeft": knife_fire_left},
                                  loop=False,
                                  fps_override=24)
        hand_sprite.add_callback("GunFireRight",self.finish_firing)
        hand_sprite.add_callback("GunFireLeft", self.finish_firing)
        hand_sprite.add_callback("BreadFireRight",self.finish_firing)
        hand_sprite.add_callback("BreadFireLeft", self.finish_firing)
        hand_sprite.add_callback("ShurikenFireRight",self.finish_firing)
        hand_sprite.add_callback("ShurikenFireLeft", self.finish_firing)
        hand_sprite.add_callback("FireFireRight", self.finish_firing)
        hand_sprite.add_callback("FireFireLeft", self.finish_firing)
        hand_sprite.add_callback("GatlingFireRight", self.finish_firing)
        hand_sprite.add_callback("GatlingFireLeft", self.finish_firing)
        hand_sprite.add_callback("KnifeFireLeft", self.finish_firing)
        hand_sprite.add_callback("KnifeFireRight", self.finish_firing)
        hand_sprite.start_animation("GunIdleRight")

        self.fire_sprite = Sprite(12)
        fire = Player.get_animation("flame.png", (14, 1), 4)
        fire_vanish = Player.get_animation("flame.png", (14, 1), 14, start_frame=2)
        self.fire_sprite.add_animation({
            "Idle": fire,
            "Vanish": fire_vanish,
        }, loop=False)
        self.fire_sprite.chain_animation("Idle", "Idle")
        self.fire_sprite.start_animation("Idle", restart_if_active=True)

        self.knife_sound = SoundManager.load("assets/sounds/Knife-2.mp3")
        self.knife_sound.set_volume(0.3)

    def update_hand(self, dt, events):
        mpos = pygame.mouse.get_pos()
        aim_position = Camera.screen_to_world(mpos)
        relative = aim_position - self.position
        relative.scale_to(70)

        da = self.aim_angle - relative.get_angle_of_position_degrees()
        target = (sorted([da-360, da, da+360], key=lambda x: abs(x)))[0]
        max_change = abs(target)
        change = target * 25 * dt

        if abs(change) > abs(max_change) and target != 0:
            change *= abs(max_change)/abs(change)
        self.aim_angle -= change

        da = self.arm_angle - relative.get_angle_of_position_degrees()
        target = (sorted([da-360, da, da+360], key=lambda x: abs(x)))[0]
        amt = target * 100
        if abs(amt) > 1000:
            amt *= 1000/abs(amt)
        amt *= dt
        if abs(amt) > abs(target) and target != 0:
            amt *= abs(target)/abs(amt)
        self.arm_angle -= amt

        self.arm_angle %= 360
        self.aim_angle %= 360

        self.aim_knockback += self.knockback_velocity*dt
        if self.knockback_velocity > -500:
            self.knockback_velocity -= 50000*dt
        if self.aim_knockback < 0:
            self.aim_knockback = 0

        if self.weapon_mode == c.FIRE:
            self.fire_sprite.update(dt, events)

        if self.weapon_mode == c.GATLING and not self.rolling:
            if self.velocity.magnitude() > c.MAX_GATLING_SPEED:
                self.velocity.scale_to(c.MAX_GATLING_SPEED)

    def fire(self):
        if self.last_fire < c.COOLDOWNS[self.weapon_mode]:
            return

        self.last_fire = 0
        self.firing = True
        mpos = pygame.mouse.get_pos()
        relative = Camera.screen_to_world(mpos) - self.position

        self.aim_angle = relative.get_angle_of_position_degrees()
        self.aim_knockback = 0
        self.arm_angle = self.aim_angle
        offset = self.position + Pose.polar(self.aim_distance + 28, self.arm_angle)
        knockback = Pose((0, 0))

        if self.weapon_mode == c.GUN:
            self.knockback_velocity = 1500
            if relative.x < 0:
                self.hand_sprite.start_animation("GunFireLeft")
            else:
                self.hand_sprite.start_animation("GunFireRight")
            self.frame.particles.append(MuzzleFlash(offset.get_position(), self.arm_angle))
            self.frame.projectiles.append(PistolBullet(offset.get_position(), relative.get_position(), self.frame))
            random.choice(self.pistols).play()
            knockback = relative * -1
            knockback.scale_to(500)
            self.frame.shake(direction=relative, amt=15)
            for i in range(8):
                self.frame.particles.append(SparkParticle(position=(self.hand_sprite.x, self.hand_sprite.y),
                                                          velocity=relative.get_position(), duration=0.4, scale=20, color=(255, 180, 0)))
        elif self.weapon_mode == c.BREAD:
            self.knockback_velocity = 0
            if relative.x < 0:
                self.hand_sprite.start_animation("BreadFireLeft")
            else:
                self.hand_sprite.start_animation("BreadFireRight")
            self.frame.projectiles.append(Bread(offset.get_position(), relative.get_position(), self.frame))
            random.choice(self.breads).play()
        elif self.weapon_mode == c.GATLING:
            self.knockback_velocity = 200
            if relative.x < 0:
                self.hand_sprite.start_animation("GatlingFireLeft")
            else:
                self.hand_sprite.start_animation("GatlingFireRight")
            if self.velocity.magnitude() > c.MAX_GATLING_SPEED:
                self.velocity.scale_to(c.MAX_GATLING_SPEED)

            muzzle_offset = self.position + Pose.polar(self.aim_distance + 155, self.arm_angle) + Pose((0, 25))
            particle_offset = self.position + Pose.polar(self.aim_distance + 125, self.arm_angle) + Pose((0, 25))
            spark_offset = self.position + Pose.polar(self.aim_distance + 5, self.arm_angle) + Pose((0, 25))
            bullet_offset = self.position + Pose.polar(self.aim_distance + 125, self.arm_angle) + Pose((0, 25)) * 0.5
            
            self.frame.particles.append(MuzzleFlash(muzzle_offset.get_position(), self.arm_angle, duration=0.03))
            bullet = PistolBullet(bullet_offset.get_position(), relative.get_position(), self.frame)
            random.choice(self.shots).play()
            bullet.damage = 40
            self.frame.projectiles.append(bullet)
            knockback = relative * -1
            knockback.scale_to(350)
            self.frame.shake(direction=relative, amt=10)
            for i in range(5):
                self.frame.particles.append(
                    SparkParticle(position=(particle_offset).get_position(), velocity=relative.get_position(),
                                  duration=0.3, scale=25, color=(255, 180, 0)))
                self.frame.particles.append(
                    SparkParticle(position=(spark_offset).get_position(), velocity=relative.get_position(),
                                  duration=0.15, velocity_scale=0.6, scale=20, color=(255, 180, 0)))
        elif self.weapon_mode == c.SHURIKEN:
            self.knockback_velocity = 1500
            if relative.x < 0:
                self.hand_sprite.start_animation("ShurikenFireLeft")
            else:
                self.hand_sprite.start_animation("ShurikenFireRight")
            angle = relative.get_angle_of_position_degrees()
            for angle_offset in [180/math.pi*(-1 + d/2) for d in range(5)]:
                new_angle = angle + angle_offset
                new_relative = Pose.polar(1, new_angle)
                self.frame.projectiles.append(Shuriken(offset.get_position(), new_relative.get_position(), self.frame))
            knockback = relative * -1
            knockback.scale_to(500)
            random.choice(self.shurikens).play()
        elif self.weapon_mode == c.FIRE:
            self.knockback_velocity = 0
            if relative.x < 0:
                self.hand_sprite.start_animation("FireFireLeft")
            else:
                self.hand_sprite.start_animation("FireFireRight")
            self.fire_sprite.start_animation("Vanish")
        elif self.weapon_mode == c.KNIFE:
            self.knockback_velocity = 0
            if relative.x < 0:
                self.hand_sprite.start_animation("KnifeFireLeft")
            else:
                self.hand_sprite.start_animation("KnifeFireRight")
            knife_position = relative.copy()
            knife_position.scale_to(150)
            knife_position += self.position
            for enemy in self.frame.enemies:
                dist = (enemy.position - knife_position).magnitude()
                if dist < enemy.radius + 150:
                    if not enemy.lethal and not enemy.destroyed and not enemy.raised:
                        enemy.take_damage(130)
                        for i in range(16):
                            pos = enemy.position * 0.7 + self.position * 0.3
                            self.frame.particles.append(SparkParticle(pos.get_position(), duration=0.2, color=(255, 255, 255), velocity_scale=1.5))
            self.knife_sound.play()

        self.velocity += knockback

    def finish_firing(self):
        self.firing = False

    def draw_hand(self, surface, offset=(0, 0), up=False):
        if self.rolling or self.dead:
            return
        dist = self.aim_distance - self.aim_knockback
        relative = Pose((math.cos(self.arm_angle*math.pi/180), -math.sin(self.arm_angle * math.pi/180))) * dist
        sprite_angle = self.aim_angle
        if (up and relative.y > 0) or (not up and relative.y <= 0):
            return
        if (relative.x < 0 and "idle" in self.hand_sprite.active_animation_key.lower()) or ("fire" in self.hand_sprite.active_animation_key.lower() and "left" in self.hand_sprite.active_animation_key.lower()):
            sprite_angle += 180
            sprite_angle %= 360

        animation = None
        if not self.firing:
            if self.weapon_mode == c.GUN:
                animation = "GunIdle"
            elif self.weapon_mode == c.GATLING:
                animation = "GatlingIdle"
            elif self.weapon_mode == c.BREAD:
                animation = "BreadIdle"
            elif self.weapon_mode == c.SHURIKEN:
                animation = "ShurikenIdle"
            elif self.weapon_mode == c.FIRE:
                animation = "FireIdle"
                self.fire_sprite.start_animation("Idle", restart_if_active=False)
            elif self.weapon_mode == c.KNIFE:
                animation = "KnifeIdle"
            
        if animation:
            if relative.x < 0:
                animation += "Left"
            else:
                animation += "Right"
            self.hand_sprite.start_animation(animation, restart_if_active=False)
        
        if self.weapon_mode == c.KNIFE:
            relative *= 2
        elif self.weapon_mode == c.GATLING:
            relative *= 1.25


        self.hand_sprite.set_position((self.position + relative).get_position())
        if self.weapon_mode == c.GATLING:
            self.hand_sprite.y += 30

        self.hand_sprite.set_angle(sprite_angle)
        self.hand_sprite.update_image()
        self.hand_sprite.draw(surface, offset)
        if self.weapon_mode == c.FIRE and not (self.last_fire < c.COOLDOWNS[c.FIRE] and not self.firing):
            pos = self.position + relative
            self.fire_sprite.set_position(pos.get_position())
            self.fire_sprite.draw(surface, offset)
