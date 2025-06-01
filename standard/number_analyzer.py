#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 번호별 분석 스크립트
- 번호별 출현 횟수 분석
- 번호별 동반 출현 분석
- 번호별 트렌드 분석
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
from itertools import combinations

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class NumberAnalyzer:
    def __init__(self, data_file='lottery_data/pension_lottery_all.csv'):
        """번호 분석기 초기화"""
        self.data_file = data_file
        self.data = None
        self.results_dir = 'analysis_results'
        self.charts_dir = 'charts'

        # 디렉토리 생성
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)

        # 로깅 설정
        log_filename = f"logs/number_analysis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs('logs', exist_ok=True)
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
            self.logger.info(f"데이터 로드 완료: {len(self.data)}개 회차")
            return True
        except Exception as e:
            self.logger.error(f"데이터 로드 실패: {e}")
            return False

    def analyze_number_frequency(self):
        """번호별 출현 빈도 분석"""
        self.logger.info("번호별 출현 빈도 분석 시작")

        # 1등 당첨번호 분석
        first_numbers = {}
        second_numbers = {}

        # 실제 당첨번호 출현 횟수 분석 추가
        winning_numbers_frequency = defaultdict(int)

        for _, row in self.data.iterrows():
            # 실제 6자리 당첨번호 출현 횟수
            first_num = str(row['first_number']).zfill(6)
            winning_numbers_frequency[first_num] += 1

            # 기존 자리별 분석
            for i, digit in enumerate(first_num):
                pos_key = f"1등_{i + 1}자리"
                if pos_key not in first_numbers:
                    first_numbers[pos_key] = Counter()
                first_numbers[pos_key][digit] += 1

            # 2등 당첨번호 (끝자리)
            second_num = str(row['second_number'])
            if second_num not in second_numbers:
                second_numbers[second_num] = 0
            second_numbers[second_num] += 1

        # 결과 저장
        results = {
            'first_numbers': first_numbers,
            'second_numbers': second_numbers,
            'winning_numbers_frequency': dict(winning_numbers_frequency),
            'analysis_date': datetime.now().isoformat()
        }

        # JSON으로 저장
        with open(f'{self.results_dir}/number_frequency.json', 'w', encoding='utf-8') as f:
            # Counter 객체를 딕셔너리로 변환
            json_data = {
                'first_numbers': {k: dict(v) for k, v in first_numbers.items()},
                'second_numbers': second_numbers,
                'winning_numbers_frequency': dict(winning_numbers_frequency),
                'analysis_date': results['analysis_date']
            }
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        self.logger.info("번호별 출현 빈도 분석 완료")
        return results

    def analyze_companion_numbers(self):
        """번호별 동반 출현 분석"""
        self.logger.info("번호별 동반 출현 분석 시작")

        companion_data = defaultdict(lambda: defaultdict(int))
        position_companions = {}

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)

            # 각 자리수별 동반 출현 분석
            for i in range(6):
                pos_key = f"자리{i + 1}"
                if pos_key not in position_companions:
                    position_companions[pos_key] = defaultdict(lambda: defaultdict(int))

                current_digit = first_num[i]

                # 같은 번호의 다른 자리수들과의 동반 출현
                for j in range(6):
                    if i != j:
                        other_digit = first_num[j]
                        companion_data[f"{pos_key}_{current_digit}"][f"자리{j + 1}_{other_digit}"] += 1
                        position_companions[pos_key][current_digit][other_digit] += 1

        # 상위 동반 출현 번호 추출 (각 숫자별 top 5)
        top_companions = {}
        for pos_digit, companions in companion_data.items():
            sorted_companions = sorted(companions.items(), key=lambda x: x[1], reverse=True)
            top_companions[pos_digit] = sorted_companions[:10]  # 상위 10개

        results = {
            'companion_data': dict(companion_data),
            'top_companions': top_companions,
            'position_companions': dict(position_companions),
            'analysis_date': datetime.now().isoformat()
        }

        # JSON으로 저장 (딕셔너리로 변환)
        with open(f'{self.results_dir}/companion_numbers.json', 'w', encoding='utf-8') as f:
            json_data = {
                'companion_data': {k: dict(v) for k, v in companion_data.items()},
                'top_companions': top_companions,
                'position_companions': {k: {k2: dict(v2) for k2, v2 in v.items()} for k, v in
                                        position_companions.items()},
                'analysis_date': results['analysis_date']
            }
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        self.logger.info("번호별 동반 출현 분석 완료")
        return results

    def create_number_frequency_charts(self, frequency_data):
        """번호별 출현 빈도 차트 생성"""
        self.logger.info("번호별 출현 빈도 차트 생성 시작")

        # 1등 번호 각 자리별 출현 빈도 차트
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('1등 당첨번호 자리별 숫자 출현 빈도', fontsize=16, fontweight='bold')

        positions = ['1등_1자리', '1등_2자리', '1등_3자리', '1등_4자리', '1등_5자리', '1등_6자리']

        for idx, pos in enumerate(positions):
            row = idx // 3
            col = idx % 3
            ax = axes[row, col]

            if pos in frequency_data['first_numbers']:
                digits = list(frequency_data['first_numbers'][pos].keys())
                counts = list(frequency_data['first_numbers'][pos].values())

                bars = ax.bar(digits, counts, color='skyblue', alpha=0.7)
                ax.set_title(f'{pos} 출현 빈도', fontweight='bold')
                ax.set_xlabel('숫자')
                ax.set_ylabel('출현 횟수')

                # 막대 위에 값 표시
                for bar, count in zip(bars, counts):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                            str(count), ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/number_frequency_by_position.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 2등 번호 출현 빈도 차트
        plt.figure(figsize=(12, 8))
        second_digits = list(frequency_data['second_numbers'].keys())
        second_counts = list(frequency_data['second_numbers'].values())

        bars = plt.bar(second_digits, second_counts, color='lightcoral', alpha=0.7)
        plt.title('2등 당첨번호 출현 빈도', fontsize=14, fontweight='bold')
        plt.xlabel('끝자리 번호')
        plt.ylabel('출현 횟수')

        # 막대 위에 값 표시
        for bar, count in zip(bars, second_counts):
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     str(count), ha='center', va='bottom')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/second_number_frequency.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 실제 당첨번호 출현 빈도 차트 (상위 30개)
        if 'winning_numbers_frequency' in frequency_data:
            winning_numbers = frequency_data['winning_numbers_frequency']

            # 출현 횟수 기준으로 정렬 (상위 30개)
            sorted_numbers = sorted(winning_numbers.items(), key=lambda x: x[1], reverse=True)[:30]

            if sorted_numbers:
                numbers = [item[0] for item in sorted_numbers]
                counts = [item[1] for item in sorted_numbers]

                plt.figure(figsize=(16, 10))
                bars = plt.bar(range(len(numbers)), counts, color='lightgreen', alpha=0.7)
                plt.title('1등 당첨번호 출현 빈도 (상위 30개)', fontsize=14, fontweight='bold')
                plt.xlabel('당첨번호')
                plt.ylabel('출현 횟수')
                plt.xticks(range(len(numbers)), numbers, rotation=45, ha='right')

                # 막대 위에 값 표시
                for bar, count in zip(bars, counts):
                    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                             str(count), ha='center', va='bottom', fontsize=8)

                plt.tight_layout()
                plt.savefig(f'{self.charts_dir}/winning_numbers_frequency.png', dpi=300, bbox_inches='tight')
                plt.close()

                # 중복 출현된 번호들만 별도 차트
                duplicated_numbers = [(num, count) for num, count in sorted_numbers if count > 1]

                if duplicated_numbers:
                    dup_numbers = [item[0] for item in duplicated_numbers]
                    dup_counts = [item[1] for item in duplicated_numbers]

                    plt.figure(figsize=(14, 8))
                    bars = plt.bar(range(len(dup_numbers)), dup_counts, color='orange', alpha=0.7)
                    plt.title('중복 출현 당첨번호 (2회 이상)', fontsize=14, fontweight='bold')
                    plt.xlabel('당첨번호')
                    plt.ylabel('출현 횟수')
                    plt.xticks(range(len(dup_numbers)), dup_numbers, rotation=45, ha='right')

                    # 막대 위에 값 표시
                    for bar, count in zip(bars, dup_counts):
                        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                                 f'{count}회', ha='center', va='bottom', fontsize=9, fontweight='bold')

                    plt.tight_layout()
                    plt.savefig(f'{self.charts_dir}/duplicated_winning_numbers.png', dpi=300, bbox_inches='tight')
                    plt.close()

        self.logger.info("번호별 출현 빈도 차트 생성 완료")

    def create_companion_heatmap(self, companion_data):
        """동반 출현 히트맵 생성"""
        self.logger.info("동반 출현 히트맵 생성 시작")

        # 각 자리별로 히트맵 생성
        for pos in range(1, 7):
            # 해당 자리의 동반 출현 데이터 추출
            pos_data = defaultdict(lambda: defaultdict(int))

            for key, companions in companion_data['companion_data'].items():
                if key.startswith(f"자리{pos}_"):
                    digit = key.split('_')[1]
                    for comp_key, count in companions.items():
                        comp_pos, comp_digit = comp_key.split('_')
                        pos_data[digit][comp_digit] += count

            if pos_data:
                # 히트맵용 매트릭스 생성
                digits = sorted(set(list(pos_data.keys()) +
                                    [d for subdict in pos_data.values() for d in subdict.keys()]))

                matrix = np.zeros((len(digits), len(digits)))
                for i, d1 in enumerate(digits):
                    for j, d2 in enumerate(digits):
                        if d1 in pos_data and d2 in pos_data[d1]:
                            matrix[i][j] = pos_data[d1][d2]

                # 히트맵 생성
                plt.figure(figsize=(10, 8))
                sns.heatmap(matrix,
                            xticklabels=digits,
                            yticklabels=digits,
                            annot=True,
                            fmt='g',
                            cmap='YlOrRd',
                            cbar_kws={'label': '동반 출현 횟수'})

                plt.title(f'{pos}자리 숫자별 동반 출현 빈도', fontsize=14, fontweight='bold')
                plt.xlabel('동반 출현 숫자')
                plt.ylabel('기준 숫자')
                plt.tight_layout()
                plt.savefig(f'{self.charts_dir}/companion_heatmap_pos{pos}.png', dpi=300, bbox_inches='tight')
                plt.close()

        self.logger.info("동반 출현 히트맵 생성 완료")

    def analyze_number_trends(self):
        """번호별 트렌드 분석 (최근 추세)"""
        self.logger.info("번호별 트렌드 분석 시작")

        # 최근 50회차 데이터로 트렌드 분석
        recent_data = self.data.tail(50)

        trends = {}
        for pos in range(1, 7):
            pos_trends = defaultdict(list)

            for _, row in recent_data.iterrows():
                round_num = row['round']
                first_num = str(row['first_number']).zfill(6)
                digit = first_num[pos - 1]
                pos_trends[digit].append(round_num)

            trends[f'자리{pos}'] = dict(pos_trends)

        # 트렌드 점수 계산 (최근 출현일수록 높은 점수)
        trend_scores = {}
        latest_round = self.data['round'].max()

        for pos, pos_data in trends.items():
            trend_scores[pos] = {}
            for digit, rounds in pos_data.items():
                if rounds:
                    # 최근성 점수 (최근 출현일수록 높은 점수)
                    recent_score = sum([1 / (latest_round - r + 1) for r in rounds])
                    trend_scores[pos][digit] = {
                        'recent_score': recent_score,
                        'last_appearance': max(rounds),
                        'frequency': len(rounds)
                    }

        results = {
            'trends': trends,
            'trend_scores': trend_scores,
            'analysis_period': f"최근 50회차 ({recent_data['round'].min()}회 ~ {recent_data['round'].max()}회)",
            'analysis_date': datetime.now().isoformat()
        }

        # 결과 저장
        with open(f'{self.results_dir}/number_trends.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.logger.info("번호별 트렌드 분석 완료")
        return results

    def create_trend_charts(self, trend_data):
        """트렌드 차트 생성"""
        self.logger.info("트렌드 차트 생성 시작")

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('최근 50회차 자리별 숫자 트렌드 점수', fontsize=16, fontweight='bold')

        for pos_idx in range(6):
            row = pos_idx // 3
            col = pos_idx % 3
            ax = axes[row, col]

            pos_key = f'자리{pos_idx + 1}'
            if pos_key in trend_data['trend_scores']:
                digits = list(trend_data['trend_scores'][pos_key].keys())
                scores = [trend_data['trend_scores'][pos_key][d]['recent_score'] for d in digits]

                bars = ax.bar(digits, scores, color='lightgreen', alpha=0.7)
                ax.set_title(f'{pos_key} 트렌드 점수', fontweight='bold')
                ax.set_xlabel('숫자')
                ax.set_ylabel('트렌드 점수')

                # 막대 위에 값 표시
                for bar, score in zip(bars, scores):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                            f'{score:.2f}', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/number_trends.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("트렌드 차트 생성 완료")

    def generate_summary_report(self, frequency_data, companion_data, trend_data):
        """종합 분석 보고서 생성"""
        self.logger.info("종합 분석 보고서 생성 시작")

        report = {
            'analysis_summary': {
                'total_rounds': len(self.data),
                'analysis_date': datetime.now().isoformat(),
                'data_range': f"{self.data['round'].min()}회 ~ {self.data['round'].max()}회"
            },
            'frequency_analysis': {
                'most_frequent_by_position': {},
                'least_frequent_by_position': {},
                'most_frequent_second': max(frequency_data['second_numbers'].items(), key=lambda x: x[1]),
                'least_frequent_second': min(frequency_data['second_numbers'].items(), key=lambda x: x[1])
            },
            'winning_numbers_analysis': {
                'total_unique_numbers': 0,
                'duplicated_numbers_count': 0,
                'most_frequent_winning_number': None,
                'duplicated_numbers': []
            },
            'trend_analysis': {
                'hot_numbers_by_position': {},
                'cold_numbers_by_position': {}
            },
            'companion_analysis': {
                'strongest_companions': {},
                'insights': []
            }
        }

        # 자리별 최다/최소 출현 번호
        for pos_key, pos_data in frequency_data['first_numbers'].items():
            most_freq = max(pos_data.items(), key=lambda x: x[1])
            least_freq = min(pos_data.items(), key=lambda x: x[1])
            report['frequency_analysis']['most_frequent_by_position'][pos_key] = most_freq
            report['frequency_analysis']['least_frequent_by_position'][pos_key] = least_freq

        # 당첨번호 출현 횟수 분석
        if 'winning_numbers_frequency' in frequency_data:
            winning_numbers = frequency_data['winning_numbers_frequency']
            report['winning_numbers_analysis']['total_unique_numbers'] = len(winning_numbers)

            # 중복 출현된 번호들
            duplicated = [(num, count) for num, count in winning_numbers.items() if count > 1]
            report['winning_numbers_analysis']['duplicated_numbers_count'] = len(duplicated)
            report['winning_numbers_analysis']['duplicated_numbers'] = duplicated

            if winning_numbers:
                most_frequent = max(winning_numbers.items(), key=lambda x: x[1])
                report['winning_numbers_analysis']['most_frequent_winning_number'] = most_frequent

        # 자리별 핫/콜드 번호 (트렌드 점수 기준)
        for pos_key, pos_scores in trend_data['trend_scores'].items():
            if pos_scores:
                hot_number = max(pos_scores.items(), key=lambda x: x[1]['recent_score'])
                cold_number = min(pos_scores.items(), key=lambda x: x[1]['recent_score'])
                report['trend_analysis']['hot_numbers_by_position'][pos_key] = hot_number
                report['trend_analysis']['cold_numbers_by_position'][pos_key] = cold_number

        # 인사이트 생성
        insights = [
            f"총 {len(self.data)}회차 데이터를 분석했습니다.",
            f"2등 당첨번호 중 '{report['frequency_analysis']['most_frequent_second'][0]}'이 {report['frequency_analysis']['most_frequent_second'][1]}회로 가장 많이 출현했습니다.",
            f"총 {report['winning_numbers_analysis']['total_unique_numbers']}개의 서로 다른 당첨번호가 나왔습니다.",
        ]

        if report['winning_numbers_analysis']['duplicated_numbers_count'] > 0:
            insights.append(f"{report['winning_numbers_analysis']['duplicated_numbers_count']}개의 번호가 2회 이상 중복 출현했습니다.")

            if report['winning_numbers_analysis']['most_frequent_winning_number']:
                most_freq_num, most_freq_count = report['winning_numbers_analysis']['most_frequent_winning_number']
                insights.append(f"가장 많이 나온 당첨번호는 '{most_freq_num}'으로 {most_freq_count}회 출현했습니다.")
        else:
            insights.append("모든 당첨번호가 단 1회씩만 출현했습니다.")

        insights.extend([
            "각 자리별로 출현 빈도와 최근 트렌드가 다르게 나타납니다.",
            "동반 출현 패턴을 통해 특정 숫자 조합의 경향을 파악할 수 있습니다."
        ])

        report['companion_analysis']['insights'] = insights

        # 보고서 저장
        with open(f'{self.results_dir}/number_analysis_summary.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info("종합 분석 보고서 생성 완료")
        return report

    def run_full_analysis(self):
        """전체 분석 실행"""
        self.logger.info("=== 번호별 분석 시작 ===")

        # 데이터 로드
        if not self.load_data():
            return False

        try:
            # 1. 번호별 출현 빈도 분석
            frequency_data = self.analyze_number_frequency()
            self.create_number_frequency_charts(frequency_data)

            # 2. 번호별 동반 출현 분석
            companion_data = self.analyze_companion_numbers()
            self.create_companion_heatmap(companion_data)

            # 3. 번호별 트렌드 분석
            trend_data = self.analyze_number_trends()
            self.create_trend_charts(trend_data)

            # 4. 종합 보고서 생성
            summary_report = self.generate_summary_report(frequency_data, companion_data, trend_data)

            self.logger.info("=== 번호별 분석 완료 ===")
            print("분석이 완료되었습니다!")
            print(f"결과 파일: {self.results_dir}/")
            print(f"차트 파일: {self.charts_dir}/")

            return True

        except Exception as e:
            self.logger.error(f"분석 중 오류 발생: {e}")
            return False


def main():
    """메인 함수"""
    analyzer = NumberAnalyzer()
    success = analyzer.run_full_analysis()

    if success:
        print("\n🎉 번호별 분석이 성공적으로 완료되었습니다!")
        print("\n📁 생성된 파일들:")
        print("- analysis_results/number_frequency.json")
        print("- analysis_results/companion_numbers.json")
        print("- analysis_results/number_trends.json")
        print("- analysis_results/number_analysis_summary.json")
        print("- charts/number_frequency_by_position.png")
        print("- charts/second_number_frequency.png")
        print("- charts/winning_numbers_frequency.png (당첨번호 출현 빈도)")
        print("- charts/duplicated_winning_numbers.png (중복 출현 번호)")
        print("- charts/companion_heatmap_pos*.png")
        print("- charts/number_trends.png")
    else:
        print("❌ 분석 중 오류가 발생했습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()