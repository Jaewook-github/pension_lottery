#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 패턴 분석 Flask 애플리케이션 (완전 수정된 버전)
"""

import os
import json
import subprocess
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
from config import config

# 전역 변수
running_tasks = {}  # 실행 중인 작업 추적


def create_app(config_name=None):
    """Flask 애플리케이션 팩토리"""
    # 설정 로드
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 로깅 설정
    setup_logging(app)

    # 유틸리티 함수들 등록
    register_utility_functions(app)

    # 템플릿 필터 등록
    register_template_filters(app)

    # 라우트 등록
    register_routes(app)

    # 에러 핸들러 등록
    register_error_handlers(app)

    return app


def setup_logging(app):
    """로깅 설정"""
    if not app.debug:
        file_handler = logging.FileHandler(
            os.path.join(app.config['LOGS_DIR'], 'flask_app.log')
        )
        file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)


def register_utility_functions(app):
    """유틸리티 함수들 등록"""

    def load_json_file(filepath):
        """JSON 파일 로드"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            app.logger.error(f"JSON 파일 로드 실패 {filepath}: {e}")
        return None

    def get_file_modified_time(filepath):
        """파일 수정 시간 반환"""
        try:
            if os.path.exists(filepath):
                return datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        return None

    def run_python_script(script_name, task_id, lottery_type="720"):
        """Python 스크립트 실행 (백그라운드)"""
        try:
            app.logger.info(f"스크립트 실행 시작: {script_name} (타입: {lottery_type})")
            running_tasks[task_id] = {'status': 'running', 'start_time': datetime.now()}

            # 환경변수로 연금복권 타입 전달
            env = os.environ.copy()
            env['LOTTERY_TYPE'] = lottery_type

            result = subprocess.run(
                ['python', script_name],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env
            )

            if result.returncode == 0:
                running_tasks[task_id] = {
                    'status': 'completed',
                    'start_time': running_tasks[task_id]['start_time'],
                    'end_time': datetime.now(),
                    'output': result.stdout
                }
                app.logger.info(f"스크립트 실행 완료: {script_name}")
            else:
                running_tasks[task_id] = {
                    'status': 'failed',
                    'start_time': running_tasks[task_id]['start_time'],
                    'end_time': datetime.now(),
                    'error': result.stderr,
                    'output': result.stdout
                }
                app.logger.error(f"스크립트 실행 실패: {script_name} - {result.stderr}")

        except Exception as e:
            running_tasks[task_id] = {
                'status': 'failed',
                'start_time': running_tasks[task_id].get('start_time', datetime.now()),
                'end_time': datetime.now(),
                'error': str(e)
            }
            app.logger.error(f"스크립트 실행 중 예외 발생: {script_name} - {e}")

    # 함수들을 앱 컨텍스트에 등록
    app.load_json_file = load_json_file
    app.get_file_modified_time = get_file_modified_time
    app.run_python_script = run_python_script


def register_template_filters(app):
    """템플릿 필터 등록"""

    @app.template_filter('avg')
    def average_filter(values):
        """평균 계산 필터"""
        if not values:
            return 0
        return sum(values) / len(values)

    @app.template_filter('safe_divide')
    def safe_divide_filter(numerator, denominator):
        """안전한 나눗셈 필터"""
        if denominator == 0:
            return 0
        return numerator / denominator


