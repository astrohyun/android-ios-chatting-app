# frontend/chat_lobby.py
import flet as ft
import asyncio
import threading
import httpx
import re
import websockets
import time
from better_profanity import profanity
profanity.load_censor_words()  # 기본 금지어 목록 로드

all_users = []
# 이모티콘 매핑 정의 (필요시 추가 가능)
EMOJI_MAP = {
    ":이모티콘:": "😊",
    ":smile:": "😃",
    ":heart:": "❤️",
    ":thumbsup:": "👍",
    ":fire:": "🔥",
}  #이모티콘 리스트를 추가하거나, 이모티콘 입력 방식을 변경하는것을 생각해 봅시다

def parse_message_text(text: str, all_users):
    controls = []

    # 파일 메시지 정규식: FILE:파일명|URL (타임스탬프)
    file_pattern = re.compile(r"^FILE:(.+?)\|(.+?)$")
    file_match = file_pattern.match(text)

    if file_match:
        file_name, file_url = file_match.groups()   # unpack
        controls.append(
            ft.Row([
                ft.Icon(ft.icons.ATTACH_FILE, size=18, color=ft.colors.BLUE),
                #ft.Text(f"{file_name}", color=ft.colors.BLUE, weight="bold"),
                #ft.TextButton("다운로드", url=file_url)
                ft.TextButton(text=file_name, style=ft.ButtonStyle(color=ft.colors.BLUE), url=file_url),
            ], spacing=5)
        )
        return ft.Column(controls)

    text = profanity.censor(text)

    # ">"로 시작하는 메시지 처리 (말풍선처럼 박스를 그리기)
    if text.startswith("> "):
        quote_text = text[2:].strip()  # ">"와 공백을 제거한 후 메시지
        controls.append(
            ft.Container(
                content=ft.Text(quote_text, italic=True),  # 인용된 메시지 스타일
                bgcolor=ft.colors.BLUE_GREY_900,
                padding=0,
                border_radius=5,
            )
        )
    else:
        words = text.split() #split은? words를 띄어쓰기 = 공백 기준으로 나눈다

        all_users_lower = [user.lower() for user in all_users]  # 🔥 대소문자 변환
        print(f"멘션 체크: all_users = {all_users_lower}")  # ✅ 디버깅 추가

        for word in words:
            print(f"단어 분석: {word}")  # ✅ 디버깅 추가

            # 멘션 처리 (대소문자 무시)
            if word.startswith("@") and word[1:].lower() in all_users_lower:  # 정규표현식으로 바꿔서 처리하면 좋을듯?
                print(f"✅ 멘션 감지: {word}")  # ✅ 디버깅 추가
                controls.append(ft.Text(word, color=ft.colors.BLUE, weight="bold"))
            # 연속된 이모지 처리
            elif re.match(r":\w+:", word):   # re는 무엇일까요?  R.E. - Regular Expression : 정규표현(식)
                emoji_text = re.sub(r":(\w+):", lambda m: EMOJI_MAP.get(m.group(0), m.group(0)), word)
                controls.append(ft.Text(emoji_text, size=20))
            else:
                controls.append(ft.Text(word))

    return ft.Row(spacing=5, controls=controls)

async def chat_lobby(page: ft.Page, jwt_token: str, nickname: str, channel: str = "default", channels_list=None, prev_messages=None): ##3.1.
##3.1.
    async def load_channels():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://43.203.205.210:5050/chat/channels")
                if response.status_code == 200:
                    channels_list = [channel['name'] for channel in response.json()]  # 채널 목록을 받아옴
                    return channels_list
                else:
                    print("채널 목록을 가져오는 데 실패했습니다.")
                    return []
        except Exception as ex:
            print(f"채널 목록 가져오기 실패: {ex}")
            return []

