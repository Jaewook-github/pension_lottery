#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 당첨번호 크롤링 스크립트
동행복권 사이트에서 연금복권 데이터를 수집하여 CSV/JSON으로 저장
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


class PensionLotteryCrawler:
    def __init__(self):
        """크롤러 초기화"""
        self.base_url = "https://www.dhlottery.co.kr"
        self.pension_url = f"{self.base_url}/gameResult.do?method=byWin&wiselog=H_C_1_1&drwNo="
        self.session = requests.Session()

        # 디렉토리 생성
        self.data_dir = 'lottery_data'
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs('logs', exist_ok=True)

        # 로깅 설정
        log_filename = f"logs/crawling_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        self.data = []

    def get_latest_round(self):
        """최신 회차 번호 가져오기"""
        try:
            response = self.session.get(f"{self.base_url}/gameResult.do?method=byWin")
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 회차 번호 찾기 (여러 방법 시도)
            selectors = [
                'select[name="drwNo"] option:first-child',
                '.win_result .title strong',
                '#article .title'
            ]

            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        latest_round = int(numbers[0])
                        self.logger.info(f"최신 회차 확인: {latest_round}회")
                        return latest_round

            # 기본값으로 현재 회차 추정
            current_year = datetime.now().year
            weeks_passed = (datetime.now() - datetime(current_year, 1, 1)).days // 7
            estimated_round = (current_year - 2021) * 52 + weeks_passed

            self.logger.warning(f"최신 회차를 찾을 수 없어 추정값 사용: {estimated_round}회")
            return estimated_round

        except Exception as e:
            self.logger.error(f"최신 회차 확인 실패: {e}")
            return 1000  # 기본값

    def crawl_round(self, round_num):
        """특정 회차 데이터 크롤링"""
        try:
            url = f"{self.pension_url}{round_num}"
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 당첨번호 추출 시도
            round_data = self._extract_winning_numbers(soup, round_num)

            if round_data:
                self.data.append(round_data)
                return True
            else:
                self.logger.warning(f"{round_num}회 데이터를 찾을 수 없습니다.")
                return False

        except Exception as e:
            self.logger.error(f"{round_num}회 크롤링 실패: {e}")
            return False

    def _extract_winning_numbers(self, soup, round_num):
        """HTML에서 당첨번호 추출"""
        try:
            # 다양한 셀렉터로 당첨번호 찾기
            selectors = [
                '.win_result .num',
                '.lotto_num',
                '.winner_number',
                'span.ball_645'
            ]

            winning_numbers = []
            for selector in selectors:
                numbers = soup.select(selector)
                if numbers:
                    for num in numbers:
                        text = num.get_text().strip()
                        if text.isdigit():
                            winning_numbers.append(text)
                    break

            if not winning_numbers:
                # 텍스트에서 숫자 패턴 찾기
                text = soup.get_text()
                patterns = [
                    r'당첨번호.*?(\d{6})',
                    r'(\d{6})',
                    r'번호.*?(\d{6})'
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        winning_numbers = matches
                        break

            if winning_numbers and len(winning_numbers) >= 1:
                # 1등 당첨번호 (6자리)
                first_number = winning_numbers[0].zfill(6)

                # 2등 당첨번호 (보통 끝자리 번호)
                second_number = '0'  # 기본값
                if len(winning_numbers) > 1:
                    second_number = winning_numbers[1][-1]  # 마지막 자리
                elif len(first_number) == 6:
                    second_number = first_number[-1]  # 1등 번호의 마지막 자리

                # 조 계산 (1등 번호 앞자리로)
                jo = int(first_number[0]) if first_number[0] != '0' else 1
                if jo > 5:
                    jo = jo % 5 + 1

                return {
                    'round': round_num,
                    'first_number': first_number,
                    'second_number': second_number,
                    'jo': jo,
                    'crawl_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            return None

        except Exception as e:
            self.logger.error(f"당첨번호 추출 실패 (round {round_num}): {e}")
            return None

    def save_to_csv(self, filename='pension_lottery_all.csv'):
        """CSV 파일로 저장"""
        filepath = os.path.join(self.data_dir, filename)

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if self.data:
                    fieldnames = self.data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.data)

            self.logger.info(f"CSV 저장 완료: {filepath} ({len(self.data)}개 회차)")

        except Exception as e:
            self.logger.error(f"CSV 저장 실패: {e}")

    def save_to_json(self, filename='pension_lottery_all.json'):
        """JSON 파일로 저장"""
        filepath = os.path.join(self.data_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.data, jsonfile, ensure_ascii=False, indent=2)

            self.logger.info(f"JSON 저장 완료: {filepath} ({len(self.data)}개 회차)")

        except Exception as e:
            self.logger.error(f"JSON 저장 실패: {e}")

    def load_existing_data(self):
        """기존 데이터 로드"""
        csv_file = os.path.join(self.data_dir, 'pension_lottery_all.csv')

        if os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    self.data = list(reader)

                    # 데이터 타입 변환
                    for row in self.data:
                        row['round'] = int(row['round'])
                        row['jo'] = int(row['jo'])

                self.logger.info(f"기존 데이터 로드: {len(self.data)}개 회차")
                return True

            except Exception as e:
                self.logger.error(f"기존 데이터 로드 실패: {e}")
                self.data = []
                return False

        return False

    def get_missing_rounds(self, latest_round):
        """누락된 회차 찾기"""
        existing_rounds = set()
        if self.data:
            existing_rounds = {int(row['round']) for row in self.data}

        all_rounds = set(range(1, latest_round + 1))
        missing_rounds = sorted(all_rounds - existing_rounds)

        return missing_rounds

    def crawl_all(self, start_round=1, end_round=None, delay=1):
        """전체 회차 크롤링"""
        self.logger.info("=== 연금복권 크롤링 시작 ===")

        # 기존 데이터 로드
        self.load_existing_data()

        # 최신 회차 확인
        if end_round is None:
            end_round = self.get_latest_round()

        # 누락된 회차 찾기
        missing_rounds = self.get_missing_rounds(end_round)

        if not missing_rounds:
            self.logger.info("모든 데이터가 최신 상태입니다.")
            return True

        self.logger.info(f"크롤링할 회차: {len(missing_rounds)}개 ({min(missing_rounds)}~{max(missing_rounds)})")

        success_count = 0
        total_count = len(missing_rounds)

        for i, round_num in enumerate(missing_rounds, 1):
            self.logger.info(f"[{i}/{total_count}] {round_num}회 크롤링 중...")

            if self.crawl_round(round_num):
                success_count += 1

                # 중간 저장 (10회차마다)
                if success_count % 10 == 0:
                    self.save_to_csv()
                    self.save_to_json()
                    self.logger.info(f"중간 저장 완료: {success_count}개 회차")

            # 서버 부하 방지
            if delay > 0:
                time.sleep(delay)

        # 최종 저장
        if self.data:
            # 회차순 정렬
            self.data.sort(key=lambda x: int(x['round']))
            self.save_to_csv()
            self.save_to_json()

        self.logger.info(f"=== 크롤링 완료 ===")
        self.logger.info(f"성공: {success_count}/{total_count}개 회차")
        self.logger.info(f"전체 데이터: {len(self.data)}개 회차")

        return success_count > 0


def main():
    """메인 함수"""
    crawler = PensionLotteryCrawler()

    try:
        # 전체 크롤링 실행
        success = crawler.crawl_all(delay=1)

        if success:
            print("\n🎉 크롤링이 성공적으로 완료되었습니다!")
            print(f"📁 저장된 파일:")
            print(f"   - lottery_data/pension_lottery_all.csv")
            print(f"   - lottery_data/pension_lottery_all.json")
            print(f"📊 총 {len(crawler.data)}개 회차 데이터 수집")
        else:
            print("❌ 크롤링 중 오류가 발생했습니다. 로그를 확인해주세요.")

    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 중단되었습니다.")
        crawler.save_to_csv()
        crawler.save_to_json()
        print("현재까지 수집된 데이터를 저장했습니다.")

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")


if __name__ == "__main__":
    main()