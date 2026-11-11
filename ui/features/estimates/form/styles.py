"""FormStylesMixin: isolated UI responsibilities; inherited by the screen coordinator.

Preserves original control construction and callbacks for migration safety.
"""
import math
from typing import Any, Callable, Dict, List
import flet as ft


from ui.theme.tokens import UIColors

class FormStylesMixin:
    @classmethod
    def _field_style(cls, suffix_icon=None):
        style = {
            "border": cls._input_border(),
            "bgcolor": ft.Colors.TRANSPARENT,
            "cursor_color": cls.PRIMARY_COLOR,
            "label_style": ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=UIColors.TEXT_SECONDARY),
            "dense": True,
        }
        if suffix_icon:
            style["suffix"] = ft.Icon(suffix_icon, size=16, color=UIColors.TEXT_SECONDARY)
        return style

    @classmethod
    def _read_only_field_style(cls):
        return {
            "border": cls._input_border(UIColors.BORDER),
            "bgcolor": UIColors.SURFACE_SUBTLE,
            "label_style": ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=UIColors.TEXT_SECONDARY),
            "dense": True,
        }

    @classmethod
    def _dropdown_style(cls):
        return {
            "border": cls._input_border(),
            "bgcolor": ft.Colors.WHITE,
            "label_style": ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=UIColors.TEXT_SECONDARY),
            "dense": True,
            "menu_style": ft.MenuStyle(
                bgcolor=ft.Colors.WHITE,
                elevation=6,
                shape=ft.RoundedRectangleBorder(radius=12),
            ),
        }

    @classmethod
    def _input_border(cls, default_color=UIColors.BORDER_STRONG):
        return {
            ft.ControlState.DEFAULT: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(width=1, color=default_color),
            ),
            ft.ControlState.FOCUSED: ft.OutlineInputBorder(
                border_radius=10,
                side=ft.BorderSide(width=1.5, color=cls.PRIMARY_COLOR),
            ),
        }

    @classmethod
    def _primary_button_style(cls):
        return ft.ButtonStyle(
            bgcolor=cls.PRIMARY_COLOR,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.Padding(16, 12, 16, 12),
        )