#    if channels_list is None:
#            channels_list = load_channels()

    # 채널 전환 함수: 페이지를 재구성하여 새로운 채널로 접속
    async def close_and_switch(new_channel: str):
        if ws_connection["ws"]:
            try:
                await ws_connection["ws"].close()  # WebSocket 종료를 비동기적으로 기다림
            except Exception as e:
                print(f"WebSocket 종료 중 오류 발생: {e}")

        new_messages = await fetch_messages(new_channel)    ##3.1.

        page.run_task(chat_lobby, page, jwt_token, nickname, channel=new_channel, channels_list=channels_list, prev_messages=new_messages) ##3.1.

    def switch_channel(new_channel: str):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(close_and_switch(new_channel))
        loop.close()

    async def fetch_messages(channel_name):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://43.203.205.210:5050/chat/messages?channel={channel_name}")
                if response.status_code == 200:
                    messages = response.json()
                    return messages
                else:
                    print("메시지 로드 실패")
                    return []
        except Exception as ex:
            print(f"메시지 불러오기 오류: {ex}")
            return []

    ##3.1.
    page.title = "Chat Lobby"
    if channels_list is None:
        channels_list = await load_channels()

    if prev_messages is None:
        prev_messages = []

    current_channel = channel  # 현재 접속 채널


    # addon 2
    is_dark_mode = False

    def toggle_theme(e):
        nonlocal is_dark_mode
        if is_dark_mode:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_switch_button.text = "Switch to dark mode"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_switch_button.text = "Switch to light mode"
        is_dark_mode = not is_dark_mode
        theme_switch_button.update()
        page.update()


    theme_switch_button = ft.ElevatedButton(
        text="Switch to dark mode",
        on_click=toggle_theme
    )

