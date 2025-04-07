# AutoLabs 자동 출석체크

이 프로젝트는 [AutoLabs](https://autolabs.co.kr/) 웹사이트에서 자동으로 출석체크를 수행하는 GitHub Actions 워크플로우입니다.

## 기능

- GitHub Actions를 사용하여 매일 자동으로 출석체크
- 환경변수를 통한 안전한 자격 증명 관리
- 서버 시간 차이를 고려한 출석체크 로직
- 출석체크 성공 여부 확인 및 재시도 메커니즘

## 설정 방법

### 1. 저장소 설정

1. 이 저장소를 포크하거나 클론합니다.
2. GitHub 저장소에 다음 시크릿을 추가합니다:
   - `AUTOLABS_USER_ID`: AutoLabs 웹사이트 사용자 ID
   - `AUTOLABS_PASSWORD`: AutoLabs 웹사이트 비밀번호

### 2. GitHub Secrets 설정

1. 저장소의 Settings 탭으로 이동합니다.
2. 왼쪽 메뉴에서 "Secrets and variables" > "Actions"를 선택합니다.
3. "New repository secret" 버튼을 클릭합니다.
4. 다음 시크릿을 추가합니다:
   - Name: `AUTOLABS_USER_ID`, Value: 본인의 AutoLabs 아이디
   - Name: `AUTOLABS_PASSWORD`, Value: 본인의 AutoLabs 비밀번호

### 3. 워크플로우 실행

워크플로우는 다음과 같이 실행됩니다:

- 매일 한국 시간 기준 밤 11:55에 자동으로 실행됩니다.
- GitHub 저장소의 Actions 탭에서 "AutoLabs Attendance Check" 워크플로우를 선택하고 "Run workflow" 버튼을 클릭하여 수동으로 실행할 수도 있습니다.

## 코드 구성

- `.github/workflows/attendance.yml`: GitHub Actions 워크플로우 설정 파일
- `attendance.js`: 출석체크를 수행하는 JavaScript 코드

## 문제 해결

1. 출석체크가 실패하는 경우, GitHub Actions의 실행 로그를 확인합니다.
2. 로그인 실패 시, GitHub Secrets의 자격 증명이 올바른지 확인합니다.
3. 웹사이트의 변경으로 인해 출석체크가 작동하지 않는 경우, 코드를 업데이트해야 할 수 있습니다.

## 주의사항

- 이 스크립트는 교육 및 개인적 사용을 위한 것입니다.
- 웹사이트의 이용 약관을 준수하고 서버에 부담을 주지 않도록 합니다.
