# 🎰 연금복권 패턴 분석 시스템

데이터 기반으로 연금복권 당첨 패턴을 분석하는 Flask 웹 애플리케이션입니다.

## 📋 목차
- [프로젝트 개요](#-프로젝트-개요)
- [주요 기능](#-주요-기능)
- [설치 및 실행](#-설치-및-실행)
- [사용법](#-사용법)
- [파일 구조](#-파일-구조)
- [분석 기능](#-분석-기능)
- [API 명세](#-api-명세)
- [문제 해결](#-문제-해결)

## 🎯 프로젝트 개요

이 프로젝트는 동행복권 사이트에서 연금복권 데이터를 수집하고, 다양한 패턴 분석을 통해 당첨 번호의 경향을 파악하는 시스템입니다.

### 주요 특징
- **자동 데이터 수집**: 동행복권 사이트 크롤링
- **다각도 분석**: 조별, 번호별, 패턴별 분석
- **시각화**: 차트와 그래프를 통한 결과 표시
- **웹 인터페이스**: 직관적인 Flask 웹 애플리케이션
- **실시간 모니터링**: 작업 진행 상황 실시간 확인

## ✨ 주요 기능

### 1. 데이터 수집
- 🕷️ **자동 크롤링**: 1회차부터 최신 회차까지 전체 데이터 수집
- 💾 **다중 형식 저장**: CSV, JSON 형식으로 데이터 저장
- 📝 **로그 관리**: 상세한 크롤링 로그 자동 생성

### 2. 기본 분석
- 📊 **조별 출현 빈도**: 각 조의 당첨 횟수 분석
- 📈 **트렌드 분석**: 최근 50회차 경향 분석
- 🎯 **끝자리 패턴**: 2등 당첨번호 끝자리 분석
- 📉 **통계 보고서**: 종합적인 분석 결과 제공

### 3. 번호별 분석
- 🔢 **자리별 출현 빈도**: 1~6자리별 숫자 출현 분석
- 🤝 **동반 출현 분석**: 특정 숫자와 함께 나오는 번호 분석
- 📊 **트렌드 점수**: 최근 출현 경향 점수화
- 🔥 **핫/콜드 번호**: 최근 자주/드물게 나오는 번호 식별

### 4. 고급 패턴 분석
- ⚪⚫ **홀짝 패턴**: 홀수/짝수 분포 및 패턴 분석
- 📈 **연속 패턴**: 상승/하강/동일 연속 분석
- 📏 **간격 패턴**: 인접 숫자 간격 분석
- 🔄 **조합 패턴**: 조와 번호의 조합 관계 분석

## 🚀 설치 및 실행

### 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)

### 1단계: 저장소 클론
```bash
git clone [repository-url]
cd lottery-analysis
```

### 2단계: 패키지 설치
```bash
pip install -r requirements.txt
```

### 3단계: 애플리케이션 실행
```bash
python app.py
```

### 4단계: 웹브라우저 접속
```
http://localhost:5000
```

## 📖 사용법

### 1. 기본 사용 순서
1. **데이터 크롤링** 🕷️
   - 메인 페이지에서 "데이터 크롤링" 버튼 클릭
   - 전체 회차 데이터가 자동으로 수집됩니다

2. **기본 분석** 📈
   - "기본 분석 실행" 버튼 클릭
   - 조별 출현 빈도, 트렌드 등 기본 통계 생성

3. **번호별 분석** 🔢
   - "번호별 분석 실행" 버튼 클릭
   - 자리별 출현 빈도, 동반 출현 패턴 분석

4. **패턴 분석** 🔍
   - "패턴 분석 실행" 버튼 클릭
   - 홀짝, 연속, 간격 등 고급 패턴 분석

### 2. 결과 확인
- **대시보드**: 📊 전체 분석 결과 종합 확인
- **패턴분석**: 🔍 상세한 패턴 분석 결과 확인

## 📁 파일 구조

```
mysite/
├── app.py                       # Flask 메인 애플리케이션
├── config.py                    # 설정 파일
├── requirements.txt             # Python 패키지 목록
├── 
├── # 분석 스크립트
├── pension_lottery_crawler.py   # 크롤링 스크립트
├── pension_lottery_analyzer.py  # 기본 분석 스크립트
├── number_analyzer.py          # 번호별 분석 스크립트
├── pattern_analyzer.py         # 패턴 분석 스크립트
├── 
├── # 템플릿 파일
├── templates/
│   ├── base.html               # 기본 템플릿
│   ├── index.html              # 메인 페이지
│   ├── dashboard.html          # 대시보드
│   ├── patterns.html           # 패턴 분석 페이지
│   └── error.html              # 에러 페이지
├── 
├── # 데이터 디렉토리
├── lottery_data/               # 크롤링된 원본 데이터
├── analysis_results/           # 분석 결과 파일
├── charts/                     # 생성된 차트 이미지
├── logs/                       # 로그 파일
├── 
└── README.md                   # 프로젝트 설명서
```

## 📊 분석 기능

### 기본 분석
| 분석 유형 | 설명 | 출력 파일 |
|----------|------|-----------|
| 조별 출현 빈도 | 각 조(1~5조)의 당첨 횟수 | `jo_frequency.png` |
| 최근 트렌드 | 최근 50회차 조별 출현 | `recent_jo_frequency.png` |
| 끝자리 분석 | 2등 당첨번호 끝자리 분포 | `last_digit_frequency.png` |

### 번호별 분석
| 분석 유형 | 설명 | 출력 파일 |
|----------|------|-----------|
| 자리별 출현 빈도 | 1~6자리별 숫자(0~9) 출현 분석 | `number_frequency_by_position.png` |
| 동반 출현 | 특정 숫자와 함께 나오는 번호 분석 | `companion_heatmap_pos*.png` |
| 트렌드 점수 | 최근 출현 빈도 기반 점수 | `number_trends.png` |

### 패턴 분석
| 분석 유형 | 설명 | 출력 파일 |
|----------|------|-----------|
| 홀짝 패턴 | 홀수/짝수 분포 및 패턴 | `pattern_analysis.png` |
| 간격 패턴 | 인접 숫자 간격 분포 | `gap_analysis.png` |

## 🔌 API 명세

### 분석 실행 API
```http
POST /api/execute/<action>
```
**Parameters:**
- `action`: `crawl`, `analyze`, `number_analyze`, `pattern_analyze`

**Response:**
```json
{
    "status": "started|error",
    "message": "작업 시작 메시지",
    "task_id": "작업 ID"
}
```

### 작업 상태 확인 API
```http
GET /api/task/<task_id>
```
**Response:**
```json
{
    "status": "running|completed|failed",
    "start_time": "시작 시간",
    "end_time": "종료 시간",
    "output": "실행 결과"
}
```

### 시스템 상태 API
```http
GET /api/status
```
**Response:**
```json
{
    "crawl_data_exists": true,
    "basic_analysis_exists": true,
    "number_analysis_exists": true,
    "pattern_analysis_exists": true,
    "running_tasks": 0
}
```

### 분석 데이터 API
```http
GET /api/data/<data_type>
```
**Parameters:**
- `data_type`: `basic`, `frequency`, `companion`, `trends`, `patterns`, `odd_even`, `consecutive`, `gaps`

### 차트 목록 API
```http
GET /api/charts
```

## 🛠️ 문제 해결

### 일반적인 문제들

#### 1. 크롤링 실패
**증상**: 크롤링이 중단되거나 실패
**해결방법**:
- 인터넷 연결 확인
- 동행복권 사이트 접속 가능한지 확인
- `logs/crawling_log_*.txt` 파일 확인
- 잠시 후 다시 시도

#### 2. 분석 실패
**증상**: 분석 스크립트 실행 오류
**해결방법**:
- 크롤링 데이터가 있는지 확인 (`lottery_data/` 디렉토리)
- Python 패키지가 모두 설치되었는지 확인
- `logs/analysis_log_*.txt` 파일 확인

#### 3. 차트가 표시되지 않음
**증상**: 웹페이지에서 차트 이미지가 안 보임
**해결방법**:
- 분석이 완료되었는지 확인
- `charts/` 디렉토리에 이미지 파일이 있는지 확인
- 브라우저 새로고침 (Ctrl + F5)

#### 4. 포트 충돌
**증상**: Flask 애플리케이션 실행 시 포트 오류
**해결방법**:
```bash
# 다른 포트로 실행
python app.py --port 5001
```

### 로그 파일 위치
- **크롤링 로그**: `logs/crawling_log_*.txt`
- **분석 로그**: `logs/*_analysis_log_*.txt`
- **Flask 로그**: `logs/flask_app.log`
- **PHP 오류 로그**: `logs/php_errors.log` (기존 PHP 버전용)

### 데이터 파일 위치
- **원본 데이터**: `lottery_data/pension_lottery_all.csv`
- **분석 결과**: `analysis_results/*.json`
- **차트 이미지**: `charts/*.png`

## 🔧 개발자 정보

### 기술 스택
- **Backend**: Python 3.8+, Flask 2.3+
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Data Processing**: Pandas, NumPy
- **Visualization**: Matplotlib, Seaborn
- **Web Scraping**: Requests, BeautifulSoup4

### 라이선스
이 프로젝트는 개인 프로젝트로 제작되었습니다.

### 기여하기
버그 리포트나 기능 제안은 이슈로 등록해주세요.

---

**⚠️ 주의사항**: 이 시스템은 분석 목적으로만 사용하세요. 복권 구매는 신중하게 결정하시기 바랍니다.