import flet as ft


def main(page: ft.Page):
    page.title = "Todo Demo"
    page.padding = 20

    tasks = ft.Column()
    remaining = ft.Text("Còn 0 việc")

    def update_count(e=None):
        n = sum(1 for c in tasks.controls if not c.value)
        remaining.value = f"Còn {n} việc"
        page.update()

    def add_task(e):
        text = new_task.value.strip()
        if not text:
            return
        tasks.controls.append(ft.Checkbox(label=text, on_change=update_count))
        new_task.value = ""
        update_count()

    new_task = ft.TextField(
        hint_text="Nhập việc cần làm...",
        expand=True,
        on_submit=add_task,
    )

    page.add(
        ft.Row([new_task, ft.IconButton(icon=ft.Icons.ADD, on_click=add_task)]),
        tasks,
        remaining,
    )


ft.run(main)