#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
연금복권 패턴 분석 시스템 설정 파일
"""

import os
from datetime import timedelta

# 기본 디렉토리 설정
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """기본 설정 클래스"""

    # Flask 기본 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pension-lottery-analysis-secret-key-2025'

    # 디렉토리 설정
    LOTTERY_DATA_DIR = os.path.join(basedir, 'lottery_data')
    ANALYSIS_RESULTS_DIR = os.path.join(basedir, 'analysis_results')
    CHARTS_DIR = os.path.join(basedir, 'charts')
    LOGS_DIR = os.path.join(basedir, 'logs')
    STATIC_DIR = os.path.join(basedir, 'static')
    TEMPLATES_DIR = os.path.join(basedir, 'templates')

    # 로깅 설정
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    # Flask 애플리케이션 설정
    JSON_AS_ASCII = False  # 한글 지원
    JSONIFY_PRETTYPRINT_REGULAR = True
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)

    # 업로드 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')

    # 세션 설정
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # HTTPS에서 True로 설정
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # 크롤링 설정
    CRAWLING_DELAY = 2  # 초 단위
    CRAWLING_TIMEOUT = 30  # 초 단위
    CRAWLING_MAX_RETRIES = 3

    # 분석 설정
    ANALYSIS_BATCH_SIZE = 100
    CHART_DPI = 300
    CHART_FIGURE_SIZE = (12, 8)

    # 캐시 설정
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5분

    # 데이터베이스 설정 (향후 확장용)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    @staticmethod
    def init_app(app):
        """애플리케이션 초기화"""
        # 필요한 디렉토리 생성
        directories = [
            app.config['LOTTERY_DATA_DIR'],
            app.config['ANALYSIS_RESULTS_DIR'],
            app.config['CHARTS_DIR'],
            app.config['LOGS_DIR'],
            app.config['UPLOAD_FOLDER']
        ]

        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except PermissionError:
                print(f"경고: {directory} 디렉토리 생성 권한이 없습니다.")
            except Exception as e:
                print(f"경고: {directory} 디렉토리 생성 실패: {e}")


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    TESTING = False

    # 개발 환경 특화 설정
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False

    # 로깅 레벨 상세화
    LOG_LEVEL = 'DEBUG'

    # 크롤링 설정 (개발 시 빠르게)
    CRAWLING_DELAY = 1
    CRAWLING_TIMEOUT = 15

    # 개발용 데이터베이스
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'dev_data.sqlite')


class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False

    # 테스트용 디렉토리
    LOTTERY_DATA_DIR = os.path.join(basedir, 'test_data')
    ANALYSIS_RESULTS_DIR = os.path.join(basedir, 'test_results')
    CHARTS_DIR = os.path.join(basedir, 'test_charts')
    LOGS_DIR = os.path.join(basedir, 'test_logs')

    # 테스트용 데이터베이스
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite://'

    # 테스트 시 빠른 실행
    CRAWLING_DELAY = 0.1
    CRAWLING_TIMEOUT = 5
    CRAWLING_MAX_RETRIES = 1


class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    TESTING = False

    # 보안 강화
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # 로깅 레벨
    LOG_LEVEL = 'INFO'

    # 운영용 데이터베이스
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'prod_data.sqlite')

    # 크롤링 설정 (서버 부하 고려)
    CRAWLING_DELAY = 3
    CRAWLING_TIMEOUT = 60

    # 캐시 설정 강화
    CACHE_DEFAULT_TIMEOUT = 600  # 10분

    @classmethod
    def init_app(cls, app):
        """운영 환경 초기화"""
        Config.init_app(app)

        # 운영 환경 로깅 설정
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists(app.config['LOGS_DIR']):
            os.makedirs(app.config['LOGS_DIR'])

        file_handler = RotatingFileHandler(
            os.path.join(app.config['LOGS_DIR'], 'lottery_analysis.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s: %(message)s'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('연금복권 분석 시스템 시작')


class HerokuConfig(ProductionConfig):
    """Heroku 배포 설정"""
    SSL_REDIRECT = True

    @classmethod
    def init_app(cls, app):
        """Heroku 환경 초기화"""
        ProductionConfig.init_app(app)

        # Heroku 로깅
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class DockerConfig(ProductionConfig):
    """Docker 컨테이너 설정"""

    @classmethod
    def init_app(cls, app):
        """Docker 환경 초기화"""
        ProductionConfig.init_app(app)

        # Docker 로깅
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


# 설정 매핑
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


# 현재 설정 가져오기
def get_config():
    """현재 환경의 설정을 반환"""
    config_name = os.environ.get('FLASK_CONFIG') or 'default'
    return config[config_name]


# 설정 검증
def validate_config(config_obj):
    """설정 값 검증"""
    required_dirs = [
        'LOTTERY_DATA_DIR',
        'ANALYSIS_RESULTS_DIR',
        'CHARTS_DIR',
        'LOGS_DIR'
    ]

    for dir_key in required_dirs:
        if not hasattr(config_obj, dir_key):
            raise ValueError(f"필수 디렉토리 설정이 없습니다: {dir_key}")

    # 크롤링 설정 검증
    if config_obj.CRAWLING_DELAY < 0:
        raise ValueError("CRAWLING_DELAY는 0 이상이어야 합니다.")

    if config_obj.CRAWLING_TIMEOUT < 1:
        raise ValueError("CRAWLING_TIMEOUT은 1 이상이어야 합니다.")

    return True


# 환경별 설정 출력
def print_config_info(config_name='default'):
    """현재 설정 정보 출력"""
    config_obj = config[config_name]

    print(f"\n=== {config_name.upper()} 환경 설정 ===")
    print(f"DEBUG: {config_obj.DEBUG}")
    print(f"TESTING: {config_obj.TESTING}")
    print(f"LOG_LEVEL: {config_obj.LOG_LEVEL}")
    print(f"CRAWLING_DELAY: {config_obj.CRAWLING_DELAY}초")
    print(f"CRAWLING_TIMEOUT: {config_obj.CRAWLING_TIMEOUT}초")
    print(f"CHARTS_DIR: {config_obj.CHARTS_DIR}")
    print("=" * 40)


if __name__ == "__main__":
    # 설정 테스트
    import sys

    if len(sys.argv) > 1:
        config_name = sys.argv[1]
    else:
        config_name = 'development'

    if config_name in config:
        try:
            config_obj = config[config_name]()
            validate_config(config_obj)
            print_config_info(config_name)
            print("✅ 설정 검증 성공")
        except Exception as e:
            print(f"❌ 설정 검증 실패: {e}")
    else:
        print(f"❌ 잘못된 설정명: {config_name}")
        print(f"사용 가능한 설정: {list(config.keys())}")