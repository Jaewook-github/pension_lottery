import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# 한글 폰트 설정 (matplotlib)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class LotteryAnalyzer:
    def __init__(self, db_name="lottery_data.db"):
        self.db_name = db_name
        self.load_data()

    def load_data(self):
        """데이터베이스에서 데이터 로드"""
        try:
            conn = sqlite3.connect(self.db_name)
            self.df = pd.read_sql_query('SELECT * FROM lottery_results ORDER BY round_number', conn)
            conn.close()
            print(f"총 {len(self.df)}개의 회차 데이터를 로드했습니다.")
        except Exception as e:
            print(f"데이터 로드 실패: {e}")
            self.df = pd.DataFrame()

    def extract_individual_numbers(self, number_string):
        """번호 문자열에서 개별 숫자 추출"""
        if pd.isna(number_string) or not number_string:
            return []

        # "5조162265" 형태에서 숫자 추출
        if '조' in str(number_string):
            # 조 단위 분리
            parts = str(number_string).split('조')
            if len(parts) == 2:
                jo_part = parts[0]
                remaining = parts[1]
                # 각 자리수를 개별 숫자로 분리
                numbers = [int(jo_part)] + [int(d) for d in remaining if d.isdigit()]
                return numbers

    def debug_data_structure(self):
        """데이터 구조 확인 (디버깅용)"""
        print("\n=== 데이터 구조 확인 ===")
        print("데이터베이스 컬럼:", list(self.df.columns))
        print(f"총 데이터 개수: {len(self.df)}")

        if not self.df.empty:
            print("\n최근 5개 데이터 샘플:")
            for idx, row in self.df.tail(5).iterrows():
                print(f"회차 {row['round_number']}:")
                print(f"  1등: '{row['first_prize_numbers']}'")
                print(f"  보너스: '{row['bonus_numbers']}'")

                # 숫자 추출 테스트
                first_nums = self.extract_individual_numbers(row['first_prize_numbers'])
                bonus_nums = self.extract_individual_numbers(row['bonus_numbers'])
                print(f"  1등 추출된 숫자: {first_nums}")
                print(f"  보너스 추출된 숫자: {bonus_nums}")
                print()

        # 데이터 타입 확인
        print("데이터 타입:")
        print(self.df.dtypes)

        # null 값 확인
        print("\nNull 값 개수:")
        print(self.df.isnull().sum())

        # 쉼표로 구분된 숫자들
        numbers = []
        for num_str in str(number_string).split(','):
            try:
                num = int(num_str.strip())
                if 0 <= num <= 9:  # 한 자리 숫자만
                    numbers.append(num)
            except:
                continue

        return numbers

    def analyze_position_frequency(self):
        """자리별 숫자 출현 빈도 분석"""
        print("\n=== 자리별 숫자 출현 빈도 분석 ===")

        # 1등 번호 자리별 분석 (7자리)
        first_positions = [[] for _ in range(7)]
        valid_first_count = 0

        for numbers_str in self.df['first_prize_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if numbers and len(numbers) >= 7:
                valid_first_count += 1
                for i, num in enumerate(numbers[:7]):
                    first_positions[i].append(num)

        print(f"1등 번호 자리별 분석 (유효한 데이터: {valid_first_count}개):")
        for i, position_nums in enumerate(first_positions):
            if position_nums:
                counter = Counter(position_nums)
                print(f"  {i + 1}번째 자리:")
                for num, count in counter.most_common():
                    print(f"    숫자 {num}: {count}회 ({count / len(position_nums) * 100:.1f}%)")
                print()
            else:
                print(f"  {i + 1}번째 자리: 데이터 없음")

        # 보너스 번호 자리별 분석 (6자리)
        bonus_positions = [[] for _ in range(6)]
        valid_bonus_count = 0

        for numbers_str in self.df['bonus_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if numbers and len(numbers) >= 6:
                valid_bonus_count += 1
                for i, num in enumerate(numbers[:6]):
                    bonus_positions[i].append(num)

        print(f"보너스 번호 자리별 분석 (유효한 데이터: {valid_bonus_count}개):")
        for i, position_nums in enumerate(bonus_positions):
            if position_nums:
                counter = Counter(position_nums)
                print(f"  {i + 1}번째 자리:")
                for num, count in counter.most_common():
                    print(f"    숫자 {num}: {count}회 ({count / len(position_nums) * 100:.1f}%)")
                print()
            else:
                print(f"  {i + 1}번째 자리: 데이터 없음")

        return first_positions, bonus_positions
        """번호 문자열에서 개별 숫자 추출"""
        if pd.isna(number_string) or not number_string:
            return []

        # "5조162265" 형태에서 숫자 추출
        if '조' in str(number_string):
            # 조 단위 분리
            parts = str(number_string).split('조')
            if len(parts) == 2:
                jo_part = parts[0]
                remaining = parts[1]
                # 각 자리수를 개별 숫자로 분리
                numbers = [int(jo_part)] + [int(d) for d in remaining if d.isdigit()]
                return numbers

        # 쉼표로 구분된 숫자들
        numbers = []
        for num_str in str(number_string).split(','):
            try:
                num = int(num_str.strip())
                if 0 <= num <= 9:  # 한 자리 숫자만
                    numbers.append(num)
            except:
                continue

        return numbers

    def analyze_number_frequency(self):
        """번호 출현 빈도 분석"""
        print("\n=== 번호 출현 빈도 분석 ===")

        # 1등 번호 분석
        first_numbers = []
        for numbers in self.df['first_prize_numbers']:
            extracted = self.extract_individual_numbers(numbers)
            if extracted:  # 빈 리스트가 아닌 경우만
                first_numbers.extend(extracted)

        first_counter = Counter(first_numbers)

        # 보너스 번호 분석
        bonus_numbers = []
        for numbers in self.df['bonus_numbers']:
            extracted = self.extract_individual_numbers(numbers)
            if extracted:  # 빈 리스트가 아닌 경우만
                bonus_numbers.extend(extracted)

        bonus_counter = Counter(bonus_numbers)

        print("1등 당첨번호 빈도 (상위 10개):")
        if first_counter:
            for num, count in first_counter.most_common(10):
                print(f"  숫자 {num}: {count}회 출현")
        else:
            print("  분석할 데이터가 없습니다.")

        print("\n보너스 당첨번호 빈도 (상위 10개):")
        if bonus_counter:
            for num, count in bonus_counter.most_common(10):
                print(f"  숫자 {num}: {count}회 출현")
        else:
            print("  분석할 데이터가 없습니다.")

        return first_counter, bonus_counter

    def analyze_position_frequency(self):
        """자리별 숫자 출현 빈도 분석"""
        print("\n=== 자리별 숫자 출현 빈도 분석 ===")

        # 1등 번호 자리별 분석 (7자리)
        first_positions = [[] for _ in range(7)]
        for numbers_str in self.df['first_prize_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if len(numbers) >= 7:
                for i, num in enumerate(numbers[:7]):
                    first_positions[i].append(num)

        print("1등 번호 자리별 분석:")
        for i, position_nums in enumerate(first_positions):
            if position_nums:
                counter = Counter(position_nums)
                print(f"  {i + 1}번째 자리:")
                for num, count in counter.most_common():
                    print(f"    숫자 {num}: {count}회 ({count / len(position_nums) * 100:.1f}%)")
                print()

        # 보너스 번호 자리별 분석 (6자리)
        bonus_positions = [[] for _ in range(6)]
        for numbers_str in self.df['bonus_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if len(numbers) >= 6:
                for i, num in enumerate(numbers[:6]):
                    bonus_positions[i].append(num)

        print("보너스 번호 자리별 분석:")
        for i, position_nums in enumerate(bonus_positions):
            if position_nums:
                counter = Counter(position_nums)
                print(f"  {i + 1}번째 자리:")
                for num, count in counter.most_common():
                    print(f"    숫자 {num}: {count}회 ({count / len(position_nums) * 100:.1f}%)")
                print()

        return first_positions, bonus_positions

    def analyze_complete_number_frequency(self):
        """완전한 번호별 출현 횟수 분석"""
        print("\n=== 완전한 번호별 출현 횟수 분석 ===")

        # 1등 완전 번호 빈도
        valid_first_numbers = self.df['first_prize_numbers'].dropna()
        first_complete = Counter(valid_first_numbers)

        print("1등 완전 번호 출현 횟수:")
        duplicates_found = False
        for number, count in first_complete.most_common(20):
            if count > 1:  # 2회 이상 나온 번호만 표시
                print(f"  {number}: {count}회")
                duplicates_found = True

        if not duplicates_found:
            print("  중복 출현한 1등 번호 없음")

        # 보너스 완전 번호 빈도
        valid_bonus_numbers = self.df['bonus_numbers'].dropna()
        bonus_complete = Counter(valid_bonus_numbers)

        print("\n보너스 완전 번호 출현 횟수:")
        duplicates_found = False
        for number, count in bonus_complete.most_common(20):
            if count > 1:  # 2회 이상 나온 번호만 표시
                print(f"  {number}: {count}회")
                duplicates_found = True

        if not duplicates_found:
            print("  중복 출현한 보너스 번호 없음")

        return first_complete, bonus_complete

    def analyze_number_pattern_frequency(self):
        """특정 숫자 패턴의 출현 빈도 분석"""
        print("\n=== 숫자 패턴 출현 빈도 분석 ===")

        # 연속 숫자 패턴 분석
        consecutive_patterns = []
        same_digit_patterns = []
        valid_count = 0

        for numbers_str in self.df['first_prize_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if numbers and len(numbers) >= 2:
                valid_count += 1
                # 연속 숫자 개수
                consecutive_count = 0
                for i in range(len(numbers) - 1):
                    if abs(numbers[i + 1] - numbers[i]) == 1:
                        consecutive_count += 1
                consecutive_patterns.append(consecutive_count)

                # 같은 숫자 개수
                same_count = len(numbers) - len(set(numbers))
                same_digit_patterns.append(same_count)

        print(f"패턴 분석 (유효한 데이터: {valid_count}개):")

        if consecutive_patterns:
            print("\n연속 숫자 패턴 분석:")
            consecutive_counter = Counter(consecutive_patterns)
            for pattern, count in consecutive_counter.most_common():
                print(f"  {pattern}개 연속: {count}회")
        else:
            print("\n연속 숫자 패턴: 분석할 데이터 없음")

        if same_digit_patterns:
            print("\n중복 숫자 패턴 분석:")
            same_counter = Counter(same_digit_patterns)
            for pattern, count in same_counter.most_common():
                print(f"  {pattern}개 중복: {count}회")
        else:
            print("\n중복 숫자 패턴: 분석할 데이터 없음")

    def analyze_hot_cold_numbers(self):
        """핫/콜드 번호 분석"""
        print("\n=== 핫/콜드 번호 분석 ===")

        # 전체 기간 분석
        first_counter, bonus_counter = self.analyze_number_frequency()

        if not first_counter and not bonus_counter:
            print("분석할 데이터가 없습니다.")
            return

        # 최근 20회차 분석
        recent_data = self.df.tail(20) if len(self.df) >= 20 else self.df
        recent_first_numbers = []
        recent_bonus_numbers = []

        for numbers in recent_data['first_prize_numbers']:
            extracted = self.extract_individual_numbers(numbers)
            if extracted:
                recent_first_numbers.extend(extracted)

        for numbers in recent_data['bonus_numbers']:
            extracted = self.extract_individual_numbers(numbers)
            if extracted:
                recent_bonus_numbers.extend(extracted)

        recent_first_counter = Counter(recent_first_numbers)
        recent_bonus_counter = Counter(recent_bonus_numbers)

        print(f"전체 기간 vs 최근 {len(recent_data)}회차 비교:")

        if first_counter:
            print("\n1등 번호:")
            top_5_all = [num for num, _ in first_counter.most_common(5)]
            top_5_recent = [num for num, _ in recent_first_counter.most_common(5)]
            bottom_5_all = [num for num, _ in first_counter.most_common()[-5:]]
            cold_recent = [i for i in range(10) if recent_first_counter.get(i, 0) == 0]

            print(f"  전체 핫 번호 (상위 5개): {top_5_all}")
            print(f"  최근 핫 번호 (상위 5개): {top_5_recent}")
            print(f"  전체 콜드 번호 (하위 5개): {bottom_5_all}")
            print(f"  최근 콜드 번호: {cold_recent}")

        if bonus_counter:
            print("\n보너스 번호:")
            top_5_all = [num for num, _ in bonus_counter.most_common(5)]
            top_5_recent = [num for num, _ in recent_bonus_counter.most_common(5)]
            bottom_5_all = [num for num, _ in bonus_counter.most_common()[-5:]]
            cold_recent = [i for i in range(10) if recent_bonus_counter.get(i, 0) == 0]

            print(f"  전체 핫 번호 (상위 5개): {top_5_all}")
            print(f"  최근 핫 번호 (상위 5개): {top_5_recent}")
            print(f"  전체 콜드 번호 (하위 5개): {bottom_5_all}")
            print(f"  최근 콜드 번호: {cold_recent}")

    def plot_number_frequency(self):
        """번호 빈도 시각화"""
        first_counter, bonus_counter = self.analyze_number_frequency()

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 1등 번호 빈도
        if first_counter:
            numbers = list(range(10))
            frequencies = [first_counter.get(i, 0) for i in numbers]

            ax1.bar(numbers, frequencies, color='skyblue', alpha=0.7)
            ax1.set_title('1st Prize Number Frequency')
            ax1.set_xlabel('Number')
            ax1.set_ylabel('Frequency')
            ax1.set_xticks(numbers)

        # 보너스 번호 빈도
        if bonus_counter:
            numbers = list(range(10))
            frequencies = [bonus_counter.get(i, 0) for i in numbers]

            ax2.bar(numbers, frequencies, color='lightcoral', alpha=0.7)
            ax2.set_title('Bonus Number Frequency')
            ax2.set_xlabel('Number')
            ax2.set_ylabel('Frequency')
            ax2.set_xticks(numbers)

    def plot_position_frequency(self):
        """자리별 번호 빈도 시각화"""
        first_positions, bonus_positions = self.analyze_position_frequency()

        # 1등 번호 자리별 히트맵
        if any(first_positions):
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

            # 1등 번호 자리별 히트맵 데이터 준비
            first_heatmap_data = np.zeros((10, 7))  # 숫자 0-9, 자리 1-7
            for pos_idx, position_nums in enumerate(first_positions):
                if position_nums:
                    counter = Counter(position_nums)
                    for num, count in counter.items():
                        first_heatmap_data[num][pos_idx] = count

            # 1등 번호 히트맵
            sns.heatmap(first_heatmap_data,
                        xticklabels=[f'자리{i + 1}' for i in range(7)],
                        yticklabels=list(range(10)),
                        annot=True, fmt='g', cmap='Blues', ax=ax1)
            ax1.set_title('1등 번호 자리별 출현 빈도')
            ax1.set_xlabel('자리 위치')
            ax1.set_ylabel('숫자')

            # 보너스 번호 자리별 히트맵
            if any(bonus_positions):
                bonus_heatmap_data = np.zeros((10, 6))  # 숫자 0-9, 자리 1-6
                for pos_idx, position_nums in enumerate(bonus_positions):
                    if position_nums:
                        counter = Counter(position_nums)
                        for num, count in counter.items():
                            bonus_heatmap_data[num][pos_idx] = count

                sns.heatmap(bonus_heatmap_data,
                            xticklabels=[f'자리{i + 1}' for i in range(6)],
                            yticklabels=list(range(10)),
                            annot=True, fmt='g', cmap='Reds', ax=ax2)
                ax2.set_title('보너스 번호 자리별 출현 빈도')
                ax2.set_xlabel('자리 위치')
                ax2.set_ylabel('숫자')

            plt.tight_layout()
            plt.savefig('position_frequency.png', dpi=300, bbox_inches='tight')
            plt.show()

    def plot_hot_cold_comparison(self):
        """핫/콜드 번호 비교 차트"""
        first_counter, bonus_counter = self.analyze_number_frequency()

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # 1등 번호 전체 빈도
        numbers = list(range(10))
        first_frequencies = [first_counter.get(i, 0) for i in numbers]
        colors1 = ['red' if freq >= np.percentile(first_frequencies, 80) else
                   'blue' if freq <= np.percentile(first_frequencies, 20) else 'gray'
                   for freq in first_frequencies]

        ax1.bar(numbers, first_frequencies, color=colors1, alpha=0.7)
        ax1.set_title('1등 번호 핫/콜드 분석 (전체)')
        ax1.set_xlabel('숫자')
        ax1.set_ylabel('출현 횟수')
        ax1.set_xticks(numbers)

        # 보너스 번호 전체 빈도
        bonus_frequencies = [bonus_counter.get(i, 0) for i in numbers]
        colors2 = ['red' if freq >= np.percentile(bonus_frequencies, 80) else
                   'blue' if freq <= np.percentile(bonus_frequencies, 20) else 'gray'
                   for freq in bonus_frequencies]

        ax2.bar(numbers, bonus_frequencies, color=colors2, alpha=0.7)
        ax2.set_title('보너스 번호 핫/콜드 분석 (전체)')
        ax2.set_xlabel('숫자')
        ax2.set_ylabel('출현 횟수')
        ax2.set_xticks(numbers)

        # 최근 20회차 분석
        recent_data = self.df.tail(20)
        recent_first_numbers = []
        recent_bonus_numbers = []

        for numbers in recent_data['first_prize_numbers']:
            recent_first_numbers.extend(self.extract_individual_numbers(numbers))
        for numbers in recent_data['bonus_numbers']:
            recent_bonus_numbers.extend(self.extract_individual_numbers(numbers))

        recent_first_counter = Counter(recent_first_numbers)
        recent_bonus_counter = Counter(recent_bonus_numbers)

        # 최근 1등 번호
        recent_first_freq = [recent_first_counter.get(i, 0) for i in numbers]
        ax3.bar(numbers, recent_first_freq, color='orange', alpha=0.7)
        ax3.set_title('1등 번호 빈도 (최근 20회차)')
        ax3.set_xlabel('숫자')
        ax3.set_ylabel('출현 횟수')
        ax3.set_xticks(numbers)

        # 최근 보너스 번호
        recent_bonus_freq = [recent_bonus_counter.get(i, 0) for i in numbers]
        ax4.bar(numbers, recent_bonus_freq, color='green', alpha=0.7)
        ax4.set_title('보너스 번호 빈도 (최근 20회차)')
        ax4.set_xlabel('숫자')
        ax4.set_ylabel('출현 횟수')
        ax4.set_xticks(numbers)

        plt.tight_layout()
        plt.savefig('hot_cold_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()

    def analyze_patterns(self):
        """패턴 분석"""
        print("\n=== 패턴 분석 ===")

        # 연속된 숫자 패턴 분석
        consecutive_patterns = []

        for numbers_str in self.df['first_prize_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if len(numbers) >= 2:
                consecutive_count = 0
                for i in range(len(numbers) - 1):
                    if numbers[i + 1] == numbers[i] + 1:
                        consecutive_count += 1
                consecutive_patterns.append(consecutive_count)

        if consecutive_patterns:
            avg_consecutive = np.mean(consecutive_patterns)
            print(f"평균 연속 숫자 패턴: {avg_consecutive:.2f}")

        # 홀짝 패턴 분석
        odd_even_patterns = {'odd': 0, 'even': 0}

        for numbers_str in self.df['first_prize_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if numbers:
                last_digit = numbers[-1]  # 마지막 자리 숫자
                if last_digit % 2 == 0:
                    odd_even_patterns['even'] += 1
                else:
                    odd_even_patterns['odd'] += 1

        print(f"마지막 자리 홀수: {odd_even_patterns['odd']}회")
        print(f"마지막 자리 짝수: {odd_even_patterns['even']}회")

    def analyze_trends(self):
        """시간별 트렌드 분석"""
        print("\n=== 시간별 트렌드 분석 ===")

        if 'draw_date' in self.df.columns:
            # 날짜별 데이터 그룹화
            self.df['draw_date'] = pd.to_datetime(self.df['draw_date'], errors='coerce')

            # 월별 추첨 횟수
            monthly_draws = self.df.groupby(self.df['draw_date'].dt.to_period('M')).size()
            print("월별 추첨 횟수:")
            for period, count in monthly_draws.tail(12).items():
                print(f"  {period}: {count}회")

    def find_number_correlations(self):
        """숫자 간 상관관계 분석"""
        print("\n=== 숫자 상관관계 분석 ===")

        # 각 자리별 숫자 추출
        position_data = []

        for numbers_str in self.df['first_prize_numbers']:
            numbers = self.extract_individual_numbers(numbers_str)
            if len(numbers) >= 7:  # 7자리 숫자인 경우
                position_data.append(numbers[:7])

        if position_data:
            position_df = pd.DataFrame(position_data,
                                       columns=[f'Position_{i + 1}' for i in range(7)])

            # 상관관계 계산
            correlation_matrix = position_df.corr()

            print("자리별 숫자 상관관계 (높은 상관관계 상위 5개):")
            correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i + 1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    correlations.append((
                        correlation_matrix.columns[i],
                        correlation_matrix.columns[j],
                        abs(corr_value)
                    ))

            correlations.sort(key=lambda x: x[2], reverse=True)
            for pos1, pos2, corr in correlations[:5]:
                print(f"  {pos1} - {pos2}: {corr:.3f}")

    def predict_next_numbers(self):
        """다음 번호 예측 (통계적 접근)"""
        print("\n=== 다음 번호 예측 (참고용) ===")

        # 최근 패턴 분석
        recent_data = self.df.tail(20)  # 최근 20회차

        recent_numbers = []
        for numbers_str in recent_data['first_prize_numbers']:
            recent_numbers.extend(self.extract_individual_numbers(numbers_str))

        if recent_numbers:
            recent_counter = Counter(recent_numbers)
            print("최근 20회차에서 자주 나온 숫자:")
            for num, count in recent_counter.most_common(5):
                print(f"  숫자 {num}: {count}회")

            # 가장 적게 나온 숫자
            all_numbers = list(range(10))
            rare_numbers = [num for num in all_numbers if recent_counter.get(num, 0) <= 1]
            print(f"최근 잘 안 나온 숫자: {rare_numbers}")

        print("\n※ 이는 통계적 분석일 뿐이며, 실제 당첨을 보장하지 않습니다.")

    def generate_analysis_report(self, save_to_file=True):
        """종합 분석 보고서 생성"""
        report = []
        report.append("=" * 50)
        report.append("연금복권720+ 데이터 분석 보고서")
        report.append("=" * 50)
        report.append(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"분석 대상: {len(self.df)}개 회차")
        report.append("")

        # 기본 통계
        if not self.df.empty:
            min_round = self.df['round_number'].min()
            max_round = self.df['round_number'].max()
            report.append(f"회차 범위: {min_round}회 ~ {max_round}회")
            report.append("")

        # 번호 빈도 분석 결과 추가
        first_counter, bonus_counter = self.analyze_number_frequency()

        report.append("1등 당첨번호 빈도 분석:")
        for num, count in first_counter.most_common(10):
            report.append(f"  숫자 {num}: {count}회 출현")
        report.append("")

        report.append("보너스 당첨번호 빈도 분석:")
        for num, count in bonus_counter.most_common(10):
            report.append(f"  숫자 {num}: {count}회 출현")
        report.append("")

        # 완전 번호 빈도 분석
        first_complete, bonus_complete = self.analyze_complete_number_frequency()
        report.append("완전 번호 중복 출현:")
        duplicates_found = False
        for number, count in first_complete.most_common(10):
            if count > 1:
                report.append(f"  1등 {number}: {count}회")
                duplicates_found = True
        for number, count in bonus_complete.most_common(10):
            if count > 1:
                report.append(f"  보너스 {number}: {count}회")
                duplicates_found = True
        if not duplicates_found:
            report.append("  중복 출현한 완전 번호 없음")
        report.append("")

        # 패턴 분석 등 추가...

        report_text = "\n".join(report)
        print(report_text)

        if save_to_file:
            with open(f'lottery_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
                      'w', encoding='utf-8') as f:
                f.write(report_text)
            print("\n보고서가 파일로 저장되었습니다.")

    def export_analysis_data(self):
        """분석 결과를 CSV로 내보내기"""
        # 번호별 통계
        first_counter, bonus_counter = self.analyze_number_frequency()

        # 기본 번호별 통계
        analysis_data = []
        for i in range(10):
            analysis_data.append({
                'number': i,
                'first_prize_frequency': first_counter.get(i, 0),
                'bonus_frequency': bonus_counter.get(i, 0),
                'total_frequency': first_counter.get(i, 0) + bonus_counter.get(i, 0)
            })

        analysis_df = pd.DataFrame(analysis_data)
        filename1 = f'lottery_number_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        analysis_df.to_csv(filename1, index=False, encoding='utf-8-sig')
        print(f"기본 번호 분석 데이터가 {filename1}으로 저장되었습니다.")

        # 자리별 분석 데이터
        first_positions, bonus_positions = self.analyze_position_frequency()

        # 1등 자리별 데이터
        if any(first_positions):
            position_data = []
            for pos_idx, position_nums in enumerate(first_positions):
                if position_nums:
                    counter = Counter(position_nums)
                    for num in range(10):
                        position_data.append({
                            'position': pos_idx + 1,
                            'number': num,
                            'frequency': counter.get(num, 0),
                            'percentage': counter.get(num, 0) / len(position_nums) * 100 if position_nums else 0
                        })

            position_df = pd.DataFrame(position_data)
            filename2 = f'lottery_position_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            position_df.to_csv(filename2, index=False, encoding='utf-8-sig')
            print(f"자리별 분석 데이터가 {filename2}으로 저장되었습니다.")

        # 완전 번호 분석 데이터
        first_complete, bonus_complete = self.analyze_complete_number_frequency()

        complete_data = []
        for number, count in first_complete.most_common():
            complete_data.append({
                'type': '1등',
                'complete_number': number,
                'frequency': count
            })

        for number, count in bonus_complete.most_common():
            complete_data.append({
                'type': '보너스',
                'complete_number': number,
                'frequency': count
            })

        if complete_data:
            complete_df = pd.DataFrame(complete_data)
            filename3 = f'lottery_complete_numbers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            complete_df.to_csv(filename3, index=False, encoding='utf-8-sig')
            print(f"완전 번호 분석 데이터가 {filename3}으로 저장되었습니다.")


def main():
    """메인 실행 함수"""
    analyzer = LotteryAnalyzer()

    if analyzer.df.empty:
        print("분석할 데이터가 없습니다. 먼저 크롤링을 실행하세요.")
        return

    print("\n연금복권720+ 데이터 분석 도구")
    print("0. 데이터 구조 확인 (디버깅)")
    print("1. 번호 빈도 분석")
    print("2. 자리별 번호 출현 빈도")
    print("3. 완전 번호별 출현 횟수")
    print("4. 패턴 분석")
    print("5. 핫/콜드 번호 분석")
    print("6. 시간별 트렌드 분석")
    print("7. 숫자 상관관계 분석")
    print("8. 다음 번호 예측")
    print("9. 기본 빈도 차트")
    print("10. 자리별 빈도 히트맵")
    print("11. 핫/콜드 비교 차트")
    print("12. 종합 분석 보고서")
    print("13. 분석 데이터 내보내기")
    print("14. 전체 분석 실행")

    choice = input("선택하세요 (0-14): ").strip()

    if choice == '0':
        analyzer.debug_data_structure()
    elif choice == '1':
        analyzer.analyze_number_frequency()
    elif choice == '2':
        analyzer.analyze_position_frequency()
    elif choice == '3':
        analyzer.analyze_complete_number_frequency()
    elif choice == '4':
        analyzer.analyze_number_pattern_frequency()
    elif choice == '5':
        analyzer.analyze_hot_cold_numbers()
    elif choice == '6':
        analyzer.analyze_trends()
    elif choice == '7':
        analyzer.find_number_correlations()
    elif choice == '8':
        analyzer.predict_next_numbers()
    elif choice == '9':
        analyzer.plot_number_frequency()
    elif choice == '10':
        analyzer.plot_position_frequency()
    elif choice == '11':
        analyzer.plot_hot_cold_comparison()
    elif choice == '12':
        analyzer.generate_analysis_report()
    elif choice == '13':
        analyzer.export_analysis_data()
    elif choice == '14':
        print("전체 분석을 실행합니다...")
        analyzer.analyze_number_frequency()
        analyzer.analyze_position_frequency()
        analyzer.analyze_complete_number_frequency()
        analyzer.analyze_number_pattern_frequency()
        analyzer.analyze_hot_cold_numbers()
        analyzer.analyze_trends()
        analyzer.find_number_correlations()
        analyzer.predict_next_numbers()
        analyzer.plot_number_frequency()
        analyzer.plot_position_frequency()
        analyzer.plot_hot_cold_comparison()
        analyzer.generate_analysis_report()
        analyzer.export_analysis_data()
    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()