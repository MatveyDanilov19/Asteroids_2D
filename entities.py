"""Модуль игровых сущностей (астероиды, корабль, снаряды) и физики ударов."""

import math
import random
import pygame


class Ball:
    """Астероид круглой формы с массой, равной его площади."""

    def __init__(
        self,
        pos: tuple[float, float],
        radius: float,
        vel: tuple[float, float],
        color: tuple[int, int, int],
    ):
        """Инициализирует астероид по позиции pos, радиусу и скорости vel."""
        self.x, self.y = pos
        self._radius = radius
        self.vx, self.vy = vel
        self.color = color
        self._mass = math.pi * (radius ** 2)

    @property
    def radius(self) -> float:
        """Возвращает радиус астероида."""
        return self._radius

    @property
    def mass(self) -> float:
        """Возвращает массу астероида (равную площади круга)."""
        return self._mass

    def move(self, dt: float) -> None:
        """Перемещает астероид за интервал времени dt."""
        self.x += self.vx * dt
        self.y += self.vy * dt

    def handle_wall_collision(self, width: int, height: int) -> None:
        """Выполняет упругое отражение от границ игровой области."""
        if self.x - self._radius < 0:
            self.x = self._radius
            self.vx = -self.vx
        elif self.x + self._radius > width:
            self.x = width - self._radius
            self.vx = -self.vx

        if self.y - self._radius < 0:
            self.y = self._radius
            self.vy = -self.vy
        elif self.y + self._radius > height:
            self.y = height - self._radius
            self.vy = -self.vy

    def split(self, min_split_radius: float = 10.0) -> list["Ball"]:
        """Раскалывает крупный астероид на 2 осколка или уничтожает мелкий."""
        if self._radius < min_split_radius:
            return []

        new_radius = self._radius * 0.6
        fragments = []
        for _ in range(2):
            angle = random.uniform(0, 2 * math.pi)
            speed = math.hypot(self.vx, self.vy) * random.uniform(1.1, 1.35)
            vel = (speed * math.cos(angle), speed * math.sin(angle))
            pos = (
                self.x + math.cos(angle) * new_radius,
                self.y + math.sin(angle) * new_radius,
            )
            fragments.append(Ball(pos, new_radius, vel, self.color))
        return fragments

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает астероид на поверхности."""
        pos = (int(self.x), int(self.y))
        r = int(self._radius)
        pygame.draw.circle(surface, self.color, pos, r)
        pygame.draw.circle(surface, (230, 230, 230), pos, r, 1)


class Bullet:
    """Лазерный снаряд, выпущенный кораблем."""

    def __init__(self, x: float, y: float, angle: float, speed: float = 650.0):
        """Создает снаряд в точке (x, y), летящий под углом angle."""
        self.x = x
        self.y = y
        self.radius = 3.0
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = 1.6

    def update(self, dt: float) -> None:
        """Обновляет положение и оставшееся время жизни снаряда."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt

    def is_alive(self, width: int, height: int) -> bool:
        """Проверяет, находится ли снаряд в пределах экрана и времени жизни."""
        return (
            self.lifetime > 0
            and 0 <= self.x <= width
            and 0 <= self.y <= height
        )

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает снаряд на экране."""
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(surface, (255, 230, 80), pos, int(self.radius))


class Ship:
    """Космический корабль игрока в виде треугольника."""

    def __init__(self, x: float, y: float):
        """Инициализирует корабль в заданной стартовой точке."""
        self.start_pos = (x, y)
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2
        self.radius = 15.0
        self.status = {
            "lives": 3,
            "invuln": 2.0,
            "thrusting": False,
        }

    @property
    def lives(self) -> int:
        """Возвращает текущее количество жизней корабля."""
        return self.status["lives"]

    @lives.setter
    def lives(self, value: int) -> None:
        """Устанавливает количество жизней корабля."""
        self.status["lives"] = value

    @property
    def invulnerable_timer(self) -> float:
        """Возвращает оставшееся время неуязвимости корабля."""
        return self.status["invuln"]

    def reset_position(self) -> None:
        """Возвращает корабль в центр и включает временную неуязвимость."""
        self.x, self.y = self.start_pos
        self.vx = 0.0
        self.vy = 0.0
        self.angle = -math.pi / 2
        self.status["invuln"] = 2.5

    def update(self, dt: float, keys, width: int, height: int) -> None:
        """Обрабатывает управление и физику движения корабля."""
        if self.status["invuln"] > 0:
            self.status["invuln"] -= dt

        rot_speed = 4.5
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= rot_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += rot_speed * dt

        thrusting = bool(keys[pygame.K_UP] or keys[pygame.K_w])
        self.status["thrusting"] = thrusting
        if thrusting:
            accel = 320.0
            self.vx += math.cos(self.angle) * accel * dt
            self.vy += math.sin(self.angle) * accel * dt

        self.vx *= 0.992
        self.vy *= 0.992
        speed = math.hypot(self.vx, self.vy)
        max_speed = 420.0
        if speed > max_speed:
            self.vx = (self.vx / speed) * max_speed
            self.vy = (self.vy / speed) * max_speed

        self.x += self.vx * dt
        self.y += self.vy * dt
        self._clamp_to_bounds(width, height)

    def _clamp_to_bounds(self, width: int, height: int) -> None:
        """Удерживает корабль внутри границ экрана."""
        if self.x < self.radius:
            self.x = self.radius
            self.vx = 0.0
        elif self.x > width - self.radius:
            self.x = width - self.radius
            self.vx = 0.0

        if self.y < self.radius:
            self.y = self.radius
            self.vy = 0.0
        elif self.y > height - self.radius:
            self.y = height - self.radius
            self.vy = 0.0

    def shoot(self) -> Bullet:
        """Создает и возвращает снаряд, выпущенный из носа корабля."""
        nose_x = self.x + math.cos(self.angle) * (self.radius + 4)
        nose_y = self.y + math.sin(self.angle) * (self.radius + 4)
        return Bullet(nose_x, nose_y, self.angle)

    def get_triangle_points(self) -> list[tuple[float, float]]:
        """Вычисляет координаты вершин треугольника корабля."""
        nose = (
            self.x + math.cos(self.angle) * (self.radius + 5),
            self.y + math.sin(self.angle) * (self.radius + 5),
        )
        left_wing = (
            self.x + math.cos(self.angle + 2.45) * self.radius,
            self.y + math.sin(self.angle + 2.45) * self.radius,
        )
        right_wing = (
            self.x + math.cos(self.angle - 2.45) * self.radius,
            self.y + math.sin(self.angle - 2.45) * self.radius,
        )
        return [nose, left_wing, right_wing]

    def draw(self, surface: pygame.Surface) -> None:
        """Отрисовывает треугольник корабля и пламя двигателя."""
        invuln = self.status["invuln"]
        if invuln > 0 and int(invuln * 10) % 2 == 0:
            return

        points = self.get_triangle_points()
        pygame.draw.polygon(surface, (70, 200, 255), points)
        pygame.draw.polygon(surface, (255, 255, 255), points, 2)

        if self.status["thrusting"]:
            flame = (
                self.x - math.cos(self.angle) * (self.radius + 8),
                self.y - math.sin(self.angle) * (self.radius + 8),
            )
            pygame.draw.line(
                surface, (255, 140, 40), (self.x, self.y), flame, 3
            )


def check_circle_collision(
    circle1: tuple[float, float, float],
    circle2: tuple[float, float, float],
) -> bool:
    """Проверяет пересечение двух окружностей вида (x, y, radius)."""
    x1, y1, r1 = circle1
    x2, y2, r2 = circle2
    dx = x2 - x1
    dy = y2 - y1
    return (dx * dx + dy * dy) <= ((r1 + r2) ** 2)


def resolve_elastic_collision(b1: Ball, b2: Ball) -> None:
    """Рассчитывает абсолютно упругое столкновение двух астероидов."""
    dx = b2.x - b1.x
    dy = b2.y - b1.y
    dist_sq = dx * dx + dy * dy
    min_dist = b1.radius + b2.radius

    if dist_sq >= min_dist * min_dist or dist_sq == 0:
        return

    dist = math.sqrt(dist_sq)
    nx = dx / dist
    ny = dy / dist

    overlap = min_dist - dist
    total_mass = b1.mass + b2.mass
    b1.x -= nx * overlap * (b2.mass / total_mass)
    b1.y -= ny * overlap * (b2.mass / total_mass)
    b2.x += nx * overlap * (b1.mass / total_mass)
    b2.y += ny * overlap * (b1.mass / total_mass)

    dvx = b2.vx - b1.vx
    dvy = b2.vy - b1.vy
    vel_along_normal = dvx * nx + dvy * ny

    if vel_along_normal > 0:
        return

    impulse = -(2.0 * vel_along_normal) / (1.0 / b1.mass + 1.0 / b2.mass)
    b1.vx -= (impulse * nx) / b1.mass
    b1.vy -= (impulse * ny) / b1.mass
    b2.vx += (impulse * nx) / b2.mass
    b2.vy += (impulse * ny) / b2.mass
