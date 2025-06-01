#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 고급 패턴 분석 스크립트
- 조합 패턴 분석
- 연속/건너뛰기 패턴 분석
- 홀수/짝수 분포 분석
- 번호 간격 패턴 분석
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


class PatternAnalyzer:
    def __init__(self, data_file='lottery_data/pension_lottery_all.csv'):
        """고급 패턴 분석기 초기화"""
        self.data_file = data_file
        self.data = None
        self.results_dir = 'analysis_results'
        self.charts_dir = 'charts'

        # 디렉토리 생성
        os.makedirs(self.results_dir, exist_ok=True)
        os.makedirs(self.charts_dir, exist_ok=True)

        # 로깅 설정
        log_filename = f"logs/pattern_analysis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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

    def analyze_odd_even_patterns(self):
        """홀수/짝수 분포 분석"""
        self.logger.info("홀수/짝수 분포 분석 시작")

        odd_even_data = {
            'by_position': {},
            'by_round': [],
            'overall_stats': {}
        }

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)
            round_data = {
                'round': row['round'],
                'positions': {},
                'odd_count': 0,
                'even_count': 0
            }

            # 각 자리별 홀수/짝수 분석
            for i, digit in enumerate(first_num):
                pos_key = f'pos_{i + 1}'
                digit_int = int(digit)
                is_odd = digit_int % 2 == 1

                if pos_key not in odd_even_data['by_position']:
                    odd_even_data['by_position'][pos_key] = {'odd': 0, 'even': 0}

                if is_odd:
                    odd_even_data['by_position'][pos_key]['odd'] += 1
                    round_data['odd_count'] += 1
                else:
                    odd_even_data['by_position'][pos_key]['even'] += 1
                    round_data['even_count'] += 1

                round_data['positions'][pos_key] = 'odd' if is_odd else 'even'

            odd_even_data['by_round'].append(round_data)

        # 전체 통계
        total_rounds = len(self.data)
        total_digits = total_rounds * 6
        total_odd = sum([pos_data['odd'] for pos_data in odd_even_data['by_position'].values()])
        total_even = sum([pos_data['even'] for pos_data in odd_even_data['by_position'].values()])

        odd_even_data['overall_stats'] = {
            'total_digits': total_digits,
            'total_odd': total_odd,
            'total_even': total_even,
            'odd_percentage': (total_odd / total_digits) * 100,
            'even_percentage': (total_even / total_digits) * 100
        }

        # 패턴 분석 (연속된 홀수/짝수)
        pattern_counts = defaultdict(int)
        for round_data in odd_even_data['by_round']:
            pattern = ''.join([round_data['positions'][f'pos_{i + 1}'][0].upper() for i in range(6)])
            pattern_counts[pattern] += 1

        odd_even_data['pattern_counts'] = dict(sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:20])

        # 결과 저장
        with open(f'{self.results_dir}/odd_even_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(odd_even_data, f, ensure_ascii=False, indent=2)

        self.logger.info("홀수/짝수 분포 분석 완료")
        return odd_even_data

    def analyze_consecutive_patterns(self):
        """연속/건너뛰기 패턴 분석"""
        self.logger.info("연속/건너뛰기 패턴 분석 시작")

        consecutive_data = {
            'ascending_sequences': defaultdict(int),
            'descending_sequences': defaultdict(int),
            'same_digit_sequences': defaultdict(int),
            'gap_patterns': defaultdict(int),
            'by_round': []
        }

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)
            digits = [int(d) for d in first_num]

            round_analysis = {
                'round': row['round'],
                'digits': digits,
                'ascending_seq': 0,
                'descending_seq': 0,
                'same_seq': 0,
                'gaps': []
            }

            # 연속 패턴 분석
            asc_count = desc_count = same_count = 0
            current_asc = current_desc = current_same = 1

            for i in range(1, 6):
                # 상승 연속
                if digits[i] == digits[i - 1] + 1:
                    current_asc += 1
                else:
                    if current_asc >= 2:
                        consecutive_data['ascending_sequences'][current_asc] += 1
                        asc_count = max(asc_count, current_asc)
                    current_asc = 1

                # 하강 연속
                if digits[i] == digits[i - 1] - 1:
                    current_desc += 1
                else:
                    if current_desc >= 2:
                        consecutive_data['descending_sequences'][current_desc] += 1
                        desc_count = max(desc_count, current_desc)
                    current_desc = 1

                # 동일 숫자 연속
                if digits[i] == digits[i - 1]:
                    current_same += 1
                else:
                    if current_same >= 2:
                        consecutive_data['same_digit_sequences'][current_same] += 1
                        same_count = max(same_count, current_same)
                    current_same = 1

                # 간격 분석
                gap = abs(digits[i] - digits[i - 1])
                round_analysis['gaps'].append(gap)
                consecutive_data['gap_patterns'][gap] += 1

            # 마지막 연속 처리
            if current_asc >= 2:
                consecutive_data['ascending_sequences'][current_asc] += 1
                asc_count = max(asc_count, current_asc)
            if current_desc >= 2:
                consecutive_data['descending_sequences'][current_desc] += 1
                desc_count = max(desc_count, current_desc)
            if current_same >= 2:
                consecutive_data['same_digit_sequences'][current_same] += 1
                same_count = max(same_count, current_same)

            round_analysis['ascending_seq'] = asc_count
            round_analysis['descending_seq'] = desc_count
            round_analysis['same_seq'] = same_count

            consecutive_data['by_round'].append(round_analysis)

        # 딕셔너리를 일반 딕셔너리로 변환
        consecutive_data['ascending_sequences'] = dict(consecutive_data['ascending_sequences'])
        consecutive_data['descending_sequences'] = dict(consecutive_data['descending_sequences'])
        consecutive_data['same_digit_sequences'] = dict(consecutive_data['same_digit_sequences'])
        consecutive_data['gap_patterns'] = dict(consecutive_data['gap_patterns'])

        # 결과 저장
        with open(f'{self.results_dir}/consecutive_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(consecutive_data, f, ensure_ascii=False, indent=2)

        self.logger.info("연속/건너뛰기 패턴 분석 완료")
        return consecutive_data

    def analyze_jo_number_combinations(self):
        """조와 번호 조합 패턴 분석"""
        self.logger.info("조와 번호 조합 패턴 분석 시작")

        combination_data = {
            'jo_first_digit': defaultdict(lambda: defaultdict(int)),
            'jo_last_digit': defaultdict(lambda: defaultdict(int)),
            'jo_sum_patterns': defaultdict(lambda: defaultdict(int)),
            'jo_even_odd_ratio': defaultdict(lambda: {'odd': 0, 'even': 0})
        }

        for _, row in self.data.iterrows():
            jo = row['jo']
            first_num = str(row['first_number']).zfill(6)

            # 조와 첫째자리 관계
            first_digit = first_num[0]
            combination_data['jo_first_digit'][jo][first_digit] += 1

            # 조와 마지막자리 관계
            last_digit = first_num[-1]
            combination_data['jo_last_digit'][jo][last_digit] += 1

            # 조와 숫자 합 관계
            digit_sum = sum([int(d) for d in first_num])
            sum_range = f"{digit_sum // 10 * 10}-{digit_sum // 10 * 10 + 9}"
            combination_data['jo_sum_patterns'][jo][sum_range] += 1

            # 조별 홀수/짝수 비율
            odd_count = sum([1 for d in first_num if int(d) % 2 == 1])
            even_count = 6 - odd_count
            combination_data['jo_even_odd_ratio'][jo]['odd'] += odd_count
            combination_data['jo_even_odd_ratio'][jo]['even'] += even_count

        # 중첩 defaultdict를 일반 딕셔너리로 변환
        result_data = {}
        for key, value in combination_data.items():
            result_data[key] = {k: dict(v) if isinstance(v, defaultdict) else v for k, v in value.items()}

        # 결과 저장
        with open(f'{self.results_dir}/jo_number_combinations.json', 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        self.logger.info("조와 번호 조합 패턴 분석 완료")
        return result_data

    def analyze_number_gaps(self):
        """번호 간격 패턴 분석"""
        self.logger.info("번호 간격 패턴 분석 시작")

        gap_data = {
            'adjacent_gaps': defaultdict(int),
            'position_gaps': {},
            'gap_sequences': defaultdict(int),
            'by_round': []
        }

        # 각 자리별 간격 분석
        for pos in range(5):  # 0-1, 1-2, 2-3, 3-4, 4-5 자리 간격
            gap_data['position_gaps'][f'pos{pos + 1}-{pos + 2}'] = defaultdict(int)

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)
            digits = [int(d) for d in first_num]

            round_gaps = []
            for i in range(5):
                gap = abs(digits[i + 1] - digits[i])
                round_gaps.append(gap)
                gap_data['adjacent_gaps'][gap] += 1
                gap_data['position_gaps'][f'pos{i + 1}-{i + 2}'][gap] += 1

            # 간격 시퀀스 패턴 (첫 3개 간격)
            gap_sequence = tuple(round_gaps[:3])
            gap_data['gap_sequences'][gap_sequence] += 1

            gap_data['by_round'].append({
                'round': row['round'],
                'gaps': round_gaps,
                'max_gap': max(round_gaps),
                'min_gap': min(round_gaps),
                'avg_gap': sum(round_gaps) / len(round_gaps)
            })

        # defaultdict를 일반 딕셔너리로 변환
        gap_data['adjacent_gaps'] = dict(gap_data['adjacent_gaps'])
        gap_data['position_gaps'] = {k: dict(v) for k, v in gap_data['position_gaps'].items()}
        gap_data['gap_sequences'] = {str(k): v for k, v in gap_data['gap_sequences'].items()}

        # 결과 저장
        with open(f'{self.results_dir}/number_gaps.json', 'w', encoding='utf-8') as f:
            json.dump(gap_data, f, ensure_ascii=False, indent=2)

        self.logger.info("번호 간격 패턴 분석 완료")
        return gap_data

    def create_pattern_charts(self, odd_even_data, consecutive_data, gap_data):
        """패턴 분석 차트 생성"""
        self.logger.info("패턴 분석 차트 생성 시작")

        # 1. 홀수/짝수 분포 차트
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('홀수/짝수 분포 패턴 분석', fontsize=16, fontweight='bold')

        # 자리별 홀수/짝수 분포
        positions = list(odd_even_data['by_position'].keys())
        odd_counts = [odd_even_data['by_position'][pos]['odd'] for pos in positions]
        even_counts = [odd_even_data['by_position'][pos]['even'] for pos in positions]

        x = np.arange(len(positions))
        width = 0.35

        axes[0, 0].bar(x - width / 2, odd_counts, width, label='홀수', color='lightcoral', alpha=0.7)
        axes[0, 0].bar(x + width / 2, even_counts, width, label='짝수', color='lightblue', alpha=0.7)
        axes[0, 0].set_title('자리별 홀수/짝수 분포')
        axes[0, 0].set_xlabel('자리')
        axes[0, 0].set_ylabel('출현 횟수')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels([f'{i + 1}자리' for i in range(6)])
        axes[0, 0].legend()

        # 전체 홀수/짝수 비율 파이차트
        total_odd = odd_even_data['overall_stats']['total_odd']
        total_even = odd_even_data['overall_stats']['total_even']

        axes[0, 1].pie([total_odd, total_even], labels=['홀수', '짝수'],
                       colors=['lightcoral', 'lightblue'], autopct='%1.1f%%')
        axes[0, 1].set_title('전체 홀수/짝수 비율')

        # 가장 많이 나온 홀짝 패턴 (상위 10개)
        top_patterns = list(odd_even_data['pattern_counts'].items())[:10]
        pattern_names = [p[0] for p in top_patterns]
        pattern_counts = [p[1] for p in top_patterns]

        axes[1, 0].barh(pattern_names, pattern_counts, color='lightgreen', alpha=0.7)
        axes[1, 0].set_title('상위 홀짝 패턴 (O:홀수, E:짝수)')
        axes[1, 0].set_xlabel('출현 횟수')

        # 연속 패턴 분포
        if consecutive_data['ascending_sequences']:
            seq_lengths = list(consecutive_data['ascending_sequences'].keys())
            seq_counts = list(consecutive_data['ascending_sequences'].values())

            axes[1, 1].bar(seq_lengths, seq_counts, color='gold', alpha=0.7)
            axes[1, 1].set_title('상승 연속 패턴 분포')
            axes[1, 1].set_xlabel('연속 길이')
            axes[1, 1].set_ylabel('출현 횟수')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/pattern_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

        # 2. 간격 패턴 차트
        plt.figure(figsize=(14, 10))

        # 인접 숫자 간격 분포
        gaps = list(gap_data['adjacent_gaps'].keys())
        gap_counts = list(gap_data['adjacent_gaps'].values())

        plt.subplot(2, 2, 1)
        plt.bar(gaps, gap_counts, color='skyblue', alpha=0.7)
        plt.title('인접 숫자 간격 분포')
        plt.xlabel('간격')
        plt.ylabel('출현 횟수')

        # 자리별 간격 분포 (히트맵)
        position_gaps_matrix = []
        positions = sorted(gap_data['position_gaps'].keys())
        all_gaps = sorted(set().union(*[gap_data['position_gaps'][pos].keys() for pos in positions]))

        for pos in positions:
            row = [gap_data['position_gaps'][pos].get(gap, 0) for gap in all_gaps]
            position_gaps_matrix.append(row)

        plt.subplot(2, 2, 2)
        sns.heatmap(position_gaps_matrix,
                    xticklabels=all_gaps,
                    yticklabels=[pos.replace('pos', '').replace('-', '→') for pos in positions],
                    annot=True, fmt='d', cmap='YlOrRd')
        plt.title('자리별 간격 분포 히트맵')

        # 간격 통계 (회차별 최대/최소/평균 간격)
        max_gaps = [round_data['max_gap'] for round_data in gap_data['by_round']]
        avg_gaps = [round_data['avg_gap'] for round_data in gap_data['by_round']]

        plt.subplot(2, 2, 3)
        plt.hist(max_gaps, bins=20, alpha=0.7, color='orange', label='최대 간격')
        plt.title('회차별 최대 간격 분포')
        plt.xlabel('최대 간격')
        plt.ylabel('빈도')

        plt.subplot(2, 2, 4)
        plt.hist(avg_gaps, bins=20, alpha=0.7, color='green', label='평균 간격')
        plt.title('회차별 평균 간격 분포')
        plt.xlabel('평균 간격')
        plt.ylabel('빈도')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/gap_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("패턴 분석 차트 생성 완료")

    def generate_pattern_summary(self, odd_even_data, consecutive_data, combination_data, gap_data):
        """패턴 분석 종합 보고서 생성"""
        self.logger.info("패턴 분석 종합 보고서 생성 시작")

        summary = {
            'analysis_summary': {
                'total_rounds': len(self.data),
                'analysis_date': datetime.now().isoformat(),
                'data_range': f"{self.data['round'].min()}회 ~ {self.data['round'].max()}회"
            },
            'odd_even_insights': {
                'overall_odd_percentage': round(odd_even_data['overall_stats']['odd_percentage'], 2),
                'overall_even_percentage': round(odd_even_data['overall_stats']['even_percentage'], 2),
                'most_common_pattern': max(odd_even_data['pattern_counts'].items(), key=lambda x: x[1]),
                'position_bias': {}
            },
            'consecutive_insights': {
                'max_ascending_sequence': max(consecutive_data['ascending_sequences'].keys()) if consecutive_data[
                    'ascending_sequences'] else 0,
                'max_descending_sequence': max(consecutive_data['descending_sequences'].keys()) if consecutive_data[
                    'descending_sequences'] else 0,
                'max_same_sequence': max(consecutive_data['same_digit_sequences'].keys()) if consecutive_data[
                    'same_digit_sequences'] else 0,
                'most_common_gap': max(consecutive_data['gap_patterns'].items(), key=lambda x: x[1]) if
                consecutive_data['gap_patterns'] else None
            },
            'gap_insights': {
                'most_common_adjacent_gap': max(gap_data['adjacent_gaps'].items(), key=lambda x: x[1]),
                'avg_max_gap': round(np.mean([r['max_gap'] for r in gap_data['by_round']]), 2),
                'avg_min_gap': round(np.mean([r['min_gap'] for r in gap_data['by_round']]), 2),
                'overall_avg_gap': round(np.mean([r['avg_gap'] for r in gap_data['by_round']]), 2)
            },
            'key_findings': []
        }

        # 자리별 홀짝 편향 분석
        for pos, data in odd_even_data['by_position'].items():
            total = data['odd'] + data['even']
            odd_pct = (data['odd'] / total) * 100
            summary['odd_even_insights']['position_bias'][pos] = {
                'odd_percentage': round(odd_pct, 1),
                'bias': 'odd' if odd_pct > 55 else ('even' if odd_pct < 45 else 'balanced')
            }

        # 주요 발견사항 생성
        findings = [
            f"전체 {summary['analysis_summary']['total_rounds']}회차 데이터를 분석했습니다.",
            f"홀수와 짝수의 전체 비율은 {summary['odd_even_insights']['overall_odd_percentage']}% : {summary['odd_even_insights']['overall_even_percentage']}%입니다.",
            f"가장 흔한 홀짝 패턴은 '{summary['odd_even_insights']['most_common_pattern'][0]}'으로 {summary['odd_even_insights']['most_common_pattern'][1]}번 출현했습니다.",
        ]

        if summary['consecutive_insights']['most_common_gap']:
            findings.append(
                f"인접 숫자 간 가장 흔한 간격은 {summary['consecutive_insights']['most_common_gap'][0]}으로 {summary['consecutive_insights']['most_common_gap'][1]}번 나타났습니다.")

        findings.append(
            f"회차별 평균 최대 간격은 {summary['gap_insights']['avg_max_gap']}이고, 전체 평균 간격은 {summary['gap_insights']['overall_avg_gap']}입니다.")

        summary['key_findings'] = findings

        # 보고서 저장
        with open(f'{self.results_dir}/pattern_analysis_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.logger.info("패턴 분석 종합 보고서 생성 완료")
        return summary

    def run_full_analysis(self):
        """전체 패턴 분석 실행"""
        self.logger.info("=== 고급 패턴 분석 시작 ===")

        # 데이터 로드
        if not self.load_data():
            return False

        try:
            # 1. 홀수/짝수 분포 분석
            odd_even_data = self.analyze_odd_even_patterns()

            # 2. 연속/건너뛰기 패턴 분석
            consecutive_data = self.analyze_consecutive_patterns()

            # 3. 조와 번호 조합 분석
            combination_data = self.analyze_jo_number_combinations()

            # 4. 번호 간격 패턴 분석
            gap_data = self.analyze_number_gaps()

            # 5. 차트 생성
            self.create_pattern_charts(odd_even_data, consecutive_data, gap_data)

            # 6. 종합 보고서 생성
            summary = self.generate_pattern_summary(odd_even_data, consecutive_data, combination_data, gap_data)

            self.logger.info("=== 고급 패턴 분석 완료 ===")
            print("고급 패턴 분석이 완료되었습니다!")
            print(f"결과 파일: {self.results_dir}/")
            print(f"차트 파일: {self.charts_dir}/")

            return True

        except Exception as e:
            self.logger.error(f"분석 중 오류 발생: {e}")
            return False


def main():
    """메인 함수"""
    analyzer = PatternAnalyzer()
    success = analyzer.run_full_analysis()

    if success:
        print("\n🎉 고급 패턴 분석이 성공적으로 완료되었습니다!")
        print("\n📁 생성된 파일들:")
        print("- analysis_results/odd_even_patterns.json")
        print("- analysis_results/consecutive_patterns.json")
        print("- analysis_results/jo_number_combinations.json")
        print("- analysis_results/number_gaps.json")
        print("- analysis_results/pattern_analysis_summary.json")
        print("- charts/pattern_analysis.png")
        print("- charts/gap_analysis.png")
    else:
        print("❌ 분석 중 오류가 발생했습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()