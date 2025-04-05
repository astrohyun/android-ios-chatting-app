# frontend/main.py
import flet as ft
from main_screen import login_page
from register_screen import register_page
from chat_lobby import chat_lobby

def main(page: ft.Page):
    page.title = "Chat App"

    def go_to_login():
        page.clean()
        login_page(page, on_success=go_to_chat, on_register=go_to_register)
        page.update()

    def go_to_register():
        page.clean()
        register_page(page, on_back=go_to_login)
        page.update()

    def go_to_chat(jwt_token: str, nickname: str):
        page.clean()
        # 모든 사용자는 로그인 후 기본 채널 "default"에 접속
        chat_lobby(page, jwt_token, nickname, channel="default")
        page.update()

    go_to_login()


ft.app(target=main)