#    try:
#        async with httpx.AsyncClient() as client:
#            response = await client.get("http://43.203.205.210:5050/chat/channels")
#            if response.status_code == 200:
#                channels_list = [channel['name'] for channel in response.json()]  # 채널 목록을 받아옴
#            else:
#                print("채널 목록을 가져오는 데 실패했습니다.")
#    except Exception as ex:
#        print(f"채널 목록 가져오기 실패: {ex}")

    # 1. 헤더에 사용자 정보와 현재 채널 표시
    header = ft.Row(
        [
            ft.Text(f"사용자: {nickname}", weight="bold"),
            ft.Text(f"채널: {current_channel}", color=ft.colors.BLUE, weight="bold"),
            theme_switch_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # 2. 좌측 패널: 채널 목록과 채널 생성 버튼
    channel_list_view = ft.ListView(expand=True, spacing=0, padding=0)  ##3.1.
    for ch1 in channels_list:
        # ListTile을 GestureDetector로 감싸서 on_double_tap 이벤트 처리
        tile = ft.GestureDetector(
            content=ft.ListTile(title=ft.Text(ch1)),
            on_double_tap=lambda e, ch=ch1: switch_channel(ch)
        )
        channel_list_view.controls.append(tile)

    create_channel_button = ft.ElevatedButton("채널 생성", on_click=lambda e: open_create_channel_dialog())

    user_list_view = ft.ListView(expand=True, spacing=5, padding=10)
    left_panel = ft.Column(
        [ft.Text("채널 목록", weight="bold"), channel_list_view, create_channel_button,
         ft.Divider(),
         ft.Text("현재 접속 유저", weight="bold"),
         user_list_view  # 사용자 목록 추가
         ],
        width=160,
    )

    # 3. 중앙 패널: 채팅 메시지 목록 및 메시지 입력창, 전송 버튼    # 메시지 리스트 (이전 메시지 추가)
    messages_list = ft.ListView(expand=True, spacing=10, padding=10)
##JK
    for msg in prev_messages:
        parsed_message = parse_message_text(msg["message"], all_users=all_users)  # 이모티콘 및 멘션 처리 4.5.
        message_display = ft.Row([
            ft.Text(f"{msg['sender']}:", weight="bold"),
            parsed_message,
            ft.Text(f"({msg['timestamp']})", size=10, color=ft.colors.GREY)
        ], spacing=5, alignment=ft.MainAxisAlignment.START)

        messages_list.controls.append(message_display)


    input_field = ft.TextField(expand=True, hint_text="메시지를 입력하세요.")
    send_button = ft.IconButton(
                                    icon=ft.icons.SEND_ROUNDED,
                                    tooltip="Send message",
                                )


    # 파일 업로드 버튼 추가
    def file_select(e):  # e는 object
        selected_file = e.files
        if selected_file:
            file_path = selected_file[0]  ## dialog에서 선택한 첫번째 파일을 처리하겠다는 의미
            # file 정보를 미리 확인할 수 있으니까, multiple upload를 구현하려면
            # file의 정보 중 파일 크기, 종류 등을 확인하고 => 최대용량 제한을 두거나 갯수를 지정하면 됩니다
            # 카카톡에서 한번에 전송 가능한 파일 갯수가 예전에 10개?
            # 한번에 전송 가능한 파일 용량은 얼마 이하입니다 안내해주고 전처리 try: // catch exception:
            page.run_task(upload_file, file_path)

    # 파일 선택기
    file_picker = ft.FilePicker(on_result=file_select)
    # 페이지에 file_picker 추가
    page.overlay.append(file_picker)

    upload_button = ft.IconButton(
                                    icon=ft.icons.IMAGE,
                                    tooltip="Upload image",
                                    on_click=lambda e: file_picker.pick_files(allow_multiple=False),
                                )

    # 파일 업로드 버튼을 메시지 입력창 아래에 추가
    # chat_input_row = ft.Row([input_field, send_button])
    chat_input_row = ft.Row([input_field, send_button, upload_button])

    center_panel = ft.Column([messages_list, chat_input_row], expand=True)

    # 전체 레이아웃 구성 (좌측 패널 + 구분선 + 중앙 패널)
    main_layout = ft.Row([left_panel, ft.VerticalDivider(), center_panel], expand=True)
    page.controls.clear()
    page.add(header, ft.Divider(), main_layout)
    #fetch_messages("default")
    page.update()

    # 4. WebSocket 연결 관련 변수
    ws_connection = {"ws": None, "thread": None}

    # WebSocket 핸들러 (비동기)
    async def ws_handler(): ##3.1.
        global all_users

        ws_url = f"ws://43.203.205.210:5050/ws/chat?channel={current_channel}&token={jwt_token}"
        try:
            async with websockets.connect(ws_url) as websocket:
                ws_connection["ws"] = websocket
                while True:
                    message = await websocket.recv()

                    if message.startswith("USER_LIST:"):
                        user_list = message.replace("USER_LIST:", "").strip()
                        user_list = user_list.split(",") if user_list else []
                        print(f"✅ 사용자 목록 업데이트: {user_list}")

                        all_users.clear()#4.5.
                        all_users.extend(user_list)#4.5.

                        user_list_view.controls.clear()
                        for user in user_list:
                            user_list_view.controls.append(ft.Text(user))
                        page.update()


                    elif "FILE:" in message: #4.5.
                        file_index = message.find("FILE:")#4.5.
                        file_message = message[file_index:]  # "FILE:" 부터 내용만 추출 #4.5.
                        # 파일 메시지 정규식: FILE:파일명|URL (타임스탬프)
                        file_pattern = re.compile(r"^FILE:(.+?)\|(.+?) \((.+?)\)$") #4.5.
                        match = file_pattern.match(file_message)

                        if match:
                            file_name, file_url, timestamp = match.groups()
                            formatted_message = ft.Row([
                                ft.Text(f"{nickname}: ", weight="bold"),  # 메시지 송신자
                                ft.Icon(ft.icons.ATTACH_FILE, size=18, color=ft.colors.BLUE),
                                ft.TextButton(
                                    text=file_name,
                                    style=ft.ButtonStyle(color=ft.colors.BLUE),
                                    on_click=lambda e: page.launch_url(file_url)
                                ),
                                ft.Text(f"({timestamp})", size=10, color=ft.colors.GREY)
                            ], spacing=5, alignment=ft.MainAxisAlignment.START)
                            messages_list.controls.append(formatted_message)
                        else:
                            print(f"⚠ 파일 메시지 파싱 실패: {message}")
                            messages_list.controls.append(
                                ft.Text("파일 메시지 처리 오류", style=ft.TextStyle(color=ft.colors.RED)))
                        page.update()

                    else:
                        formatted_message = parse_message_text(message, all_users=all_users) #4.5.
                        messages_list.controls.append(formatted_message)
                        page.update()
        except Exception as e:
            messages_list.controls.append(ft.Text(f"WebSocket error: {str(e)}", color="red"))
            page.update()

    # 메시지 전송 함수
    async def send_ws_message(message: str):
        if ws_connection["ws"]:
            try:
                await ws_connection["ws"].send(message)
            except Exception as e:
                messages_list.controls.append(ft.Text(f"Send error: {str(e)}", color="red"))
                page.update()

    def send_message(e):
        msg = input_field.value.strip()
        if msg and ws_connection["ws"]:
            try:
                # 메시지를 전송하기 전에 메시지를 포맷 처리 (parse_message_text 호출)
                # formatted_message = parse_message_text(msg, all_users=[nickname])
                # 포맷된 메시지를 WebSocket으로 전송
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_ws_message(msg))

                page.update()
            except Exception as e:
                messages_list.controls.append(ft.Text(f"Send error: {str(e)}", color="red"))
                page.update()
        input_field.value = ""  # 입력창 초기화
        page.update()

    send_button.on_click = send_message

    # WebSocket 핸들러를 별도의 쓰레드에서 실행 (이벤트 루프 충돌 방지)
    def start_ws_thread():
        def run_ws():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(ws_handler())

        if ws_connection["thread"] and ws_connection["thread"].is_alive():
            ws_connection["thread"].join()

        ws_connection["thread"] = threading.Thread(target=run_ws, daemon=True)
        ws_connection["thread"].start()

    start_ws_thread()

    # 채널 생성 다이얼로그 열기 함수
    def open_create_channel_dialog():
        channel_name_field = ft.TextField(label="채널 이름", autofocus=True)
        channel_password_field = ft.TextField(label="비밀번호 (선택)", password=True)

        async def create_channel(e):
            new_channel = channel_name_field.value.strip()
            if new_channel:
                data = {"title": new_channel, "password": channel_password_field.value.strip()}
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post("http://43.203.205.210:5050/chat/create_channel", json=data)
                        if response.status_code == 200:
                            channels_list.append(new_channel)
                            page.snack_bar = ft.SnackBar(ft.Text("채널 생성 성공"))
                            page.dialog.open = False  # 다이얼로그 닫기
                            page.snack_bar.open = True
                            page.update()
                            switch_channel(new_channel)
                        else:
                            error_detail = response.json().get("detail", "채널 생성 실패")
                            page.snack_bar = ft.SnackBar(ft.Text(f"채널 생성 실패: {error_detail}"))
                            page.snack_bar.open = True
                            page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"에러 발생: {str(ex)}"))
                    page.snack_bar.open = True
                    page.update()

        def cancel(e):
            page.dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("채널 생성"),
            content=ft.Column([channel_name_field, channel_password_field]),
            actions=[
                ft.ElevatedButton("생성", on_click=create_channel),
                ft.TextButton("취소", on_click=cancel)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        page.dialog = dialog
        page.dialog.open = True
        page.update()

    #5. 파일 업로드 관련
    # 파일 업로드 후 전송 완료 메시지 처리
    async def upload_file(file_obj):
        try:
            async with httpx.AsyncClient() as client:
            # FilePickerFile 객체에서 파일을 읽어 bytes 형태로 변환
                with open(file_obj.path, 'rb') as file:
                    response = await client.post(
                        "http://43.203.205.210:5050/chat/upload",
                        files={"file": (file_obj.name, file, "application/octet-stream")},  # 파일을 bytes로 전달     ## HTTP body 아래로
                        data={"channel": current_channel}  # 채널 정보와 함께 전송
                    )
                    if response.status_code == 200:
                        file_url = response.json().get("file_url", "")
                        file_name = file_obj.name #3.29.
                        print(f"파일 업로드 성공: {file_url}")
                        # 업로드 완료 메시지 표시 // 3.29.

                        # WebSocket으로 파일 메시지 전송
                        file_message = f"FILE:{file_obj.name}|{file_url}"
                        #loop = asyncio.new_event_loop()
                        #asyncio.set_event_loop(loop)
                        #loop.run_until_complete(page.run_task(send_ws_message,file_message))
                        page.run_task(send_ws_message, file_message)

                        page.update()
                    else:
                        messages_list.controls.append(ft.Text("파일 업로드 실패", color=ft.colors.RED))
                        page.update()
        except Exception as ex:
            print(f"파일 업로드 중 오류 발생: {ex}")
            messages_list.controls.append(ft.Text("파일 업로드 중 오류 발생", color=ft.colors.RED))
            page.update()


# 단독 실행 시 테스트 (임시 on_success 콜백 전달)
if __name__ == "__main__":
    def dummy_launch(page: ft.Page):
        # 임의의 토큰과 닉네임을 전달 (실제 테스트 시 로그인 후 받은 값 사용)
        page.run_task(chat_lobby, page, jwt_token="your_jwt_token_here", nickname="테스트유저")

    ft.app(target=dummy_launch)
