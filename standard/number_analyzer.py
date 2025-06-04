#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 번호별 분석 스크립트 (수정된 버전)
- 각 자리별 숫자 출현 빈도 분석
- 동반 출현 패턴 분석
- 번호별 트렌드 점수 계산
- 상세 히트맵 생성
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
from datetime import datetime
from collections import defaultdict, Counter
import os
import sys
import platform


# 한글 폰트 설정
def setup_matplotlib_font():
    """플랫폼에 따른 matplotlib 폰트 설정"""
    system = platform.system()

    if system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = ['Apple SD Gothic Neo', 'DejaVu Sans']
    elif system == 'Windows':  # Windows
        plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans']
    else:  # Linux
        plt.rcParams['font.family'] = ['DejaVu Sans']

    plt.rcParams['axes.unicode_minus'] = False


class NumberAnalyzer:
    def __init__(self, lottery_type="720", data_file=None):
        """번호 분석기 초기화"""
        self.lottery_type = lottery_type

        if data_file is None:
            data_file = f'lottery_data/pension_lottery_{lottery_type}_all.csv'

        self.data_file = data_file
        self.data = None
        self.results_dir = 'analysis_results'
        self.charts_dir = 'charts'

        # 디렉토리 생성
        for directory in [self.results_dir, self.charts_dir, 'logs']:
            try:
                os.makedirs(directory, exist_ok=True)
            except PermissionError:
                print(f"경고: {directory} 디렉토리 생성 권한이 없습니다.")
            except Exception as e:
                print(f"경고: {directory} 디렉토리 생성 실패: {e}")

        # 폰트 설정
        setup_matplotlib_font()

        # 로깅 설정
        log_filename = f"logs/number_analysis_{lottery_type}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_data(self):
        """데이터 로드"""
        try:
            self.data = pd.read_csv(self.data_file, encoding='utf-8')

            # 데이터 타입 안전하게 변환
            self.data['round'] = pd.to_numeric(self.data['round'], errors='coerce')
            self.data['jo'] = pd.to_numeric(self.data['jo'], errors='coerce')

            # NaN 값 제거
            self.data = self.data.dropna(subset=['round', 'jo'])

            # 데이터 타입 변환
            self.data['round'] = self.data['round'].astype(int)
            self.data['jo'] = self.data['jo'].astype(int)

            self.logger.info(f"데이터 로드 완료: {len(self.data)}개 회차")
            return True
        except FileNotFoundError:
            self.logger.error(f"데이터 파일을 찾을 수 없습니다: {self.data_file}")
            return False
        except Exception as e:
            self.logger.error(f"데이터 로드 실패: {e}")
            return False

    def analyze_number_frequency_by_position(self):
        """자리별 숫자 출현 빈도 분석"""
        self.logger.info("자리별 숫자 출현 빈도 분석 시작")

        position_frequency = {}

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)

            for pos, digit in enumerate(first_num, 1):
                key = f"자리{pos}"
                if key not in position_frequency:
                    position_frequency[key] = defaultdict(int)
                position_frequency[key][digit] += 1

        # defaultdict를 일반 딕셔너리로 변환
        position_frequency = {k: dict(v) for k, v in position_frequency.items()}

        # 결과 저장
        with open(f'{self.results_dir}/number_frequency.json', 'w', encoding='utf-8') as f:
            json.dump(position_frequency, f, ensure_ascii=False, indent=2)

        self.logger.info("자리별 숫자 출현 빈도 분석 완료")
        return position_frequency

    def analyze_companion_numbers(self):
        """동반 출현 패턴 분석"""
        self.logger.info("동반 출현 패턴 분석 시작")

        companion_data = defaultdict(lambda: defaultdict(int))

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)
            digits = [d for d in first_num]

            # 각 자리별로 다른 자리와의 동반 출현 분석
            for i, digit_i in enumerate(digits, 1):
                for j, digit_j in enumerate(digits, 1):
                    if i != j:  # 같은 자리는 제외
                        key_i = f"자리{i}_{digit_i}"
                        key_j = f"자리{j}_{digit_j}"
                        companion_data[key_i][key_j] += 1

        # defaultdict를 일반 딕셔너리로 변환
        companion_data = {k: dict(v) for k, v in companion_data.items()}

        results = {
            'companion_data': companion_data,
            'analysis_summary': {
                'total_combinations': len(companion_data),
                'analysis_date': datetime.now().isoformat()
            }
        }

        # 결과 저장
        with open(f'{self.results_dir}/companion_numbers.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.logger.info("동반 출현 패턴 분석 완료")
        return results

    def calculate_number_trends(self):
        """번호별 트렌드 점수 계산"""
        self.logger.info("번호별 트렌드 점수 계산 시작")

        trend_scores = {}

        # 최근 30회차와 이전 30회차 비교
        if len(self.data) < 60:
            self.logger.warning("데이터가 부족하여 트렌드 분석을 건너뜁니다.")
            return {}

        recent_data = self.data.tail(30)
        previous_data = self.data.iloc[-60:-30]

        for pos in range(1, 7):
            trend_scores[f'자리{pos}'] = {}

            # 최근 30회차 빈도
            recent_freq = defaultdict(int)
            for _, row in recent_data.iterrows():
                digit = str(row['first_number']).zfill(6)[pos - 1]
                recent_freq[digit] += 1

            # 이전 30회차 빈도
            previous_freq = defaultdict(int)
            for _, row in previous_data.iterrows():
                digit = str(row['first_number']).zfill(6)[pos - 1]
                previous_freq[digit] += 1

            # 트렌드 점수 계산
            for digit in '0123456789':
                recent_count = recent_freq[digit]
                previous_count = previous_freq[digit] if previous_freq[digit] > 0 else 1

                # 트렌드 점수 = (최근 빈도 / 이전 빈도) * 100
                trend_score = (recent_count / previous_count) * 100
                trend_scores[f'자리{pos}'][digit] = round(trend_score, 2)

        # 결과 저장
        with open(f'{self.results_dir}/number_trends.json', 'w', encoding='utf-8') as f:
            json.dump(trend_scores, f, ensure_ascii=False, indent=2)

        self.logger.info("번호별 트렌드 점수 계산 완료")
        return trend_scores

    def create_number_frequency_chart(self, frequency_data):
        """자리별 숫자 출현 빈도 차트 생성"""
        self.logger.info("자리별 숫자 출현 빈도 차트 생성 시작")

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for i, (position, data) in enumerate(frequency_data.items()):
            if i >= 6:
                break

            digits = sorted(data.keys())
            counts = [data[digit] for digit in digits]

            colors = plt.cm.Set3(np.linspace(0, 1, len(digits)))

            bars = axes[i].bar(digits, counts, color=colors, alpha=0.8)
            axes[i].set_title(f'{position} 숫자 출현 빈도', fontweight='bold')
            axes[i].set_xlabel('숫자')
            axes[i].set_ylabel('출현 횟수')

            # 막대 위에 값 표시
            for bar, count in zip(bars, counts):
                axes[i].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                             str(count), ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/number_frequency_by_position.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("자리별 숫자 출현 빈도 차트 생성 완료")

    def create_companion_heatmap(self, companion_data):
        """동반 출현 히트맵 생성 (수정된 버전)"""
        self.logger.info("동반 출현 히트맵 생성 시작")

        # 각 자리별로 히트맵 생성
        for pos in range(1, 7):
            try:
                # 해당 자리의 동반 출현 데이터 추출
                pos_data = defaultdict(lambda: defaultdict(int))

                for key, companions in companion_data['companion_data'].items():
                    if key.startswith(f"자리{pos}_"):
                        digit = key.split('_')[1]
                        for comp_key, count in companions.items():
                            comp_parts = comp_key.split('_')
                            if len(comp_parts) >= 2:
                                comp_digit = comp_parts[1]
                                pos_data[digit][comp_digit] += count

                if pos_data:
                    # 히트맵용 매트릭스 생성
                    all_digits = set()
                    for d1_dict in pos_data.values():
                        all_digits.update(d1_dict.keys())
                    all_digits.update(pos_data.keys())

                    digits = sorted(list(all_digits))

                    if len(digits) > 0:
                        matrix = np.zeros((len(digits), len(digits)))
                        for i, d1 in enumerate(digits):
                            for j, d2 in enumerate(digits):
                                if d1 in pos_data and d2 in pos_data[d1]:
                                    matrix[i][j] = pos_data[d1][d2]

                        # 히트맵 생성
                        plt.figure(figsize=(10, 8))

                        # 데이터가 있는 경우에만 히트맵 생성
                        if matrix.max() > 0:
                            sns.heatmap(matrix,
                                        xticklabels=digits,
                                        yticklabels=digits,
                                        annot=True,
                                        fmt='g',
                                        cmap='YlOrRd',
                                        cbar_kws={'label': '동반 출현 횟수'})
                        else:
                            # 데이터가 없는 경우 빈 히트맵
                            plt.text(0.5, 0.5, f'{pos}자리 동반 출현 데이터 없음',
                                     ha='center', va='center', transform=plt.gca().transAxes,
                                     fontsize=16, color='gray')

                        plt.title(f'{pos}자리 숫자별 동반 출현 빈도', fontsize=14, fontweight='bold')
                        plt.xlabel('동반 출현 숫자')
                        plt.ylabel('기준 숫자')
                        plt.tight_layout()
                        plt.savefig(f'{self.charts_dir}/companion_heatmap_pos{pos}.png',
                                    dpi=300, bbox_inches='tight')
                        plt.close()
                    else:
                        self.logger.warning(f"{pos}자리 동반 출현 데이터가 없습니다.")
                else:
                    self.logger.warning(f"{pos}자리 동반 출현 데이터가 없습니다.")

            except Exception as e:
                self.logger.error(f"{pos}자리 히트맵 생성 실패: {e}")
                plt.close()  # 오류 시 플롯 정리

        self.logger.info("동반 출현 히트맵 생성 완료")

    def create_trend_chart(self, trend_data):
        """트렌드 점수 차트 생성"""
        self.logger.info("트렌드 점수 차트 생성 시작")

        if not trend_data:
            self.logger.warning("트렌드 데이터가 없어 차트 생성을 건너뜁니다.")
            return

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for i, (position, scores) in enumerate(trend_data.items()):
            if i >= 6:
                break

            digits = sorted(scores.keys())
            trend_scores = [scores[digit] for digit in digits]

            # 색상 설정 (트렌드에 따라)
            colors = ['red' if score > 100 else 'blue' if score < 100 else 'gray' for score in trend_scores]

            bars = axes[i].bar(digits, trend_scores, color=colors, alpha=0.7)
            axes[i].set_title(f'{position} 트렌드 점수', fontweight='bold')
            axes[i].set_xlabel('숫자')
            axes[i].set_ylabel('트렌드 점수')
            axes[i].axhline(y=100, color='black', linestyle='--', alpha=0.5)

            # 막대 위에 값 표시
            for bar, score in zip(bars, trend_scores):
                axes[i].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                             f'{score:.1f}', ha='center', va='bottom', fontsize=8)

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/number_trends.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("트렌드 점수 차트 생성 완료")

    def generate_analysis_summary(self, frequency_data, companion_data, trend_data):
        """번호 분석 요약 생성"""
        self.logger.info("번호 분석 요약 생성 시작")

        # 각 자리별 최다 출현 숫자 찾기
        most_frequent_by_position = {}
        for position, data in frequency_data.items():
            if data:
                most_frequent_digit = max(data, key=data.get)
                most_frequent_by_position[position] = {
                    'digit': most_frequent_digit,
                    'count': data[most_frequent_digit]
                }

        # 트렌드가 높은 숫자 찾기
        hot_numbers = {}
        if trend_data:
            for position, scores in trend_data.items():
                if scores:
                    hot_digit = max(scores, key=scores.get)
                    hot_numbers[position] = {
                        'digit': hot_digit,
                        'score': scores[hot_digit]
                    }

        summary = {
            'analysis_info': {
                'total_rounds': len(self.data),
                'lottery_type': self.lottery_type,
                'analysis_date': datetime.now().isoformat()
            },
            'most_frequent_by_position': most_frequent_by_position,
            'hot_numbers_by_trend': hot_numbers,
            'total_companion_patterns': len(companion_data.get('companion_data', {})),
            'key_insights': []
        }

        # 주요 인사이트 생성
        insights = [
            f"연금복권{self.lottery_type} 총 {len(self.data)}회차 번호별 분석 완료",
            f"총 {len(companion_data.get('companion_data', {}))}개의 동반 출현 패턴 발견"
        ]

        # 자리별 최다 출현 숫자 인사이트
        for position, info in most_frequent_by_position.items():
            insights.append(f"{position}에서 '{info['digit']}'이 {info['count']}회로 가장 많이 출현")

        summary['key_insights'] = insights

        # 결과 저장
        with open(f'{self.results_dir}/number_analysis_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.logger.info("번호 분석 요약 생성 완료")
        return summary

    def run_full_analysis(self):
        """전체 번호 분석 실행"""
        self.logger.info(f"=== 연금복권{self.lottery_type} 번호별 분석 시작 ===")

        # 데이터 로드
        if not self.load_data():
            return False

        try:
            # 1. 자리별 숫자 출현 빈도 분석
            frequency_data = self.analyze_number_frequency_by_position()
            self.create_number_frequency_chart(frequency_data)

            # 2. 동반 출현 패턴 분석
            companion_data = self.analyze_companion_numbers()
            self.create_companion_heatmap(companion_data)

            # 3. 번호별 트렌드 점수 계산
            trend_data = self.calculate_number_trends()
            self.create_trend_chart(trend_data)

            # 4. 분석 요약 생성
            summary = self.generate_analysis_summary(frequency_data, companion_data, trend_data)

            self.logger.info("=== 번호별 분석 완료 ===")
            print(f"연금복권{self.lottery_type} 번호별 분석이 완료되었습니다!")
            print(f"결과 파일: {self.results_dir}/")
            print(f"차트 파일: {self.charts_dir}/")

            return True

        except Exception as e:
            self.logger.error(f"분석 중 오류 발생: {e}")
            return False


def main():
    """메인 함수"""
    # 환경변수에서 연금복권 타입 확인
    lottery_type = os.environ.get('LOTTERY_TYPE', '720')

    # 명령행 인수 처리
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == '--type' and i + 1 < len(sys.argv):
                lottery_type = sys.argv[i + 1]

    # 대화형 모드
    if lottery_type not in ['720', '520']:
        print("연금복권 번호별 분석을 시작합니다.")
        print("1. 연금복권720+ 분석")
        print("2. 연금복권520 분석")

        choice = input("선택하세요 (1 또는 2, 기본값: 1): ").strip()

        if choice == "2":
            lottery_type = "520"
        else:
            lottery_type = "720"

    analyzer = NumberAnalyzer(lottery_type)
    success = analyzer.run_full_analysis()

    if success:
        print(f"\n🎉 연금복권{lottery_type} 번호별 분석이 성공적으로 완료되었습니다!")
        print("\n📁 생성된 파일들:")
        print("- analysis_results/number_frequency.json")
        print("- analysis_results/companion_numbers.json")
        print("- analysis_results/number_trends.json")
        print("- analysis_results/number_analysis_summary.json")
        print("- charts/number_frequency_by_position.png")
        print("- charts/companion_heatmap_pos*.png")
        print("- charts/number_trends.png")
    else:
        print("❌ 분석 중 오류가 발생했습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()