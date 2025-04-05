# frontend/register_screen.py
import flet as ft
import requests


def register_page(page: ft.Page, on_back):
    page.title = "회원가입"

    # 입력 필드 구성
    username_field = ft.TextField(label="아이디", autofocus=True)
    nickname_field = ft.TextField(label="닉네임")  # 기존 백엔드에서는 nickname 사용
    password_field = ft.TextField(label="비밀번호", password=True)

    # 회원가입 버튼 클릭 이벤트 처리
    def register_button_click(e):
        # API로 전달할 데이터 구성
        data = {
            "username": username_field.value,
            "password": password_field.value,
            "nickname": nickname_field.value,
        }
        try:
            response = requests.post("http://127.0.0.1:8003/auth/register", json=data)
            if response.status_code == 200:
                page.snack_bar = ft.SnackBar(ft.Text("회원가입 성공! 로그인 화면으로 이동합니다."))
                page.snack_bar.open = True
                page.update()
                on_back()  # 로그인 화면으로 돌아가기
            else:
                error_detail = response.json().get("detail", "회원가입 실패")
                page.snack_bar = ft.SnackBar(ft.Text(f"회원가입 실패: {error_detail}"))
                page.snack_bar.open = True
                page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"에러 발생: {str(ex)}"))
            page.snack_bar.open = True
            page.update()

    # 뒤로가기 버튼 클릭 시 로그인 화면으로 돌아감
    def back_button_click(e):
        on_back()

    # 화면 구성
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


# 단독 실행 시 테스트용 (on_back 콜백은 페이지를 닫는 식으로 처리)
if __name__ == "__main__":
    def dummy_on_back():
        print("뒤로가기 호출됨")


    ft.app(target=lambda page: register_page(page, on_back=dummy_on_back))
