#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 고급 패턴 분석 스크립트 (수정된 버전)
- 홀짝 분포 패턴 분석
- 연속 숫자 패턴 분석
- 숫자 간격 패턴 분석
- 조별 번호 조합 분석
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
import itertools


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


class PatternAnalyzer:
    def __init__(self, lottery_type="720", data_file=None):
        """고급 패턴 분석기 초기화"""
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
        log_filename = f"logs/pattern_analysis_{lottery_type}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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

    def analyze_odd_even_patterns(self):
        """홀짝 분포 패턴 분석"""
        self.logger.info("홀짝 분포 패턴 분석 시작")

        odd_even_data = {
            'by_round': [],
            'overall_distribution': defaultdict(int),
            'position_patterns': {},
            'statistics': {}
        }

        # 각 회차별 홀짝 패턴 분석
        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)
            digits = [int(d) for d in first_num]

            # 홀짝 패턴 생성
            odd_even_pattern = ['홀' if d % 2 == 1 else '짝' for d in digits]
            odd_count = sum(1 for d in digits if d % 2 == 1)
            even_count = 6 - odd_count

            pattern_str = ''.join(odd_even_pattern)
            odd_even_data['overall_distribution'][pattern_str] += 1

            odd_even_data['by_round'].append({
                'round': row['round'],
                'pattern': pattern_str,
                'odd_count': odd_count,
                'even_count': even_count,
                'digits': digits
            })

        # 자리별 홀짝 분포
        for pos in range(6):
            pos_patterns = defaultdict(int)
            for round_data in odd_even_data['by_round']:
                digit = round_data['digits'][pos]
                pattern = '홀' if digit % 2 == 1 else '짝'
                pos_patterns[pattern] += 1

            odd_even_data['position_patterns'][f'자리{pos + 1}'] = dict(pos_patterns)

        # 통계 계산
        total_rounds = len(odd_even_data['by_round'])
        odd_counts = [r['odd_count'] for r in odd_even_data['by_round']]

        odd_even_data['statistics'] = {
            'avg_odd_count': sum(odd_counts) / len(odd_counts) if odd_counts else 0,
            'max_odd_count': max(odd_counts) if odd_counts else 0,
            'min_odd_count': min(odd_counts) if odd_counts else 0,
            'most_common_pattern': max(odd_even_data['overall_distribution'],
                                       key=odd_even_data['overall_distribution'].get) if odd_even_data[
                'overall_distribution'] else '',
            'total_patterns': len(odd_even_data['overall_distribution'])
        }

        # defaultdict를 일반 딕셔너리로 변환
        odd_even_data['overall_distribution'] = dict(odd_even_data['overall_distribution'])

        # 결과 저장
        with open(f'{self.results_dir}/odd_even_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(odd_even_data, f, ensure_ascii=False, indent=2)

        self.logger.info("홀짝 분포 패턴 분석 완료")
        return odd_even_data

    def analyze_consecutive_patterns(self):
        """연속 숫자 패턴 분석"""
        self.logger.info("연속 숫자 패턴 분석 시작")

        consecutive_data = {
            'by_round': [],
            'consecutive_counts': defaultdict(int),
            'consecutive_lengths': defaultdict(int),
            'statistics': {}
        }

        for _, row in self.data.iterrows():
            first_num = str(row['first_number']).zfill(6)
            digits = [int(d) for d in first_num]

            # 연속 숫자 찾기
            consecutive_sequences = []
            current_sequence = [digits[0]]

            for i in range(1, len(digits)):
                if digits[i] == digits[i - 1] + 1:
                    current_sequence.append(digits[i])
                else:
                    if len(current_sequence) >= 2:
                        consecutive_sequences.append(current_sequence.copy())
                    current_sequence = [digits[i]]

            # 마지막 시퀀스 체크
            if len(current_sequence) >= 2:
                consecutive_sequences.append(current_sequence)

            # 연속 개수 카운트
            total_consecutive = sum(len(seq) for seq in consecutive_sequences)
            max_consecutive_length = max([len(seq) for seq in consecutive_sequences]) if consecutive_sequences else 0

            consecutive_data['consecutive_counts'][total_consecutive] += 1
            consecutive_data['consecutive_lengths'][max_consecutive_length] += 1

            consecutive_data['by_round'].append({
                'round': row['round'],
                'digits': digits,
                'consecutive_sequences': consecutive_sequences,
                'total_consecutive': total_consecutive,
                'max_consecutive_length': max_consecutive_length
            })

        # 통계 계산
        total_consecutive_list = [r['total_consecutive'] for r in consecutive_data['by_round']]
        max_lengths = [r['max_consecutive_length'] for r in consecutive_data['by_round']]

        consecutive_data['statistics'] = {
            'avg_consecutive_count': sum(total_consecutive_list) / len(
                total_consecutive_list) if total_consecutive_list else 0,
            'max_consecutive_in_single_round': max(total_consecutive_list) if total_consecutive_list else 0,
            'avg_max_consecutive_length': sum(max_lengths) / len(max_lengths) if max_lengths else 0,
            'rounds_with_consecutive': sum(1 for c in total_consecutive_list if c > 0),
            'consecutive_probability': (sum(1 for c in total_consecutive_list if c > 0) / len(
                total_consecutive_list) * 100) if total_consecutive_list else 0
        }

        # defaultdict를 일반 딕셔너리로 변환
        consecutive_data['consecutive_counts'] = dict(consecutive_data['consecutive_counts'])
        consecutive_data['consecutive_lengths'] = dict(consecutive_data['consecutive_lengths'])

        # 결과 저장
        with open(f'{self.results_dir}/consecutive_patterns.json', 'w', encoding='utf-8') as f:
            json.dump(consecutive_data, f, ensure_ascii=False, indent=2)

        self.logger.info("연속 숫자 패턴 분석 완료")
        return consecutive_data

    def analyze_number_gaps(self):
        """번호 간격 패턴 분석 (수정된 버전)"""
        self.logger.info("번호 간격 패턴 분석 시작")

        gap_data = {
            'adjacent_gaps': defaultdict(int),
            'position_gaps': {},
            'gap_sequences': defaultdict(int),
            'by_round': [],
            'statistics': {}  # 통계 정보 추가
        }

        # 통계 계산을 위한 리스트
        max_gaps = []
        min_gaps = []
        avg_gaps = []

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
            if len(round_gaps) >= 3:
                gap_sequence = tuple(round_gaps[:3])
                gap_data['gap_sequences'][gap_sequence] += 1

            # 통계 데이터 수집
            if round_gaps:
                max_gap = max(round_gaps)
                min_gap = min(round_gaps)
                avg_gap = sum(round_gaps) / len(round_gaps)

                max_gaps.append(max_gap)
                min_gaps.append(min_gap)
                avg_gaps.append(avg_gap)

                gap_data['by_round'].append({
                    'round': row['round'],
                    'gaps': round_gaps,
                    'max_gap': max_gap,
                    'min_gap': min_gap,
                    'avg_gap': avg_gap
                })

        # 통계 계산
        if max_gaps:
            gap_data['statistics'] = {
                'avg_max_gap': sum(max_gaps) / len(max_gaps),
                'avg_min_gap': sum(min_gaps) / len(min_gaps),
                'overall_avg_gap': sum(avg_gaps) / len(avg_gaps),
                'total_rounds': len(max_gaps)
            }

        # defaultdict를 일반 딕셔너리로 변환
        gap_data['adjacent_gaps'] = dict(gap_data['adjacent_gaps'])
        gap_data['position_gaps'] = {k: dict(v) for k, v in gap_data['position_gaps'].items()}
        gap_data['gap_sequences'] = {str(k): v for k, v in gap_data['gap_sequences'].items()}

        # 결과 저장
        with open(f'{self.results_dir}/number_gaps.json', 'w', encoding='utf-8') as f:
            json.dump(gap_data, f, ensure_ascii=False, indent=2)

        self.logger.info("번호 간격 패턴 분석 완료")
        return gap_data

    def analyze_jo_number_combinations(self):
        """조별 번호 조합 분석"""
        self.logger.info("조별 번호 조합 분석 시작")

        jo_combinations = defaultdict(lambda: defaultdict(int))

        for _, row in self.data.iterrows():
            jo = row['jo']
            first_num = str(row['first_number']).zfill(6)

            # 첫 2자리와 마지막 2자리 조합 분석
            first_two = first_num[:2]
            last_two = first_num[-2:]
            middle_two = first_num[2:4]

            jo_combinations[f'{jo}조']['첫2자리'][first_two] += 1
            jo_combinations[f'{jo}조']['마지막2자리'][last_two] += 1
            jo_combinations[f'{jo}조']['중간2자리'][middle_two] += 1

        # defaultdict를 일반 딕셔너리로 변환
        result = {}
        for jo, combinations in jo_combinations.items():
            result[jo] = {}
            for pos, combos in combinations.items():
                result[jo][pos] = dict(combos)

        # 결과 저장
        with open(f'{self.results_dir}/jo_number_combinations.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        self.logger.info("조별 번호 조합 분석 완료")
        return result

    def create_pattern_analysis_chart(self, odd_even_data, consecutive_data):
        """패턴 분석 종합 차트 생성"""
        self.logger.info("패턴 분석 종합 차트 생성 시작")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. 홀짝 분포 차트
        if odd_even_data['position_patterns']:
            positions = list(odd_even_data['position_patterns'].keys())
            odd_counts = [odd_even_data['position_patterns'][pos].get('홀', 0) for pos in positions]
            even_counts = [odd_even_data['position_patterns'][pos].get('짝', 0) for pos in positions]

            x = np.arange(len(positions))
            width = 0.35

            axes[0, 0].bar(x - width / 2, odd_counts, width, label='홀수', color='red', alpha=0.7)
            axes[0, 0].bar(x + width / 2, even_counts, width, label='짝수', color='blue', alpha=0.7)
            axes[0, 0].set_title('자리별 홀짝 분포', fontweight='bold')
            axes[0, 0].set_xlabel('자리')
            axes[0, 0].set_ylabel('출현 횟수')
            axes[0, 0].set_xticks(x)
            axes[0, 0].set_xticklabels(positions)
            axes[0, 0].legend()

        # 2. 연속 숫자 길이 분포
        if consecutive_data['consecutive_lengths']:
            lengths = sorted(consecutive_data['consecutive_lengths'].keys())
            counts = [consecutive_data['consecutive_lengths'][length] for length in lengths]

            axes[0, 1].bar(lengths, counts, color='green', alpha=0.7)
            axes[0, 1].set_title('연속 숫자 길이 분포', fontweight='bold')
            axes[0, 1].set_xlabel('연속 길이')
            axes[0, 1].set_ylabel('출현 횟수')

        # 3. 홀짝 패턴 상위 10개
        if odd_even_data['overall_distribution']:
            top_patterns = sorted(odd_even_data['overall_distribution'].items(),
                                  key=lambda x: x[1], reverse=True)[:10]

            patterns, counts = zip(*top_patterns)

            axes[1, 0].bar(range(len(patterns)), counts, color='purple', alpha=0.7)
            axes[1, 0].set_title('홀짝 패턴 상위 10개', fontweight='bold')
            axes[1, 0].set_xlabel('패턴')
            axes[1, 0].set_ylabel('출현 횟수')
            axes[1, 0].set_xticks(range(len(patterns)))
            axes[1, 0].set_xticklabels(patterns, rotation=45, ha='right')

        # 4. 연속 숫자 개수 분포
        if consecutive_data['consecutive_counts']:
            counts_keys = sorted(consecutive_data['consecutive_counts'].keys())
            counts_values = [consecutive_data['consecutive_counts'][key] for key in counts_keys]

            axes[1, 1].bar(counts_keys, counts_values, color='orange', alpha=0.7)
            axes[1, 1].set_title('연속 숫자 개수 분포', fontweight='bold')
            axes[1, 1].set_xlabel('연속 숫자 개수')
            axes[1, 1].set_ylabel('출현 횟수')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/pattern_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("패턴 분석 종합 차트 생성 완료")

    def create_gap_analysis_chart(self, gap_data):
        """간격 분석 차트 생성"""
        self.logger.info("간격 분석 차트 생성 시작")

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. 인접 간격 분포
        if gap_data['adjacent_gaps']:
            gaps = sorted(gap_data['adjacent_gaps'].keys())
            counts = [gap_data['adjacent_gaps'][gap] for gap in gaps]

            axes[0, 0].bar(gaps, counts, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('인접 숫자 간격 분포', fontweight='bold')
            axes[0, 0].set_xlabel('간격')
            axes[0, 0].set_ylabel('출현 횟수')

        # 2. 자리별 간격 분포 (첫 번째 자리 예시)
        first_pos_gaps = gap_data['position_gaps'].get('pos1-2', {})
        if first_pos_gaps:
            gaps = sorted(first_pos_gaps.keys())
            counts = [first_pos_gaps[gap] for gap in gaps]

            axes[0, 1].bar(gaps, counts, color='lightgreen', alpha=0.7)
            axes[0, 1].set_title('1-2자리 간격 분포', fontweight='bold')
            axes[0, 1].set_xlabel('간격')
            axes[0, 1].set_ylabel('출현 횟수')

        # 3. 최대 간격 히스토그램
        if gap_data['by_round']:
            max_gaps = [round_data['max_gap'] for round_data in gap_data['by_round']]

            axes[1, 0].hist(max_gaps, bins=10, color='coral', alpha=0.7, edgecolor='black')
            axes[1, 0].set_title('회차별 최대 간격 분포', fontweight='bold')
            axes[1, 0].set_xlabel('최대 간격')
            axes[1, 0].set_ylabel('빈도')

        # 4. 평균 간격 히스토그램
        if gap_data['by_round']:
            avg_gaps = [round_data['avg_gap'] for round_data in gap_data['by_round']]

            axes[1, 1].hist(avg_gaps, bins=10, color='gold', alpha=0.7, edgecolor='black')
            axes[1, 1].set_title('회차별 평균 간격 분포', fontweight='bold')
            axes[1, 1].set_xlabel('평균 간격')
            axes[1, 1].set_ylabel('빈도')

        plt.tight_layout()
        plt.savefig(f'{self.charts_dir}/gap_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

        self.logger.info("간격 분석 차트 생성 완료")

    def generate_pattern_summary(self, odd_even_data, consecutive_data, gap_data, jo_combinations):
        """패턴 분석 종합 요약 생성"""
        self.logger.info("패턴 분석 종합 요약 생성 시작")

        summary = {
            'analysis_info': {
                'total_rounds': len(self.data),
                'lottery_type': self.lottery_type,
                'analysis_date': datetime.now().isoformat()
            },
            'odd_even_summary': {
                'total_patterns': odd_even_data['statistics']['total_patterns'],
                'most_common_pattern': odd_even_data['statistics']['most_common_pattern'],
                'avg_odd_count': round(odd_even_data['statistics']['avg_odd_count'], 2)
            },
            'consecutive_summary': {
                'consecutive_probability': round(consecutive_data['statistics']['consecutive_probability'], 2),
                'avg_consecutive_count': round(consecutive_data['statistics']['avg_consecutive_count'], 2),
                'max_consecutive_in_single_round': consecutive_data['statistics']['max_consecutive_in_single_round']
            },
            'gap_summary': gap_data['statistics'],
            'jo_combinations_count': {jo: len(combinations) for jo, combinations in jo_combinations.items()},
            'key_insights': []
        }

        # 주요 인사이트 생성
        insights = [
            f"연금복권{self.lottery_type} 총 {len(self.data)}회차 고급 패턴 분석 완료",
            f"총 {odd_even_data['statistics']['total_patterns']}개의 홀짝 패턴 발견",
            f"연속 숫자가 나올 확률: {consecutive_data['statistics']['consecutive_probability']:.1f}%",
            f"평균 홀수 개수: {odd_even_data['statistics']['avg_odd_count']:.1f}개"
        ]

        if gap_data['statistics']:
            insights.append(f"평균 최대 간격: {gap_data['statistics']['avg_max_gap']:.1f}")

        summary['key_insights'] = insights

        # 결과 저장
        with open(f'{self.results_dir}/pattern_analysis_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        self.logger.info("패턴 분석 종합 요약 생성 완료")
        return summary

    def run_full_analysis(self):
        """전체 패턴 분석 실행"""
        self.logger.info(f"=== 연금복권{self.lottery_type} 고급 패턴 분석 시작 ===")

        # 데이터 로드
        if not self.load_data():
            return False

        try:
            # 1. 홀짝 분포 패턴 분석
            odd_even_data = self.analyze_odd_even_patterns()

            # 2. 연속 숫자 패턴 분석
            consecutive_data = self.analyze_consecutive_patterns()

            # 3. 숫자 간격 패턴 분석
            gap_data = self.analyze_number_gaps()

            # 4. 조별 번호 조합 분석
            jo_combinations = self.analyze_jo_number_combinations()

            # 5. 패턴 분석 차트 생성
            self.create_pattern_analysis_chart(odd_even_data, consecutive_data)
            self.create_gap_analysis_chart(gap_data)

            # 6. 종합 요약 생성
            summary = self.generate_pattern_summary(odd_even_data, consecutive_data, gap_data, jo_combinations)

            self.logger.info("=== 고급 패턴 분석 완료 ===")
            print(f"연금복권{self.lottery_type} 고급 패턴 분석이 완료되었습니다!")
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
        print("연금복권 고급 패턴 분석을 시작합니다.")
        print("1. 연금복권720+ 분석")
        print("2. 연금복권520 분석")

        choice = input("선택하세요 (1 또는 2, 기본값: 1): ").strip()

        if choice == "2":
            lottery_type = "520"
        else:
            lottery_type = "720"

    analyzer = PatternAnalyzer(lottery_type)
    success = analyzer.run_full_analysis()

    if success:
        print(f"\n🎉 연금복권{lottery_type} 고급 패턴 분석이 성공적으로 완료되었습니다!")
        print("\n📁 생성된 파일들:")
        print("- analysis_results/pattern_analysis_summary.json")
        print("- analysis_results/odd_even_patterns.json")
        print("- analysis_results/consecutive_patterns.json")
        print("- analysis_results/number_gaps.json")
        print("- analysis_results/jo_number_combinations.json")
        print("- charts/pattern_analysis.png")
        print("- charts/gap_analysis.png")
    else:
        print("❌ 분석 중 오류가 발생했습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    main()