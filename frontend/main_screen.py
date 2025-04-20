# frontend/main_screen.py
import flet as ft
import httpx


def login_page(page: ft.Page, on_success, on_register):
    username_field = ft.TextField(label="아이디", autofocus=True)
    password_field = ft.TextField(label="비밀번호", password=True)

    async def login():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://43.201.53.230:5050/auth/login",
                    json={
                        "username": username_field.value,
                        "password": password_field.value
                    },
                    timeout=10.0
                )
                if response.status_code == 200:
                    token = response.json().get("access_token")
                    on_success(token, username_field.value)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("로그인 실패: 아이디 또는 비밀번호를 확인하세요."))
                    page.snack_bar.open = True
                    page.update()
            except httpx.RequestError as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"서버 오류: {str(ex)}"))
                page.snack_bar.open = True
                page.update()

    def login_button_click(e):
        page.run_task(login)

    def register_button_click(e):
        on_register()

    page.controls.clear()
    page.add(
        ft.Column(
            [
                ft.Text("로그인", style="headlineMedium"),
                username_field,
                password_field,
                ft.ElevatedButton("로그인", on_click=login_button_click),
                ft.TextButton("회원가입", on_click=register_button_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )
    page.update()
