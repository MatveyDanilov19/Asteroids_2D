"""Главный модуль запуска и игрового цикла Астероиды 2D."""

from dataclasses import dataclass, field
import math
import random
import pygame

if __package__:
    from .entities import (
        Ball,
        Bullet,
        Ship,
        check_circle_collision,
        resolve_elastic_collision,
    )
    from .gui import get_simulation_params
    from .tree import Quadtree, Rectangle
else:
    from entities import (
        Ball,
        Bullet,
        Ship,
        check_circle_collision,
        resolve_elastic_collision,
    )
    from gui import get_simulation_params
    from tree import Quadtree, Rectangle


def create_asteroids(params: dict, ship: Ship) -> list[Ball]:
    """Генерирует астероиды на безопасном расстоянии от корабля в центре."""
    balls = []
    width, height = params["width"], params["height"]
    safe_zone = 110.0

    for _ in range(params["count"]):
        radius = random.uniform(params["min_r"], params["max_r"])
        x, y = _find_safe_coords(width, height, radius, ship, safe_zone)

        speed = random.uniform(params["min_v"], params["max_v"])
        angle = random.uniform(0, 2 * math.pi)
        vx = speed * math.cos(angle)
        vy = speed * math.sin(angle)

        color = (
            random.randint(110, 220),
            random.randint(110, 220),
            random.randint(120, 230),
        )
        balls.append(Ball((x, y), radius, (vx, vy), color))

    return balls


def _find_safe_coords(
    width: int, height: int, radius: float, ship: Ship, safe_zone: float
) -> tuple[float, float]:
    """Подбирает координаты спавна астероида вне зоны безопасности корабля."""
    x, y = radius + 5.0, radius + 5.0
    for _ in range(50):
        x = random.uniform(radius + 5, width - radius - 5)
        y = random.uniform(radius + 5, height - radius - 5)
        if math.hypot(x - ship.x, y - ship.y) > safe_zone + radius:
            break
    return x, y


@dataclass
class GameState:
    """Хранит текущее состояние игровой сессии."""

    ship: Ship
    balls: list[Ball] = field(default_factory=list)
    bullets: list[Bullet] = field(default_factory=list)
    score: int = 0
    game_over: bool = False
    show_tree: bool = True
    running: bool = True


