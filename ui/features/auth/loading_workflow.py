"""Brand loading sequence and ERP initialization callbacks (untouched logic)."""
import asyncio
import threading
import time
from typing import Any, Callable, Optional

import flet as ft


from ui.theme.tokens import UIColors

class LoadingWorkflowMixin:
    def start(self):
        """Kích hoạt chuỗi chuyển động và cập nhật tiến trình."""
        threading.Thread(target=self._run_loading_sequence, daemon=True).start()

    def _run_loading_sequence(self):
        # 1. Hiệu ứng xuất hiện mượt mà của Logo
        time.sleep(0.05)
        self.card.opacity = 1.0
        self.card.scale = 1.0
        self.logo_badge.scale = 1.06
        self._safe_update(self.card, self.logo_badge)

        time.sleep(0.2)
        self.logo_badge.scale = 1.0
        self._safe_update(self.logo_badge)

        # 2. Cập nhật tiến trình nạp ngầm
        stages = [0.25, 0.60, 0.85, 1.00]
        current_progress = 0.0
        for target_pct in stages:
            while current_progress < target_pct:
                current_progress = min(target_pct, round(current_progress + 0.05, 2))
                self.progress_bar.value = current_progress
                self.percent_text.value = f"{int(current_progress * 100)}%"
                time.sleep(0.02)
            time.sleep(0.05)

        # 3. Hiệu ứng thở nhẹ của logo khi hoàn tất
        self.logo_badge.scale = 1.04
        self._safe_update(self.logo_badge)
        time.sleep(0.12)

        # 4. Hiệu ứng mờ dần chuyển cảnh (Fade out)
        self.card.opacity = 0.0
        self.card.scale = 1.05
        self._safe_update(self.card)

        time.sleep(0.15)

        # 5. Gọi hàm hoàn tất để mở giao diện chính thông qua Dispatcher của Main Thread
        if self.on_complete:
            loop = getattr(self._app_page, "loop", None)
            if isinstance(loop, asyncio.AbstractEventLoop) and loop.is_running():
                loop.call_soon_threadsafe(self.on_complete)
            else:
                self.on_complete()

    def _safe_update(self, *controls):
        try:
            loop = getattr(self._app_page, "loop", None)
            if isinstance(loop, asyncio.AbstractEventLoop) and loop.is_running():
                if controls:
                    loop.call_soon_threadsafe(self._app_page.update, *controls)
                else:
                    loop.call_soon_threadsafe(self._app_page.update)
            else:
                if controls:
                    self._app_page.update(*controls)
                else:
                    self._app_page.update()
        except Exception:
            pass
