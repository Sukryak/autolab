const axios = require('axios');

// 환경변수에서 사용자 ID와 비밀번호 가져오기
const userId = process.env.AUTOLABS_USER_ID;
const password = process.env.AUTOLABS_PASSWORD;

if (!userId || !password) {
  console.error('환경변수 AUTOLABS_USER_ID와 AUTOLABS_PASSWORD를 설정해야 합니다.');
  process.exit(1);
}

// 쿠키 저장 변수
let cookies = '';
let csrfToken = '';

// 출석체크 성공 여부 확인 함수
async function checkAttendanceSuccess() {
  try {
    const response = await axios.get('https://autolabs.co.kr/attendance', {
      headers: {
        'Cookie': cookies
      }
    });
    
    // 출석체크 성공 여부를 확인하는 로직
    // 예: 오늘 날짜에 출석체크가 되어있는지 확인
    const today = new Date();
    const dateString = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
    
    return response.data.includes(`<td class="today">${dateString}</td>`) && 
           response.data.includes('출석완료');
  } catch (error) {
    console.error('출석체크 확인 중 오류 발생:', error.message);
    return false;
  }
}

// 서버 시간 가져오기
async function getServerTime() {
  try {
    const response = await axios.get('https://autolabs.co.kr/attendance');
    const match = response.data.match(/<span id="clock">(.*?)<\/span>/);
    if (match && match[1]) {
      return match[1]; // 예: "2024-12-27 00:21:30"
    }
    throw new Error('서버 시간을 찾을 수 없습니다.');
  } catch (error) {
    console.error('서버 시간 가져오기 오류:', error.message);
    throw error;
  }
}

// 최초 접속 및 CSRF 토큰 가져오기
async function getInitialCsrfToken() {
  try {
    const response = await axios.get('https://autolabs.co.kr/');
    cookies = response.headers['set-cookie'].join('; ');
    
    const match = response.data.match(/csrf-token" content="(.*?)"/);
    if (match && match[1]) {
      csrfToken = match[1];
      return csrfToken;
    }
    throw new Error('CSRF 토큰을 찾을 수 없습니다.');
  } catch (error) {
    console.error('CSRF 토큰 가져오기 오류:', error.message);
    throw error;
  }
}

// 로그인 함수
async function login() {
  try {
    const encodedPassword = encodeURIComponent(password);
    const response = await axios.post('https://autolabs.co.kr/', 
      `error_return_url=%2F&mid=main&ruleset=%40login&act=procMemberLogin&success_return_url=%2F&user_id=${userId}&password=${encodedPassword}&_rx_csrf_token=${csrfToken}`,
      {
        headers: {
          'Referer': 'https://autolabs.co.kr/',
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Cookie': cookies
        }
      }
    );
    
    // 쿠키 업데이트
    if (response.headers['set-cookie']) {
      cookies = response.headers['set-cookie'].join('; ');
    }
    
    return response.status === 200;
  } catch (error) {
    console.error('로그인 중 오류 발생:', error.message);
    return false;
  }
}

// 출석체크 함수
async function attendanceCheck() {
  try {
    const response = await axios.post('https://autolabs.co.kr/',
      `error_return_url=%2F&ruleset=Attendanceinsert&mid=main&act=procAttendanceInsertAttendance&xe_validator_id=modules%2Fattendance%2Fskins%2Fdefault%2Fattendanceinsert&success_return_url=%2F&greetings=&_rx_csrf_token=${csrfToken}`,
      {
        headers: {
          'Referer': 'https://autolabs.co.kr/',
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'Cookie': cookies
        }
      }
    );
    
    return response.status === 200;
  } catch (error) {
    console.error('출석체크 중 오류 발생:', error.message);
    return false;
  }
}

// 서버 시간 기반으로 대기 시간 계산
async function calculateWaitTime() {
  try {
    const serverTimeStr = await getServerTime();
    console.log('서버 시간:', serverTimeStr);
    
    const timeMatch = serverTimeStr.match(/\d{2}:\d{2}:\d{2}/);
    if (!timeMatch) {
      throw new Error('서버 시간 형식이 올바르지 않습니다.');
    }
    
    const timeParts = timeMatch[0].split(':');
    const hours = parseInt(timeParts[0]);
    const minutes = parseInt(timeParts[1]);
    const seconds = parseInt(timeParts[2]);
    
    const currentSeconds = hours * 3600 + minutes * 60 + seconds;
    
    // 12시간(43200초) 이후라면 다음날 00:00까지 대기
    if (currentSeconds > 43200) {
      // 86400은 하루의 총 초
      return (86400 - currentSeconds) * 1000 - 1000;
    } else {
      return 0;
    }
  } catch (error) {
    console.error('대기 시간 계산 오류:', error.message);
    return 0;
  }
}

// 지연 함수
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 메인 함수
async function main() {
  try {
    // 1. CSRF 토큰 가져오기
    await getInitialCsrfToken();
    console.log('CSRF 토큰 획득 완료');
    
    // 2. 서버 시간 기반으로 대기 시간 계산
    const waitTime = await calculateWaitTime();
    if (waitTime > 0) {
      console.log(`다음 출석체크까지 ${waitTime / 1000} 초 대기 중...`);
      await delay(waitTime);
    }
    
    // 3. 로그인
    const loginSuccess = await login();
    if (!loginSuccess) {
      throw new Error('로그인 실패');
    }
    console.log('로그인 성공');
    
    // 4. 출석체크 시도 (최대 5번)
    let attendanceSuccess = false;
    let attempts = 0;
    
    while (!attendanceSuccess && attempts < 5) {
      console.log(`출석체크 시도 ${attempts + 1}/5`);
      await attendanceCheck();
      
      // 출석체크 성공 여부 확인
      attendanceSuccess = await checkAttendanceSuccess();
      
      if (!attendanceSuccess) {
        console.log('출석체크가 확인되지 않았습니다. 30초 후 재시도합니다.');
        await delay(30000); // 30초 대기
      }
      
      attempts++;
    }
    
    if (attendanceSuccess) {
      console.log('출석체크 성공!');
    } else {
      console.log('최대 시도 횟수 초과. 출석체크 실패.');
    }
  } catch (error) {
    console.error('오류 발생:', error.message);
    process.exit(1);
  }
}

// 스크립트 실행
main();
