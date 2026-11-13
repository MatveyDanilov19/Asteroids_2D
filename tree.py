"""Модуль реализации квадродерева для пространственного разбиения."""

import pygame


class Rectangle:
    """Прямоугольная область (граница узла квадродерева)."""

    def __init__(self, x: float, y: float, w: float, h: float):
        """Инициализирует прямоугольник по центру (x, y) и полуосям (w, h)."""
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    @property
    def x(self) -> float:
        """Возвращает X-координату центра прямоугольника."""
        return self._x

    @property
    def y(self) -> float:
        """Возвращает Y-координату центра прямоугольника."""
        return self._y

    @property
    def w(self) -> float:
        """Возвращает половину ширины прямоугольника."""
        return self._w

    @property
    def h(self) -> float:
        """Возвращает половину высоты прямоугольника."""
        return self._h

    def intersects_circle(self, cx: float, cy: float, radius: float) -> bool:
        """Проверяет пересечение прямоугольника с окружностью."""
        dx = abs(cx - self._x)
        dy = abs(cy - self._y)

        if dx > (self._w + radius) or dy > (self._h + radius):
            return False
        if dx <= self._w or dy <= self._h:
            return True

        corner_dist_sq = (dx - self._w) ** 2 + (dy - self._h) ** 2
        return corner_dist_sq <= (radius ** 2)

    def intersects_rect(self, other: "Rectangle") -> bool:
        """Проверяет пересечение двух прямоугольников."""
        return (
            abs(self._x - other.x) <= (self._w + other.w)
            and abs(self._y - other.y) <= (self._h + other.h)
        )


class Quadtree:
    """Квадродерево для быстрого поиска столкновений без полного перебора."""

    def __init__(
        self,
        boundary: Rectangle,
        capacity: int = 4,
        depth: int = 0,
        max_depth: int = 8,
    ):
        """Создает узел квадродерева с заданными границами и емкостью."""
        self._boundary = boundary
        self._capacity = capacity
        self._depth = depth
        self._max_depth = max_depth
        self._objects = []
        self._divided = False

        self._northeast = None
        self._northwest = None
        self._southeast = None
        self._southwest = None

    @property
    def boundary(self) -> Rectangle:
        """Возвращает прямоугольную границу текущего узла."""
        return self._boundary

    @property
    def capacity(self) -> int:
        """Возвращает максимальную вместимость узла до разбиения."""
        return self._capacity

    @property
    def depth(self) -> int:
        """Возвращает текущую глубину узла в дереве."""
        return self._depth

    @property
    def is_divided(self) -> bool:
        """Возвращает True, если узел разбит на 4 квадранта."""
        return self._divided

    @property
    def objects(self) -> list:
        """Возвращает копию списка объектов в текущем узле."""
        return list(self._objects)

    @property
    def children(self) -> tuple:
        """Возвращает кортеж дочерних узлов или пустой кортеж."""
        if not self._divided:
            return ()
        return (
            self._northwest,
            self._northeast,
            self._southwest,
            self._southeast,
        )

    def subdivide(self) -> None:
        """Делит текущий узел на 4 дочерних квадранта."""
        x, y = self._boundary.x, self._boundary.y
        w, h = self._boundary.w / 2.0, self._boundary.h / 2.0
        next_d = self._depth + 1
        cap = self._capacity
        max_d = self._max_depth

        self._northeast = Quadtree(
            Rectangle(x + w, y - h, w, h), cap, next_d, max_d
        )
        self._northwest = Quadtree(
            Rectangle(x - w, y - h, w, h), cap, next_d, max_d
        )
        self._southeast = Quadtree(
            Rectangle(x + w, y + h, w, h), cap, next_d, max_d
        )
        self._southwest = Quadtree(
            Rectangle(x - w, y + h, w, h), cap, next_d, max_d
        )
        self._divided = True

        for obj in self._objects:
            self._insert_into_children(obj)
        self._objects.clear()

    def _insert_into_children(self, obj) -> None:
        for child in self.children:
            if child.boundary.intersects_circle(obj.x, obj.y, obj.radius):
                child.insert(obj)

    def insert(self, obj) -> bool:
        """Добавляет объект в квадродерево."""
        if not self._boundary.intersects_circle(obj.x, obj.y, obj.radius):
            return False

        if not self._divided:
            if len(self._objects) < self._capacity or (
                self._depth >= self._max_depth
            ):
                self._objects.append(obj)
                return True
            self.subdivide()

        self._insert_into_children(obj)
        return True

    def query(self, range_rect: Rectangle, found: list = None) -> list:
        """Возвращает список объектов, попадающих в заданную область."""
        if found is None:
            found = []

        if not self._boundary.intersects_rect(range_rect):
            return found

        if self._divided:
            for child in self.children:
                child.query(range_rect, found)
        else:
            for obj in self._objects:
                if obj not in found:
                    found.append(obj)

        return found

    def clear(self) -> None:
        """Очищает дерево и удаляет дочерние узлы."""
        self._objects.clear()
        self._divided = False
        self._northeast = None
        self._northwest = None
        self._southeast = None
        self._southwest = None

    def draw(self, surface: pygame.Surface, color=(45, 110, 55)) -> None:
        """Отрисовывает границы узла и всех его потомков."""
        rect = pygame.Rect(
            self._boundary.x - self._boundary.w,
            self._boundary.y - self._boundary.h,
            self._boundary.w * 2,
            self._boundary.h * 2,
        )
        pygame.draw.rect(surface, color, rect, 1)

        if self._divided:
            for child in self.children:
                child.draw(surface, color)
