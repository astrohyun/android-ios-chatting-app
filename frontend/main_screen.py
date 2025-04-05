# frontend/main_screen.py
import flet as ft
import requests


def login_page(page: ft.Page, on_success, on_register):
    username_field = ft.TextField(label="아이디", autofocus=True)
    password_field = ft.TextField(label="비밀번호", password=True)

    def login_button_click(e):
        # 로그인 API 호출
        data = {
            "username": username_field.value,
            "password": password_field.value
        }
        response = requests.post("http://127.0.0.1:8003/auth/login", json=data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            # 로그인 성공 시, 아이디를 별칭으로 사용하여 on_success 호출
            on_success(token, username_field.value)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("로그인 실패"))
            page.snack_bar.open = True
            page.update()

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