def register_routes(app):
    """라우트 등록"""

    @app.route('/')
    def index():
        """메인 페이지"""
        # 분석 데이터 로드
        basic_stats = app.load_json_file(os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'statistics_report.json'))
        number_summary = app.load_json_file(
            os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'number_analysis_summary.json'))

        # 상태 정보
        status = get_analysis_status(app)

        return render_template('index.html',
                               basic_stats=basic_stats,
                               number_summary=number_summary,
                               status=status)

    @app.route('/dashboard')
    def dashboard():
        """대시보드 페이지"""
        # 모든 분석 데이터 로드
        data = {
            'basic_stats': app.load_json_file(
                os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'statistics_report.json')),
            'number_summary': app.load_json_file(
                os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'number_analysis_summary.json')),
            'number_frequency': app.load_json_file(
                os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'number_frequency.json')),
            'companion_numbers': app.load_json_file(
                os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'companion_numbers.json')),
            'number_trends': app.load_json_file(os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'number_trends.json'))
        }

        return render_template('dashboard.html', **data)

    @app.route('/analysis')
    def analysis():
        """분석 실행 페이지"""
        return render_template('analysis.html')

    @app.route('/patterns')
    def patterns():
        """패턴 분석 페이지"""
        # 패턴 분석 데이터 로드
        pattern_summary = app.load_json_file(
            os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'pattern_analysis_summary.json'))
        odd_even_patterns = app.load_json_file(
            os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'odd_even_patterns.json'))
        consecutive_patterns = app.load_json_file(
            os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'consecutive_patterns.json'))
        gap_patterns = app.load_json_file(os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'number_gaps.json'))

        return render_template('patterns.html',
                               pattern_summary=pattern_summary,
                               odd_even_patterns=odd_even_patterns,
                               consecutive_patterns=consecutive_patterns,
                               gap_patterns=gap_patterns)

    @app.route('/api/execute/<action>', methods=['POST'])
    def execute_action(action):
        """분석 작업 실행 API (연금복권 타입 지원)"""
        task_id = f"{action}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 요청 본문에서 연금복권 타입 가져오기
        request_data = request.get_json() or {}
        lottery_type = request_data.get('lottery_type', '720')

        script_map = {
            'crawl': 'pension_lottery_crawler.py',
            'analyze': 'pension_lottery_analyzer.py',
            'number_analyze': 'number_analyzer.py',
            'pattern_analyze': 'pattern_analyzer.py'
        }

        if action not in script_map:
            return jsonify({'status': 'error', 'message': '잘못된 작업입니다.'}), 400

        # 이미 실행 중인 같은 작업이 있는지 확인
        for tid, task in running_tasks.items():
            if tid.startswith(action) and task['status'] == 'running':
                return jsonify({'status': 'error', 'message': '이미 실행 중인 작업이 있습니다.', 'task_id': tid})

        # 백그라운드로 스크립트 실행 (연금복권 타입 포함)
        thread = threading.Thread(target=app.run_python_script, args=(script_map[action], task_id, lottery_type))
        thread.daemon = True
        thread.start()

        action_name = get_action_name(action)
        return jsonify({
            'status': 'started',
            'message': f'연금복권{lottery_type} {action_name} 작업이 시작되었습니다.',
            'task_id': task_id,
            'lottery_type': lottery_type
        })

    @app.route('/api/task/<task_id>')
    def get_task_status(task_id):
        """작업 상태 확인 API"""
        if task_id in running_tasks:
            task = running_tasks[task_id].copy()
            # datetime 객체를 문자열로 변환
            if 'start_time' in task and isinstance(task['start_time'], datetime):
                task['start_time'] = task['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            if 'end_time' in task and isinstance(task['end_time'], datetime):
                task['end_time'] = task['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            return jsonify(task)
        else:
            return jsonify({'status': 'not_found'}), 404

    @app.route('/api/status')
    def api_status():
        """전체 상태 확인 API"""
        return jsonify(get_analysis_status(app))

    @app.route('/api/charts')
    def get_available_charts():
        """사용 가능한 차트 목록 API"""
        charts = []
        chart_files = [
            'jo_frequency.png',
            'recent_jo_frequency.png',
            'last_digit_frequency.png',
            'number_frequency_by_position.png',
            'second_number_frequency.png',
            'winning_numbers_frequency.png',
            'duplicated_winning_numbers.png',
            'number_trends.png',
            'pattern_analysis.png',
            'gap_analysis.png'
        ]

        for filename in chart_files:
            filepath = os.path.join(app.config['CHARTS_DIR'], filename)
            if os.path.exists(filepath):
                charts.append({
                    'filename': filename,
                    'title': get_chart_title(filename),
                    'modified': app.get_file_modified_time(filepath)
                })

        # 동반 출현 히트맵 추가
        for pos in range(1, 7):
            filename = f'companion_heatmap_pos{pos}.png'
            filepath = os.path.join(app.config['CHARTS_DIR'], filename)
            if os.path.exists(filepath):
                charts.append({
                    'filename': filename,
                    'title': f'{pos}자리 동반 출현 히트맵',
                    'modified': app.get_file_modified_time(filepath)
                })

        return jsonify(charts)

    @app.route('/charts/<filename>')
    def serve_chart(filename):
        """차트 이미지 제공"""
        return send_from_directory(app.config['CHARTS_DIR'], filename)

    @app.route('/api/data/<data_type>')
    def get_analysis_data(data_type):
        """분석 데이터 API"""
        data_files = {
            'basic': 'statistics_report.json',
            'frequency': 'number_frequency.json',
            'companion': 'companion_numbers.json',
            'trends': 'number_trends.json',
            'summary': 'number_analysis_summary.json',
            'patterns': 'pattern_analysis_summary.json',
            'odd_even': 'odd_even_patterns.json',
            'consecutive': 'consecutive_patterns.json',
            'gaps': 'number_gaps.json',
            'combinations': 'jo_number_combinations.json'
        }

        if data_type not in data_files:
            return jsonify({'error': '잘못된 데이터 타입'}), 400

        filepath = os.path.join(app.config['ANALYSIS_RESULTS_DIR'], data_files[data_type])
        data = app.load_json_file(filepath)

        if data is None:
            return jsonify({'error': '데이터를 찾을 수 없습니다.'}), 404

        return jsonify(data)

    @app.route('/api/data/patterns')
    def get_pattern_data():
        """패턴 분석 데이터 API"""
        data_files = {
            'summary': 'pattern_analysis_summary.json',
            'odd_even': 'odd_even_patterns.json',
            'consecutive': 'consecutive_patterns.json',
            'gaps': 'number_gaps.json',
            'combinations': 'jo_number_combinations.json'
        }

        result = {}
        for key, filename in data_files.items():
            filepath = os.path.join(app.config['ANALYSIS_RESULTS_DIR'], filename)
            data = app.load_json_file(filepath)
            result[key] = data

        return jsonify(result)


def register_error_handlers(app):
    """에러 핸들러 등록"""

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error_code=404, error_message='페이지를 찾을 수 없습니다.'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error_code=500, error_message='서버 내부 오류가 발생했습니다.'), 500


def get_analysis_status(app):
    """분석 상태 확인 (수정된 버전)"""
    # 기본적으로 연금복권720+ 사용
    lottery_data_file = os.path.join(app.config['LOTTERY_DATA_DIR'], 'pension_lottery_720_all.csv')

    # 연금복권520 파일도 확인
    lottery_520_file = os.path.join(app.config['LOTTERY_DATA_DIR'], 'pension_lottery_520_all.csv')

    # 기존 파일명도 확인 (하위 호환성)
    legacy_file = os.path.join(app.config['LOTTERY_DATA_DIR'], 'pension_lottery_all.csv')

    basic_analysis_file = os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'statistics_report.json')
    number_analysis_file = os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'number_analysis_summary.json')
    pattern_analysis_file = os.path.join(app.config['ANALYSIS_RESULTS_DIR'], 'pattern_analysis_summary.json')

    return {
        'crawl_data_exists': os.path.exists(lottery_data_file) or os.path.exists(lottery_520_file) or os.path.exists(
            legacy_file),
        'lottery_720_exists': os.path.exists(lottery_data_file),
        'lottery_520_exists': os.path.exists(lottery_520_file),
        'legacy_data_exists': os.path.exists(legacy_file),
        'basic_analysis_exists': os.path.exists(basic_analysis_file),
        'number_analysis_exists': os.path.exists(number_analysis_file),
        'pattern_analysis_exists': os.path.exists(pattern_analysis_file),
        'last_crawl': app.get_file_modified_time(lottery_data_file) or app.get_file_modified_time(legacy_file),
        'last_crawl_520': app.get_file_modified_time(lottery_520_file),
        'last_analysis': app.get_file_modified_time(basic_analysis_file),
        'last_number_analysis': app.get_file_modified_time(number_analysis_file),
        'last_pattern_analysis': app.get_file_modified_time(pattern_analysis_file),
        'running_tasks': len([t for t in running_tasks.values() if t['status'] == 'running'])
    }


def get_chart_title(filename):
    """차트 파일명에서 제목 추출"""
    titles = {
        'jo_frequency.png': '조별 출현 빈도',
        'recent_jo_frequency.png': '최근 조별 출현 빈도',
        'last_digit_frequency.png': '끝자리 출현 빈도',
        'number_frequency_by_position.png': '자리별 숫자 출현 빈도',
        'second_number_frequency.png': '2등 번호 출현 빈도',
        'winning_numbers_frequency.png': '당첨번호 출현 빈도',
        'duplicated_winning_numbers.png': '중복 출현 당첨번호',
        'number_trends.png': '번호별 트렌드 점수',
        'pattern_analysis.png': '홀짝 패턴 분석',
        'gap_analysis.png': '간격 패턴 분석'
    }
    return titles.get(filename, filename)


def get_action_name(action):
    """작업명 반환"""
    names = {
        'crawl': '데이터 크롤링',
        'analyze': '기본 분석',
        'number_analyze': '번호별 분석',
        'pattern_analyze': '패턴 분석'
    }
    return names.get(action, action)


# 애플리케이션 실행
if __name__ == '__main__':
    # 설정에 따라 앱 생성
    app = create_app()

    # 개발 모드에서 실행
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config.get('DEBUG', True)
    )