class GameEngine:
    """Управляет состоянием, физикой и отрисовкой игры Астероиды 2D."""

    def __init__(self, params: dict):
        """Инициализирует окно Pygame, шрифты и игровые объекты."""
        self.params = params
        pygame.init()
        self.screen = pygame.display.set_mode(
            (params["width"], params["height"])
        )
        pygame.display.set_caption("Астероиды 2D (Квадродерево)")
        self.clock = pygame.time.Clock()

        self.fonts = {
            "hud": pygame.font.SysFont("Arial", 20, bold=True),
            "big": pygame.font.SysFont("Arial", 44, bold=True),
        }

        root_bound = Rectangle(
            params["width"] / 2.0,
            params["height"] / 2.0,
            params["width"] / 2.0,
            params["height"] / 2.0,
        )
        self.quadtree = Quadtree(root_bound, capacity=4)
        self.state = GameState(
            ship=Ship(params["width"] / 2.0, params["height"] / 2.0)
        )
        self.reset()

    def reset(self) -> None:
        """Сбрасывает игровую сессию в начальное состояние."""
        ship = Ship(self.params["width"] / 2.0, self.params["height"] / 2.0)
        self.state = GameState(
            ship=ship,
            balls=create_asteroids(self.params, ship),
            show_tree=self.state.show_tree,
        )

    def handle_events(self) -> None:
        """Обрабатывает нажатия клавиш и закрытие окна."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        """Обрабатывает одиночные нажатия клавиш."""
        if key == pygame.K_ESCAPE:
            self.state.running = False
        elif key == pygame.K_t:
            self.state.show_tree = not self.state.show_tree
        elif key == pygame.K_SPACE and not self.state.game_over:
            self.state.bullets.append(self.state.ship.shoot())
        elif key == pygame.K_r and (
            self.state.game_over or not self.state.balls
        ):
            self.reset()

    def update(self, dt: float) -> None:
        """Обновляет позиции объектов и проверяет все типы столкновений."""
        if self.state.game_over or not self.state.balls:
            return

        width, height = self.params["width"], self.params["height"]
        keys = pygame.key.get_pressed()
        self.state.ship.update(dt, keys, width, height)

        for ball in self.state.balls:
            ball.move(dt)
            ball.handle_wall_collision(width, height)

        for bullet in self.state.bullets:
            bullet.update(dt)
        self.state.bullets = [
            b for b in self.state.bullets if b.is_alive(width, height)
        ]

        self.quadtree.clear()
        for ball in self.state.balls:
            self.quadtree.insert(ball)

        self._resolve_asteroid_collisions()
        self._resolve_bullet_hits()
        self._resolve_ship_collision()

    def _resolve_asteroid_collisions(self) -> None:
        """Обрабатывает упругие столкновения астероидов через квадродерево."""
        checked_pairs = set()
        for ball in self.state.balls:
            area = Rectangle(ball.x, ball.y, ball.radius * 2, ball.radius * 2)
            for other in self.quadtree.query(area):
                if ball is other:
                    continue
                pair = (min(id(ball), id(other)), max(id(ball), id(other)))
                if pair not in checked_pairs:
                    checked_pairs.add(pair)
                    resolve_elastic_collision(ball, other)

    def _resolve_bullet_hits(self) -> None:
        """Проверяет попадания снарядов в астероиды через квадродерево."""
        destroyed = set()
        used_bullets = set()
        fragments = []
        min_split_r = max(self.params["min_r"] * 1.4, 11.0)
        max_r = self.params["max_r"]

        for bullet in self.state.bullets:
            area = Rectangle(
                bullet.x,
                bullet.y,
                bullet.radius + max_r,
                bullet.radius + max_r,
            )
            hit_ball = self._find_hit_asteroid(bullet, area, destroyed)
            if hit_ball is not None:
                destroyed.add(hit_ball)
                used_bullets.add(bullet)
                self.state.score += int(100 / max(hit_ball.radius, 1) * 10)
                fragments.extend(hit_ball.split(min_split_r))

        if destroyed:
            self.state.balls = [
                b for b in self.state.balls if b not in destroyed
            ] + fragments
        if used_bullets:
            self.state.bullets = [
                b for b in self.state.bullets if b not in used_bullets
            ]

    def _find_hit_asteroid(
        self, bullet: Bullet, area: Rectangle, destroyed: set
    ) -> Ball | None:
        """Возвращает первый астероид, в который попал снаряд, или None."""
        for ball in self.quadtree.query(area):
            if ball in destroyed:
                continue
            if check_circle_collision(
                (bullet.x, bullet.y, bullet.radius),
                (ball.x, ball.y, ball.radius),
            ):
                return ball
        return None

    def _resolve_ship_collision(self) -> None:
        """Проверяет столкновение корабля с астероидами через квадродерево."""
        ship = self.state.ship
        if ship.invulnerable_timer > 0:
            return

        max_r = self.params["max_r"]
        ship_area = Rectangle(
            ship.x, ship.y, ship.radius + max_r, ship.radius + max_r
        )
        for ball in self.quadtree.query(ship_area):
            if check_circle_collision(
                (ship.x, ship.y, ship.radius * 0.85),
                (ball.x, ball.y, ball.radius),
            ):
                ship.lives -= 1
                if ship.lives <= 0:
                    self.state.game_over = True
                else:
                    ship.reset_position()
                break

    def draw(self) -> None:
        """Отрисовывает кадр игры, сетку квадродерева и интерфейс."""
        self.screen.fill((14, 16, 22))
        if self.state.show_tree:
            self.quadtree.draw(self.screen)

        for ball in self.state.balls:
            ball.draw(self.screen)
        for bullet in self.state.bullets:
            bullet.draw(self.screen)
        if not self.state.game_over:
            self.state.ship.draw(self.screen)

        self._draw_hud()

        if self.state.game_over:
            self._draw_end_overlay("ИГРА ОКОНЧЕНА", (255, 80, 80))
        elif not self.state.balls:
            self._draw_end_overlay("ПОБЕДА! ПОЛЕ ОЧИЩЕНО", (80, 230, 120))

        pygame.display.flip()

    def _draw_hud(self) -> None:
        """Отрисовывает жизни, текущий счет и подсказки управления."""
        hud_font = self.fonts["hud"]
        lives_str = f"Жизни: {'♥ ' * self.state.ship.lives}"
        score_str = (
            f"Очки: {self.state.score} | Астероидов: {len(self.state.balls)}"
        )
        ctrl_str = "[W/A/D] — полёт | [Пробел] — огонь | [T] — сетка"

        self.screen.blit(
            hud_font.render(lives_str, True, (255, 90, 90)), (15, 12)
        )
        self.screen.blit(
            hud_font.render(score_str, True, (240, 240, 240)), (15, 40)
        )
        self.screen.blit(
            hud_font.render(ctrl_str, True, (140, 150, 165)),
            (15, self.params["height"] - 28),
        )

    def _draw_end_overlay(self, title: str, color: tuple) -> None:
        """Отрисовывает затемненный экран завершения игры."""
        width, height = self.params["width"], self.params["height"]
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))

        cx, cy = width // 2, height // 2
        hud_font = self.fonts["hud"]
        t1 = self.fonts["big"].render(title, True, color)
        t2 = hud_font.render(
            f"Ваш счет: {self.state.score}", True, (255, 255, 255)
        )
        t3 = hud_font.render(
            "Нажмите [R] для новой игры или [ESC] для выхода",
            True,
            (190, 190, 190),
        )

        self.screen.blit(t1, t1.get_rect(center=(cx, cy - 45)))
        self.screen.blit(t2, t2.get_rect(center=(cx, cy + 5)))
        self.screen.blit(t3, t3.get_rect(center=(cx, cy + 45)))

    def run(self) -> None:
        """Запускает главный игровой цикл."""
        while self.state.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()


def main() -> None:
    """Точка входа для запуска приложения."""
    params = get_simulation_params()
    if params:
        engine = GameEngine(params)
        engine.run()


if __name__ == "__main__":
    main()
