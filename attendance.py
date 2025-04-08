import os
import re
import time
import requests
from datetime import datetime, timedelta

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

def get_time_difference():
    """서버 시간과 실제 시간의 차이 계산 (초 단위)"""
    try:
        server_time_str = get_server_time()
        if not server_time_str:
            return 0
        
        # 서버 시간 파싱 (예: "2024-12-27 00:21:30")
        server_time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', server_time_str)
        if not server_time_match:
            print("서버 시간 형식이 올바르지 않습니다.")
            return 0
        
        server_time = datetime.strptime(server_time_match.group(1), '%Y-%m-%d %H:%M:%S')
        real_time = datetime.now()
        
        # 시간 차이 계산 (초 단위)
        time_diff = (real_time - server_time).total_seconds()
        print(f"서버 시간과 실제 시간의 차이: {time_diff}초")
        print(f"- 서버 시간: {server_time}")
        print(f"- 실제 시간: {real_time}")
        
        return time_diff
    except Exception as e:
        print(f"시간 차이 계산 오류: {str(e)}")
        return 0

def wait_until_midnight(time_diff):
    """자정까지 대기 (서버 시간 기준)"""
    try:
        # 현재 실제 시간
        now = datetime.now()
        
        # 서버 시간 계산 (실제 시간 - 시간차)
        server_time = now - timedelta(seconds=time_diff)
        print(f"현재 서버 시간 (계산): {server_time}")
        
        # 다음 날 자정 계산 (서버 시간 기준)
        next_midnight = datetime(server_time.year, server_time.month, server_time.day) + timedelta(days=1)
        
        # 자정까지 남은 시간 (서버 시간 기준)
        seconds_until_midnight = (next_midnight - server_time).total_seconds()
        
        # 실제로 대기해야 할 시간 (실제 시간 기준)
        real_wait_seconds = max(0, seconds_until_midnight - 10)  # 10초 일찍 시작하여 확실히 자정에 체크하도록
        
        print(f"자정까지 남은 시간 (서버 시간 기준): {seconds_until_midnight}초")
        print(f"실제 대기할 시간: {real_wait_seconds}초")
        
        if real_wait_seconds > 0:
            print(f"{real_wait_seconds}초 동안 대기 중...")
            time.sleep(real_wait_seconds)
            return True
        else:
            # 이미 자정이 지났으면 바로 진행
            print("이미 자정이 지났습니다. 바로 진행합니다.")
            return True
    except Exception as e:
        print(f"자정 대기 중 오류 발생: {str(e)}")
        return False

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
        csrf_token = get_initial_csrf_token()
        if not csrf_token:
            raise Exception("CSRF 토큰 획득 실패")
        
        # 2. 시간 차이 계산
        time_diff = get_time_difference()
        
        # 3. 로그인
        login_success = login(csrf_token)
        if not login_success:
            raise Exception("로그인 실패")
        print("로그인 성공")
        
        # 4. 자정이 지났는지 확인하고, 아니라면 자정까지 대기
        now = datetime.now() - timedelta(seconds=time_diff)  # 서버 시간 기준 현재 시간
        server_hour = now.hour
        
        if server_hour >= 12:  # 서버 시간이 12시 이후라면 자정까지 대기
            print("서버 시간이 12시 이후입니다. 자정까지 대기합니다.")
            wait_until_midnight(time_diff)
        else:
            print("서버 시간이 12시 이전입니다. 바로 출석체크를 시도합니다.")
        
        # 5. 출석체크 시도 (자정 직후 계속 시도)
        attendance_success = False
        max_attempts = 30  # 최대 30번 시도 (총 15분)
        attempts = 0
        
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
