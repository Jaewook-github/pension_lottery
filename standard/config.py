#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask 애플리케이션 설정 파일
"""

import os
from datetime import timedelta


class Config:
    """기본 설정 클래스"""

    # 기본 Flask 설정
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lottery-analysis-secret-key-2024'

    # 디렉토리 설정
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    LOTTERY_DATA_DIR = os.path.join(BASE_DIR, 'lottery_data')
    ANALYSIS_RESULTS_DIR = os.path.join(BASE_DIR, 'analysis_results')
    CHARTS_DIR = os.path.join(BASE_DIR, 'charts')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')

    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # 세션 설정
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    # 크롤링 설정
    CRAWL_DELAY = 1  # 크롤링 간 딜레이 (초)
    CRAWL_TIMEOUT = 30  # 크롤링 타임아웃 (초)

    # 분석 설정
    RECENT_ROUNDS_COUNT = 50  # 최근 트렌드 분석 회차 수
    CHART_DPI = 300  # 차트 해상도

    # 로깅 설정
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @staticmethod
    def init_app(app):
        """애플리케이션 초기화"""
        # 필요한 디렉토리 생성
        dirs = [
            Config.LOTTERY_DATA_DIR,
            Config.ANALYSIS_RESULTS_DIR,
            Config.CHARTS_DIR,
            Config.LOGS_DIR
        ]

        for directory in dirs:
            os.makedirs(directory, exist_ok=True)


class DevelopmentConfig(Config):
    """개발 환경 설정"""
    DEBUG = True
    ENV = 'development'


class ProductionConfig(Config):
    """운영 환경 설정"""
    DEBUG = False
    ENV = 'production'


class TestingConfig(Config):
    """테스트 환경 설정"""
    TESTING = True
    WTF_CSRF_ENABLED = False


# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}