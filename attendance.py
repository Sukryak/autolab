import os
import re
import time
import requests
from datetime import datetime

# 환경변수에서 사용자 ID와 비밀번호 가져오기
user_id = os.environ.get('AUTOLABS_USER_ID')
password = os.environ.get('AUTOLABS_PASSWORD')

if not user_id or not password:
    print('환경변수 AUTOLABS_USER_ID와 AUTOLABS_PASSWORD를 설정해야 합니다.')
    exit(1)

# 디버깅을 위한 환경 변수 출력
print(f"환경변수 확인:")
print(f"- AUTOLABS_USER_ID 존재: {'예' if user_id else '아니오'}")
print(f"- AUTOLABS_PASSWORD 존재: {'예' if password else '아니오'}")
if user_id:
    print(f"- AUTOLABS_USER_ID: {user_id}")
if password:
    print(f"- AUTOLABS_PASSWORD 길이: {len(password)}자")
    print(f"- AUTOLABS_PASSWORD 앞 2자: {password[:2]}***")

# 세션 생성
session = requests.Session()
csrf_token = None

def get_initial_csrf_token():
    """초기 접속하여 CSRF 토큰 가져오기"""
    try:
        response = session.get('https://autolabs.co.kr/')
        print(f"초기 접속 응답 상태 코드: {response.status_code}")
        
        # CSRF 토큰 추출
        match = re.search(r'csrf-token" content="(.*?)"', response.text)
        if match:
            csrf_token = match.group(1)
            print(f"CSRF 토큰 획득 완료: {csrf_token}")
            return csrf_token
        else:
            print("CSRF 토큰을 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"CSRF 토큰 가져오기 오류: {str(e)}")
        return None

def login(csrf_token):
    """로그인 시도"""
    try:
        print("로그인 시도 중...")
        print(f"사용자 ID: {user_id}")
        print(f"비밀번호 길이: {len(password)}자")
        
        login_data = {
            'error_return_url': '/',
            'mid': 'main',
            'ruleset': '@login',
            'act': 'procMemberLogin',
            'success_return_url': '/',
            'user_id': user_id,
            'password': password,
            '_rx_csrf_token': csrf_token
        }
        
        headers = {
            'Referer': 'https://autolabs.co.kr/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }
        
        response = session.post('https://autolabs.co.kr/', data=login_data, headers=headers)
        print(f"로그인 응답 상태 코드: {response.status_code}")
        
        # 로그인 성공 여부 확인
        login_success = check_login_success()
        print(f"로그인 성공 여부: {login_success}")
        
        return login_success
    except Exception as e:
        print(f"로그인 중 오류 발생: {str(e)}")
        return False

def check_login_success():
    """로그인 성공 여부 확인"""
    try:
        response = session.get('https://autolabs.co.kr/')
        
        # 로그인 실패 메시지 확인
        login_error_messages = [
            '로그인이 필요합니다',
            '로그인 후 이용해주세요',
            '아이디 또는 비밀번호가 일치하지 않습니다'
        ]
        
        has_login_error = any(msg in response.text for msg in login_error_messages)
        
        # 로그인 성공 메시지 확인
        login_success_indicators = [
            '로그아웃',
            'logout',
            '마이페이지',
            '내 정보',
            '프로필'
        ]
        
        has_login_success = any(indicator in response.text for indicator in login_success_indicators)
        
        print(f"- 로그인 오류 메시지 포함 여부: {has_login_error}")
        print(f"- 로그인 성공 지표 포함 여부: {has_login_success}")
        
        # 로그인 상태 확인을 위한 추가 정보
        if '알림' in response.text.lower() or 'alert' in response.text.lower():
            alert_pattern = r'<div class="alert[^>]*>([\s\S]*?)<\/div>'
            alerts = re.findall(alert_pattern, response.text)
            if alerts:
                print(f"페이지에서 발견된 알림 메시지: {alerts}")
        
        return not has_login_error and has_login_success
    except Exception as e:
        print(f"로그인 확인 중 오류 발생: {str(e)}")
        return False

def get_server_time():
    """서버 시간 가져오기"""
    try:
        response = session.get('https://autolabs.co.kr/attendance')
        match = re.search(r'<span id="clock">(.*?)<\/span>', response.text)
        if match:
            server_time = match.group(1)
            print(f"서버 시간: {server_time}")
            return server_time
        else:
            print("서버 시간을 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"서버 시간 가져오기 오류: {str(e)}")
        return None

def calculate_sleep_time(server_time_str):
    """서버 시간 기반으로 자정까지 대기 시간 계산 (오토핫키 방식)"""
    try:
        # 시간 추출 (예: "2024-12-27 00:21:30"에서 시간 부분)
        time_match = re.search(r'(\d{2}):(\d{2}):(\d{2})', server_time_str)
        if not time_match:
            print("서버 시간 형식이 올바르지 않습니다.")
            return 0
        
        hours = int(time_match.group(1))
        minutes = int(time_match.group(2))
        seconds = int(time_match.group(3))
        
        current_seconds = hours * 3600 + minutes * 60 + seconds
        
        # 12시간(43200초) 이후라면 다음날 00:00까지 대기
        if current_seconds > 43200:
            # 86400은 하루의 총 초
            sleep_time = (86400 - current_seconds) * 1000
            print(f"자정까지 대기 시간: {sleep_time / 1000}초")
            return sleep_time
        else:
            print("현재 시간이 오후가 아니므로 대기하지 않습니다.")
            return 0
    except Exception as e:
        print(f"대기 시간 계산 오류: {str(e)}")
        return 0

def attendance_check(csrf_token):
    """출석체크 시도"""
    try:
        # 출석체크 페이지 먼저 방문하여 새로운 CSRF 토큰 획득
        response = session.get('https://autolabs.co.kr/attendance')
        
        # 출석체크 페이지에서 새로운 CSRF 토큰 추출
        page_csrf_match = re.search(r'csrf-token" content="(.*?)"', response.text)
        if page_csrf_match:
            csrf_token = page_csrf_match.group(1)
            print(f"출석체크 페이지에서 새로운 CSRF 토큰 획득: {csrf_token}")
        
        # 출석체크 요청 데이터
        attendance_data = {
            'error_return_url': '/',
            'ruleset': 'Attendanceinsert',
            'mid': 'attendance',
            'act': 'procAttendanceInsertAttendance',
            'success_return_url': '/attendance',
            'xe_validator_id': 'modules/attendance/skins/default/attendanceinsert',
            'greetings': '',
            '_rx_csrf_token': csrf_token
        }
        
        headers = {
            'Referer': 'https://autolabs.co.kr/attendance',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }
        
        # 출석체크 요청 전송
        response = session.post('https://autolabs.co.kr/attendance', data=attendance_data, headers=headers)
        print(f"출석체크 요청 응답 상태 코드: {response.status_code}")
        
        # 응답에 성공 메시지가 포함되어 있는지 바로 확인
        success_pattern = '<div class="alert alert-success">'
        success_messages = [
            '출석이 완료되었습니다',
            '출석은 하루 1회만 참여하실 수 있습니다',
            '내일 다시 출석해 주세요'
        ]
        
        has_success_pattern = success_pattern in response.text
        has_success_message = any(msg in response.text for msg in success_messages)
        
        if has_success_pattern or has_success_message:
            print("출석체크 요청 직후 성공 메시지 확인됨!")
            return True
        
        return response.status_code == 200
    except Exception as e:
        print(f"출석체크 중 오류 발생: {str(e)}")
        return False

def check_attendance_success():
    """출석체크 성공 여부 확인"""
    try:
        response = session.get('https://autolabs.co.kr/attendance')
        
        # 특정 HTML 패턴으로 출석체크 성공 여부 확인
        success_pattern = '<div class="alert alert-success">'
        success_messages = [
            '출석이 완료되었습니다',
            '출석은 하루 1회만 참여하실 수 있습니다',
            '내일 다시 출석해 주세요'
        ]
        
        # 성공 패턴이 있는지 확인
        has_success_pattern = success_pattern in response.text
        
        # 성공 메시지 중 하나라도 포함되어 있는지 확인
        has_success_message = any(msg in response.text for msg in success_messages)
        
        # 디버깅을 위한 로그
        print('출석체크 확인 결과:')
        print(f'- 성공 패턴 포함 여부: {has_success_pattern}')
        print(f'- 성공 메시지 포함 여부: {has_success_message}')
        
        # 두 조건 중 하나라도 만족하면 성공으로 간주
        is_success = has_success_pattern or has_success_message
        
        if is_success:
            print('출석체크 성공이 확인되었습니다!')
        else:
            print('출석체크 성공을 확인할 수 없습니다.')
            
            # 디버깅을 위해 응답의 일부 출력
            if 'alert' in response.text:
                alert_pattern = r'<div class="alert[^>]*>([\s\S]*?)<\/div>'
                alerts = re.findall(alert_pattern, response.text)
                if alerts:
                    print(f'페이지에서 발견된 알림 메시지: {alerts}')
        
        return is_success
    except Exception as e:
        print(f'출석체크 확인 중 오류 발생: {str(e)}')
        return False

def main():
    try:
        print(f"실행 시작 시간: {datetime.now()}")
        
        # 1. CSRF 토큰 가져오기
        global csrf_token
        csrf_token = get_initial_csrf_token()
        if not csrf_token:
            raise Exception("CSRF 토큰 획득 실패")
        
        # 2. 로그인
        login_success = login(csrf_token)
        if not login_success:
            raise Exception("로그인 실패")
        print("로그인 성공")
        
        # 3. 서버 시간 가져오기
        server_time_str = get_server_time()
        if not server_time_str:
            raise Exception("서버 시간 획득 실패")
        
        # 4. 자정까지 대기 시간 계산 (밀리초 단위)
        sleep_time = calculate_sleep_time(server_time_str)
        
        # 5. 대기가 필요하면 대기
        if sleep_time > 0:
            sleep_seconds = sleep_time / 1000
            print(f"자정까지 {sleep_seconds}초 대기 중...")
            
            # 안전을 위해 1초 일찍 깨어남
            if sleep_seconds > 1:
                time.sleep(sleep_seconds - 1)
            
            print("대기 완료. 서버 시간 다시 확인 중...")
            
            # 서버 시간 다시 확인하여 자정이 지났는지 확인
            new_server_time = get_server_time()
            if new_server_time:
                time_match = re.search(r'(\d{2}):(\d{2}):(\d{2})', new_server_time)
                if time_match:
                    hours = int(time_match.group(1))
                    if hours < 12:  # 00:00 ~ 11:59 사이라면 (자정이 지났다면)
                        print("자정이 지났습니다. 출석체크를 시도합니다.")
                    else:
                        print("아직 자정이 되지 않았습니다. 1초 더 대기 후 진행합니다.")
                        time.sleep(1)
        
        # 6. 출석체크 시도 (최대 10번)
        attendance_success = False
        attempts = 0
        max_attempts = 10
        
        while not attendance_success and attempts < max_attempts:
            print(f"출석체크 시도 {attempts + 1}/{max_attempts}")
            
            # 출석체크 요청
            attendance_check(csrf_token)
            
            # 출석체크 성공 여부 확인
            attendance_success = check_attendance_success()
            
            if attendance_success:
                print("출석체크 성공!")
                break
            
            print(f"출석체크가 확인되지 않았습니다. 30초 후 재시도합니다.")
            time.sleep(30)  # 30초 대기
            attempts += 1
        
        if not attendance_success:
            print("최대 시도 횟수 초과. 출석체크 실패.")
        
        print(f"실행 종료 시간: {datetime.now()}")
    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
