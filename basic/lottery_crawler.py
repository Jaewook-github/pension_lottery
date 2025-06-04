import requests
import sqlite3
import csv
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import os


class LotteryCrawler:
    def __init__(self, db_name="lottery_data.db", csv_name="lottery_data.csv"):
        self.db_name = db_name
        self.csv_name = csv_name
        self.base_url = "https://dhlottery.co.kr/gameResult.do?method=win720&Round={}"
        self.session = requests.Session()

        # User-Agent 설정 (크롤링 차단 방지)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        self.init_database()

    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lottery_results (
                round_number INTEGER PRIMARY KEY,
                first_prize_numbers TEXT,
                bonus_numbers TEXT,
                draw_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def extract_numbers_from_text(self, text):
        """텍스트에서 숫자를 추출"""
        # 연금복권720+는 7자리 숫자 조합 (예: 5조162265)
        # 조 단위를 포함한 패턴 매칭
        pattern = r'(\d+)조(\d+)'
        match = re.search(pattern, text.replace(' ', '').replace('\n', ''))
        if match:
            jo = match.group(1)
            remaining = match.group(2)
            return f"{jo}조{remaining}"

        # 일반 숫자 패턴
        numbers = re.findall(r'\d+', text.replace(' ', '').replace('\n', ''))
        return ','.join(numbers) if numbers else ""

    def crawl_round_data(self, round_number):
        """특정 회차 데이터 크롤링"""
        url = self.base_url.format(round_number)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 데이터 추출 로직
            data = {
                'round_number': round_number,
                'first_prize_numbers': '',
                'bonus_numbers': '',
                'draw_date': ''
            }

            # 테이블에서 당첨번호 추출
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        grade = cells[0].get_text(strip=True)
                        numbers_cell = cells[2] if len(cells) > 2 else cells[1]

                        if '1등' in grade:
                            # 1등 번호 추출 (7자리)
                            number_text = numbers_cell.get_text(strip=True)
                            data['first_prize_numbers'] = self.extract_numbers_from_text(number_text)

                        elif '보너스' in grade:
                            # 보너스 번호 추출 (6자리)
                            number_text = numbers_cell.get_text(strip=True)
                            data['bonus_numbers'] = self.extract_numbers_from_text(number_text)

            # 날짜 정보 추출 (페이지에서 찾을 수 있는 경우)
            date_pattern = r'(\d{4})-(\d{2})-(\d{2})'
            date_match = re.search(date_pattern, response.text)
            if date_match:
                data['draw_date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            else:
                data['draw_date'] = datetime.now().strftime('%Y-%m-%d')

            return data

        except requests.exceptions.RequestException as e:
            print(f"Round {round_number} 크롤링 실패: {e}")
            return None
        except Exception as e:
            print(f"Round {round_number} 데이터 처리 실패: {e}")
            return None

    def save_to_database(self, data):
        """데이터베이스에 저장 (업데이트 방식)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # 기존 데이터 확인
        cursor.execute('SELECT round_number FROM lottery_results WHERE round_number = ?',
                       (data['round_number'],))
        existing = cursor.fetchone()

        if existing:
            # 업데이트
            cursor.execute('''
                UPDATE lottery_results 
                SET first_prize_numbers = ?, bonus_numbers = ?, 
                    draw_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE round_number = ?
            ''', (data['first_prize_numbers'], data['bonus_numbers'],
                  data['draw_date'], data['round_number']))
            print(f"Round {data['round_number']} 데이터 업데이트됨")
        else:
            # 새로 추가
            cursor.execute('''
                INSERT INTO lottery_results 
                (round_number, first_prize_numbers, bonus_numbers, draw_date)
                VALUES (?, ?, ?, ?)
            ''', (data['round_number'], data['first_prize_numbers'],
                  data['bonus_numbers'], data['draw_date']))
            print(f"Round {data['round_number']} 새 데이터 추가됨")

        conn.commit()
        conn.close()

    def save_to_csv(self):
        """데이터베이스에서 CSV로 저장"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query('SELECT * FROM lottery_results ORDER BY round_number', conn)
        df.to_csv(self.csv_name, index=False, encoding='utf-8-sig')
        conn.close()
        print(f"CSV 파일 저장됨: {self.csv_name}")

    def get_latest_round_from_db(self):
        """데이터베이스에서 최신 회차 번호 조회"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(round_number) FROM lottery_results')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] else 0

    def crawl_all_data(self, start_round=1, end_round=None, max_retries=3):
        """모든 데이터 크롤링 (업데이트 방식)"""
        if end_round is None:
            # 최근 회차 확인을 위해 현재 회차부터 시작해서 데이터가 없을 때까지 확인
            current_round = max(start_round, self.get_latest_round_from_db() + 1)

            # 최대 회차 추정 (현재 날짜 기준)
            # 연금복권720+는 주 1회 추첨이므로 대략적으로 계산
            current_year = datetime.now().year
            estimated_max = (current_year - 2019) * 52 + 300  # 2019년부터 시작했다고 가정

            end_round = min(current_round + 50, estimated_max)  # 현재부터 50회차만 확인

        print(f"크롤링 시작: Round {start_round} ~ {end_round}")

        failed_rounds = []

        for round_num in range(start_round, end_round + 1):
            retry_count = 0

            while retry_count < max_retries:
                print(f"Round {round_num} 크롤링 중... (시도: {retry_count + 1}/{max_retries})")

                data = self.crawl_round_data(round_num)

                if data and (data['first_prize_numbers'] or data['bonus_numbers']):
                    self.save_to_database(data)
                    break
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"Round {round_num} 재시도 중...")
                        time.sleep(2)
                    else:
                        print(f"Round {round_num} 크롤링 실패 (최대 시도 횟수 초과)")
                        failed_rounds.append(round_num)

            # 요청 간 간격 (서버 부하 방지)
            time.sleep(1)

        # CSV 파일 업데이트
        self.save_to_csv()

        if failed_rounds:
            print(f"실패한 회차: {failed_rounds}")
        else:
            print("모든 회차 크롤링 완료!")

    def display_data_summary(self):
        """데이터 요약 정보 출력"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM lottery_results')
        total_count = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(round_number), MAX(round_number) FROM lottery_results')
        min_round, max_round = cursor.fetchone()

        print(f"\n=== 데이터 요약 ===")
        print(f"총 저장된 회차: {total_count}")
        print(f"회차 범위: {min_round} ~ {max_round}")

        # 최근 5개 회차 데이터 조회
        cursor.execute('''
            SELECT round_number, first_prize_numbers, bonus_numbers, draw_date 
            FROM lottery_results 
            ORDER BY round_number DESC 
            LIMIT 5
        ''')

        recent_data = cursor.fetchall()
        print(f"\n=== 최근 5개 회차 ===")
        for data in recent_data:
            print(f"Round {data[0]}: 1등({data[1]}), 보너스({data[2]}), 날짜({data[3]})")

        conn.close()


def main():
    """메인 실행 함수"""
    crawler = LotteryCrawler()

    print("연금복권720+ 크롤링 시스템")
    print("1. 전체 데이터 크롤링 (업데이트)")
    print("2. 특정 범위 크롤링")
    print("3. 데이터 요약 보기")
    print("4. 최신 데이터만 업데이트")

    choice = input("선택하세요 (1-4): ").strip()

    if choice == '1':
        start = int(input("시작 회차 (기본값 1): ") or 1)
        end = input("종료 회차 (엔터시 자동 감지): ").strip()
        end = int(end) if end else None
        crawler.crawl_all_data(start, end)

    elif choice == '2':
        start = int(input("시작 회차: "))
        end = int(input("종료 회차: "))
        crawler.crawl_all_data(start, end)

    elif choice == '3':
        crawler.display_data_summary()

    elif choice == '4':
        latest = crawler.get_latest_round_from_db()
        crawler.crawl_all_data(latest + 1, latest + 10)

    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()