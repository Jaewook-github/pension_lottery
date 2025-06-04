#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 기본 분석 스크립트 (수정된 버전)
- 조별 출현 빈도 분석
- 최근 트렌드 분석
- 2등 끝자리 번호 패턴 분석
- 기본 통계 생성
"""

import json
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import logging
from datetime import datetime
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


class PensionLotteryAnalyzer:
    def __init__(self, lottery_type="720", data_file=None):
        """기본 분석기 초기화"""
        self.lottery_type = lottery_type

        # 기본 데이터 파일 경로 설정
        if data_file is None:
            data_file = f'lottery_data/pension_lottery_{lottery_type}_all.csv'

        self.data_file = data_file
        self.data = None
        self.results_dir = 'analysis_results'
        self.charts_dir = 'charts'

        # 디렉토리 생성 (더 안전하게)
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
        log_filename = f"logs/basic_analysis_{lottery_type}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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

    def analyze_jo_frequency(self):
        """조별 출현 빈도 분석"""
        self.logger.info("조별 출현 빈도 분석 시작")

        jo_counts = self.data['jo'].value_counts().sort_index()
        jo_percentages = (jo_counts / len(self.data) * 100).round(2)

        # 최근 50회차 트렌드
        recent_data = self.data.tail(50)
        recent_jo_counts = recent_data['jo'].value_counts().sort_index()

        results = {
            'jo_frequency': jo_counts.to_dict(),
            'jo_percentages': jo_percentages.to_dict(),
            'recent_jo_frequency': recent_jo_counts.to_dict(),
            'most_frequent_jo': {
                'jo': int(jo_counts.idxmax()),
                'count': int(jo_counts.max()),
                'percentage': float(jo_percentages.max())
            },
            'least_frequent_jo': {
                'jo': int(jo_counts.idxmin()),
                'count': int(jo_counts.min()),
                'percentage': float(jo_percentages.min())
            }
        }

        self.logger.info("조별 출현 빈도 분석 완료")
        return results

    def analyze_second_number_pattern(self):
        """2등 끝자리 번호 패턴 분석"""
        self.logger.info("2등 끝자리 번호 패턴 분석 시작")

        # 2등 번호의 끝자리 분석
        second_last_digits = self.data['second_number'].astype(str).str[-1]
        digit_counts = second_last_digits.value_counts().sort_index()
        digit_percentages = (digit_counts / len(self.data) * 100).round(2)

        results = {
            'last_digit_frequency': digit_counts.to_dict(),
            'last_digit_percentages': digit_percentages.to_dict(),
            'most_frequent_digit': {
                'digit': digit_counts.idxmax(),
                'count': int(digit_counts.max()),
                'percentage': float(digit_percentages.max())
            },
            'least_frequent_digit': {
                'digit': digit_counts.idxmin(),
                'count': int(digit_counts.min()),
                'percentage': float(digit_percentages.min())
            }
        }

        self.logger.info("2등 끝자리 번호 패턴 분석 완료")
        return results

    def analyze_trends(self):
        """최근 트렌드 분석"""
        self.logger.info("최근 트렌드 분석 시작")

        # 최근 50회차와 전체 데이터 비교
        recent_data = self.data.tail(50)

        # 조별 트렌드
        overall_jo_freq = self.data['jo'].value_counts(normalize=True).sort_index()
        recent_jo_freq = recent_data['jo'].value_counts(normalize=True).sort_index()

        trend_changes = {}
        for jo in range(1, 6):
            overall_pct = overall_jo_freq.get(jo, 0) * 100
            recent_pct = recent_jo_freq.get(jo, 0) * 100
            change = recent_pct - overall_pct

            trend_changes[jo] = {
                'overall_percentage': round(overall_pct, 2),
                'recent_percentage': round(recent_pct, 2),
                'change': round(change, 2),
                'trend': 'up' if change > 2 else ('down' if change < -2 else 'stable')
            }

        results = {
            'trend_period': f"최근 50회차 ({recent_data['round'].min()}회 ~ {recent_data['round'].max()}회)",
            'jo_trends': trend_changes,
            'analysis_date': datetime.now().isoformat()
        }

        self.logger.info("최근 트렌드 분석 완료")
        return results

    def create_jo_frequency_chart(self, jo_data):
        """조별 출현 빈도 차트 생성"""
        self.logger.info("조별 출현 빈도 차트 생성 시작")

        # 전체 조별 출현 빈도
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 차트 1: 전체 조별 출현 빈도
        jos = list(jo_data['jo_frequency'].keys())
        counts = list(jo_data['jo_frequency'].values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57']

        bars1 = ax1.bar(jos, counts, color=colors, alpha=0.8)
        ax1.set_title('조별 출현 빈도 (전체)', fontsize=14, fontweight='bold', pad=20)
        ax1.set_xlabel('조')
        ax1.set_ylabel('출현 횟수')
        ax1.set_xticks(jos)
        ax1.set_xticklabels([f'{jo}조' for jo in jos])

        # 막대 위에 값 표시
        for bar, count in zip(bars1, counts):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     str(count), ha='center', va='bottom', fontweight='bold')

        # 차트 2: 최근 조별 출현 빈도
        recent_jos = list(jo_data['recent_jo_frequency'].keys())
        recent_counts = list(jo_data['recent_jo_frequency'].values())

        bars2 = ax2.bar(recent_jos, recent_counts, color=colors, alpha=0.8)
        ax2.set_title('조별 출현 빈도 (최근 50회차)', fontsize=14, fontweight='bold', pad=20)
        ax2.set_xlabel('조')
        ax2.set_ylabel('출현 횟수')
        ax2.set_xticks(recent_jos)
        ax2.set_xticklabels([f'{jo}조' for jo in recent_jos])

        # 막대 위에 값 표시
        for bar, count in zip(bars2, recent_counts):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                     str(count), ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/jo_frequency.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 최근 트렌드만 별도 저장
        plt.figure(figsize=(10, 6))
        bars = plt.bar(recent_jos, recent_counts, color=colors, alpha=0.8)
        plt.title('최근 조별 출현 빈도 (50회차)', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('조')
        plt.ylabel('출현 횟수')
        plt.xticks(recent_jos, [f'{jo}조' for jo in recent_jos])

        for bar, count in zip(bars, recent_counts):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                     str(count), ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/recent_jo_frequency.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("조별 출현 빈도 차트 생성 완료")

    def create_second_number_chart(self, second_data):
        """2등 끝자리 번호 차트 생성"""
        self.logger.info("2등 끝자리 번호 차트 생성 시작")

        plt.figure(figsize=(12, 8))

        digits = list(second_data['last_digit_frequency'].keys())
        counts = list(second_data['last_digit_frequency'].values())

        # 색상 그라데이션
        colors = plt.cm.Set3(np.linspace(0, 1, len(digits)))

        bars = plt.bar(digits, counts, color=colors, alpha=0.8)
        plt.title('2등 당첨번호 끝자리 출현 빈도', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('끝자리 번호')
        plt.ylabel('출현 횟수')

        # 막대 위에 값 표시
        for bar, count in zip(bars, counts):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     str(count), ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/last_digit_frequency.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("2등 끝자리 번호 차트 생성 완료")

    def generate_statistics_report(self, jo_data, second_data, trend_data):
        """통계 보고서 생성"""
        self.logger.info("통계 보고서 생성 시작")

        report = {
            'analysis_summary': {
                'total_rounds': len(self.data),
                'data_range': f"{self.data['round'].min()}회 ~ {self.data['round'].max()}회",
                'lottery_type': self.lottery_type,
                'analysis_date': datetime.now().isoformat()
            },
            'jo_analysis': {
                'total_jos': len(jo_data['jo_frequency']),
                'most_frequent_jo': jo_data['most_frequent_jo'],
                'least_frequent_jo': jo_data['least_frequent_jo'],
                'jo_distribution': jo_data['jo_frequency'],
                'jo_percentages': jo_data['jo_percentages']
            },
            'second_number_analysis': {
                'most_frequent_digit': second_data['most_frequent_digit'],
                'least_frequent_digit': second_data['least_frequent_digit'],
                'digit_distribution': second_data['last_digit_frequency'],
                'digit_percentages': second_data['last_digit_percentages']
            },
            'trend_analysis': trend_data,
            'key_insights': []
        }

        # 주요 인사이트 생성
        insights = [
            f"총 {len(self.data)}회차 데이터를 분석했습니다.",
            f"가장 많이 나온 조는 {jo_data['most_frequent_jo']['jo']}조로 {jo_data['most_frequent_jo']['count']}회 ({jo_data['most_frequent_jo']['percentage']}%) 출현했습니다.",
            f"2등 당첨번호 끝자리 중 '{second_data['most_frequent_digit']['digit']}'이 {second_data['most_frequent_digit']['count']}회로 가장 많이 출현했습니다."
        ]

        # 트렌드 인사이트 추가
        for jo, trend_info in trend_data['jo_trends'].items():
            if trend_info['trend'] == 'up':
                insights.append(f"{jo}조는 최근 상승 추세입니다 (+{trend_info['change']}%).")
            elif trend_info['trend'] == 'down':
                insights.append(f"{jo}조는 최근 하락 추세입니다 ({trend_info['change']}%).")

        report['key_insights'] = insights

        # 보고서 저장
        with open(f'{self.results_dir}/statistics_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info("통계 보고서 생성 완료")
        return report

    def run_full_analysis(self):
        """전체 분석 실행"""
        self.logger.info(f"=== 연금복권{self.lottery_type} 기본 분석 시작 ===")

        # 데이터 로드
        if not self.load_data():
            return False

        try:
            # 1. 조별 출현 빈도 분석
            jo_data = self.analyze_jo_frequency()
            self.create_jo_frequency_chart(jo_data)

            # 2. 2등 끝자리 번호 패턴 분석
            second_data = self.analyze_second_number_pattern()
            self.create_second_number_chart(second_data)

            # 3. 최근 트렌드 분석
            trend_data = self.analyze_trends()

            # 4. 통계 보고서 생성
            report = self.generate_statistics_report(jo_data, second_data, trend_data)

            self.logger.info("=== 기본 분석 완료 ===")
            print(f"연금복권{self.lottery_type} 기본 분석이 완료되었습니다!")
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
        print("연금복권 기본 분석을 시작합니다.")
        print("1. 연금복권720+ 분석")
        print("2. 연금복권520 분석")

        choice = input("선택하세요 (1 또는 2, 기본값: 1): ").strip()

        if choice == "2":
            lottery_type = "520"
        else:
            lottery_type = "720"

    analyzer = PensionLotteryAnalyzer(lottery_type)
    success = analyzer.run_full_analysis()

    if success:
        print(f"\n🎉 연금복권{lottery_type} 기본 분석이 성공적으로 완료되었습니다!")
        print("\n📁 생성된 파일들:")
        print("- analysis_results/statistics_report.json")
        print("- charts/jo_frequency.png")
        print("- charts/recent_jo_frequency.png")
        print("- charts/last_digit_frequency.png")
    else:
        print("❌ 분석 중 오류가 발생했습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()