# frontend/register_screen.py
import flet as ft
import httpx


def register_page(page: ft.Page, on_back):
    page.title = "회원가입"

    username_field = ft.TextField(label="아이디", autofocus=True)
    nickname_field = ft.TextField(label="닉네임")
    password_field = ft.TextField(label="비밀번호", password=True)

    async def register():
        data = {
            "username": username_field.value,
            "password": password_field.value,
            "nickname": nickname_field.value,
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post("http://43.203.205.210:5050/auth/register", json=data, timeout=10.0)
                if response.status_code == 200:
                    page.snack_bar = ft.SnackBar(ft.Text("회원가입 성공! 로그인 화면으로 이동합니다."))
                    page.snack_bar.open = True
                    page.update()
                    on_back()
                else:
                    error_detail = response.json().get("detail", "회원가입 실패")
                    page.snack_bar = ft.SnackBar(ft.Text(f"회원가입 실패: {error_detail}"))
                    page.snack_bar.open = True
                    page.update()
            except httpx.RequestError as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"네트워크 오류: {str(ex)}"))
                page.snack_bar.open = True
                page.update()

    def register_button_click(e):
        page.run_task(register)

    def back_button_click(e):
        on_back()

    page.controls.clear()
    page.add(
        ft.Column(
            [
                ft.Text("회원가입", style="headlineMedium"),
                username_field,
                nickname_field,
                password_field,
                ft.ElevatedButton("회원가입", on_click=register_button_click),
                ft.TextButton("뒤로가기", on_click=back_button_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )
    page.update()


# 단독 실행 시 테스트용
if __name__ == "__main__":
    def dummy_on_back():
        print("뒤로가기 호출됨")

    ft.app(target=lambda page: register_page(page, on_back=dummy_on_back))
