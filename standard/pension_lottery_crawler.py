#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 연금복권 크롤링 스크립트 (기존 프로젝트 구조 유지)
작동하는 코드의 핵심 로직을 채택하여 무한로딩 문제 해결
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import logging
from datetime import datetime
import os
import re
import sys
import sqlite3
import pandas as pd


class FixedPensionLotteryCrawler:
    def __init__(self, lottery_type="720"):
        """개선된 크롤러 초기화"""
        self.lottery_type = lottery_type
        self.base_url = "https://dhlottery.co.kr"

        if lottery_type == "720":
            self.pension_url = f"{self.base_url}/gameResult.do?method=win720&Round="
            self.lottery_name = "연금복권720+"
        elif lottery_type == "520":
            self.pension_url = f"{self.base_url}/gameResult.do?method=win520&Round="
            self.lottery_name = "연금복권520"
        else:
            raise ValueError("lottery_type은 '720' 또는 '520'이어야 합니다.")

        self.session = requests.Session()

        # 디렉토리 생성
        self.data_dir = 'lottery_data'
        self.db_file = f'lottery_data/pension_lottery_{lottery_type}.db'
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        # 로깅 설정
        log_filename = f"logs/fixed_crawling_{lottery_type}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # 헤더 설정 (작동하는 코드와 동일)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 데이터베이스 초기화
        self.init_database()

        self.data = []
        self.failed_rounds = []

    def init_database(self):
        """데이터베이스 초기화 (작동하는 코드 방식 채택)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lottery_results (
                round_number INTEGER PRIMARY KEY,
                first_number TEXT,
                second_number TEXT,
                jo INTEGER,
                lottery_type TEXT,
                draw_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        self.logger.info("데이터베이스 초기화 완료")

    def extract_numbers_from_text(self, text):
        """작동하는 코드의 추출 로직 채택"""
        # 핵심 패턴 - 간단하고 효과적
        pattern = r'(\d+)조(\d+)'
        match = re.search(pattern, text.replace(' ', '').replace('\n', ''))
        if match:
            jo = match.group(1)
            remaining = match.group(2)

            # 유효성 검사
            if 1 <= int(jo) <= 5 and len(remaining) == 6:
                return {
                    'jo': int(jo),
                    'number': remaining,
                    'full': f"{jo}조{remaining}"
                }

        return None

    def crawl_round_data(self, round_number):
        """작동하는 코드의 크롤링 로직 채택"""
        url = self.pension_url + str(round_number)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            data = {
                'round_number': round_number,
                'first_number': '',
                'second_number': '',
                'jo': 0,
                'lottery_type': self.lottery_type,
                'draw_date': ''
            }

            # 테이블에서 당첨번호 추출 (작동하는 코드 방식)
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        grade = cells[0].get_text(strip=True)
                        numbers_cell = cells[2] if len(cells) > 2 else cells[1]

                        if '1등' in grade or '1등' in numbers_cell.get_text():
                            # 1등 번호 추출
                            number_text = numbers_cell.get_text(strip=True)
                            extracted = self.extract_numbers_from_text(number_text)
                            if extracted:
                                data['first_number'] = extracted['number']
                                data['jo'] = extracted['jo']
                                data['second_number'] = extracted['number'][-1]  # 끝자리를 2등으로

                        elif '보너스' in grade or '2등' in grade:
                            # 보너스/2등 번호 추출
                            number_text = numbers_cell.get_text(strip=True)
                            # 6자리 숫자만 추출
                            bonus_match = re.search(r'(\d{6})', number_text)
                            if bonus_match:
                                data['second_number'] = bonus_match.group(1)[-1]

            # 날짜 정보 추출
            date_pattern = r'(\d{4})-(\d{2})-(\d{2})'
            date_match = re.search(date_pattern, response.text)
            if date_match:
                data['draw_date'] = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            else:
                data['draw_date'] = datetime.now().strftime('%Y-%m-%d')

            # 데이터 유효성 검사
            if data['first_number'] and data['jo'] > 0:
                return data
            else:
                self.logger.warning(f"Round {round_number}: 유효한 데이터를 추출하지 못함")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Round {round_number} 네트워크 오류: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Round {round_number} 데이터 처리 오류: {e}")
            return None

    def save_to_database(self, data):
        """데이터베이스에 저장 (작동하는 코드 방식)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # 기존 데이터 확인
        cursor.execute('SELECT round_number FROM lottery_results WHERE round_number = ?',
                       (data['round_number'],))
        existing = cursor.fetchone()

        if existing:
            # 업데이트
            cursor.execute('''
                UPDATE lottery_results 
                SET first_number = ?, second_number = ?, jo = ?, 
                    draw_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE round_number = ?
            ''', (data['first_number'], data['second_number'], data['jo'],
                  data['draw_date'], data['round_number']))
            self.logger.info(f"Round {data['round_number']} 데이터 업데이트됨")
        else:
            # 새로 추가
            cursor.execute('''
                INSERT INTO lottery_results 
                (round_number, first_number, second_number, jo, lottery_type, draw_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['round_number'], data['first_number'], data['second_number'],
                  data['jo'], data['lottery_type'], data['draw_date']))
            self.logger.info(f"Round {data['round_number']} 새 데이터 추가됨: {data['jo']}조 {data['first_number']}")

        conn.commit()
        conn.close()

    def get_latest_round_from_db(self):
        """데이터베이스에서 최신 회차 조회"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(round_number) FROM lottery_results')
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] else 0

    def save_to_csv_json(self):
        """기존 프로젝트 형식으로 CSV/JSON 저장"""
        conn = sqlite3.connect(self.db_file)

        # 기존 프로젝트 형식에 맞게 데이터 변환
        cursor = conn.cursor()
        cursor.execute('''
            SELECT round_number, first_number, second_number, jo, lottery_type, draw_date 
            FROM lottery_results 
            ORDER BY round_number
        ''')

        rows = cursor.fetchall()

        # CSV 형식 데이터 준비
        csv_data = []
        for row in rows:
            csv_data.append({
                'round': row[0],
                'first_number': row[1],
                'second_number': row[2],
                'jo': row[3],
                'lottery_type': row[4],
                'crawl_date': row[5] or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        # CSV 저장
        csv_filename = f'lottery_data/pension_lottery_{self.lottery_type}_all.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            if csv_data:
                fieldnames = ['round', 'first_number', 'second_number', 'jo', 'lottery_type', 'crawl_date']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

        # JSON 저장
        json_filename = f'lottery_data/pension_lottery_{self.lottery_type}_all.json'
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(csv_data, jsonfile, ensure_ascii=False, indent=2)

        # 기존 파일명으로도 저장 (하위 호환성)
        if self.lottery_type == "720":
            import shutil
            try:
                shutil.copy2(csv_filename, 'lottery_data/pension_lottery_all.csv')
                self.logger.info("레거시 파일명으로도 저장 완료")
            except Exception as e:
                self.logger.warning(f"레거시 파일 복사 실패: {e}")

        conn.close()
        self.logger.info(f"CSV/JSON 저장 완료: {len(csv_data)}개 회차")

    def crawl_all_improved(self, start_round=1, end_round=None, max_retries=3):
        """개선된 전체 크롤링 (작동하는 코드 로직 + 기존 구조)"""
        self.logger.info(f"=== {self.lottery_name} 개선된 크롤링 시작 ===")

        # 최신 회차 확인
        if end_round is None:
            # 현재 DB의 최신 회차부터 시작
            latest_in_db = self.get_latest_round_from_db()
            start_round = max(start_round, latest_in_db + 1) if latest_in_db > 0 else start_round

            # 추정 최대 회차 (2025년 기준으로 265회 정도)
            estimated_max = 300
            end_round = min(start_round + 50, estimated_max)

        self.logger.info(f"크롤링 범위: {start_round}회 ~ {end_round}회")

        failed_rounds = []
        success_count = 0

        for round_num in range(start_round, end_round + 1):
            retry_count = 0

            while retry_count < max_retries:
                self.logger.info(f"Round {round_num} 시도 {retry_count + 1}/{max_retries}")

                data = self.crawl_round_data(round_num)

                if data and data['first_number']:
                    # 성공: DB에 저장
                    self.save_to_database(data)
                    success_count += 1
                    break  # 다음 회차로
                else:
                    retry_count += 1
                    if retry_count < max_retries:
                        self.logger.warning(f"Round {round_num} 재시도 중...")
                        time.sleep(2)  # 재시도 전 대기
                    else:
                        self.logger.error(f"Round {round_num} 최대 재시도 초과 - 실패 처리")
                        failed_rounds.append(round_num)

            # 요청 간 간격 (서버 부하 방지)
            if round_num < end_round:
                time.sleep(1)

        # CSV/JSON 저장 (기존 프로젝트 호환)
        self.save_to_csv_json()

        # 결과 보고
        self.logger.info("=== 크롤링 완료 ===")
        self.logger.info(f"성공: {success_count}개 회차")
        self.logger.info(f"실패: {len(failed_rounds)}개 회차")

        if failed_rounds:
            self.logger.info(f"실패 회차: {failed_rounds}")

        return success_count > 0

    def get_latest_round(self):
        """최신 회차 확인 (단순화된 버전)"""
        try:
            # 최근 회차부터 역순으로 확인
            for test_round in range(300, 200, -1):  # 300부터 200까지 역순
                url = self.pension_url + str(test_round)
                response = self.session.get(url, timeout=5)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()

                    # 당첨번호가 있는지 확인
                    if re.search(r'\d+조\d+', text):
                        self.logger.info(f"최신 회차 확인: {test_round}회")
                        return test_round

                time.sleep(0.5)  # 짧은 대기

            return 265  # 기본값 (2025년 1월 기준)

        except Exception as e:
            self.logger.error(f"최신 회차 확인 실패: {e}")
            return 265

    def display_summary(self):
        """데이터 요약 정보 출력"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM lottery_results')
        total_count = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(round_number), MAX(round_number) FROM lottery_results')
        min_round, max_round = cursor.fetchone()

        print(f"\n=== {self.lottery_name} 데이터 요약 ===")
        print(f"총 저장된 회차: {total_count}")
        if min_round and max_round:
            print(f"회차 범위: {min_round} ~ {max_round}")

            # 최근 5개 회차 데이터 조회
            cursor.execute('''
                SELECT round_number, first_number, jo, draw_date 
                FROM lottery_results 
                ORDER BY round_number DESC 
                LIMIT 5
            ''')

            recent_data = cursor.fetchall()
            print(f"\n=== 최근 5개 회차 ===")
            for data in recent_data:
                print(f"Round {data[0]}: {data[2]}조{data[1]} ({data[3]})")
        else:
            print("저장된 데이터가 없습니다.")

        conn.close()


def main():
    """메인 실행 함수"""
    # 환경변수에서 타입 확인 (기존 프로젝트 방식)
    lottery_type = os.environ.get('LOTTERY_TYPE', '720')

    # 명령행 인수 처리
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == '--type' and i + 1 < len(sys.argv):
                lottery_type = sys.argv[i + 1]

    try:
        crawler = FixedPensionLotteryCrawler(lottery_type)

        print(f"🎰 {crawler.lottery_name} 개선된 크롤링 시작")
        print("   - 작동하는 검증된 로직 적용")
        print("   - SQLite 중간 저장으로 안정성 확보")
        print("   - 명확한 재시도 로직으로 무한로딩 방지")
        print()

        # 크롤링 실행
        success = crawler.crawl_all_improved()

        if success:
            print(f"\n🎉 크롤링이 성공적으로 완료되었습니다!")
            crawler.display_summary()
        else:
            print(f"\n⚠️ 크롤링에서 일부 문제가 발생했습니다.")
            print("로그를 확인해주세요.")

    except KeyboardInterrupt:
        print(f"\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()