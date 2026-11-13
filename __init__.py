"""Пакет симуляции столкновений и игры Астероиды 2D на базе квадродерева."""

from .entities import Ball, Bullet, Ship, resolve_elastic_collision
from .gui import get_simulation_params
from .tree import Quadtree, Rectangle

__all__ = [
    "Quadtree",
    "Rectangle",
    "Ball",
    "Bullet",
    "Ship",
    "resolve_elastic_collision",
    "get_simulation_params",
]
