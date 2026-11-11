"""TOÀN TRUNG Flet app entry point. Run: python main.py"""
import flet as ft
from app.bootstrap import main, _handle_logout, _toggle_theme

__all__ = ["main", "_handle_logout", "_toggle_theme"]

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
