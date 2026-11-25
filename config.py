"""
GlamBooking - Configuration File
Mengatur konfigurasi aplikasi, metadata MUA, dan kredensial Google Calendar API.
"""

import os

class Config:
    # Pengaturan Aplikasi Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'glambooking-secret-key-2026')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1']

    # Profil Make Up Artist (MUA)
    MUA_NAME = os.environ.get('MUA_NAME', 'Alifya Beauty Studio')
    MUA_TITLE = "Professional Bridal & Editorial Makeup Artist"
    MUA_PHONE = "+62 812-3456-7890"
    MUA_EMAIL = "hello@glambooking.id"
    MUA_INSTAGRAM = "@glambooking.official"
    MUA_TIKTOK = "@glambooking.mua"
    MUA_CITY = "Jakarta & Sekitarnya"

    # Kredensial Login Admin MUA
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'glam2026')
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'glambooking.db')

    # Konfigurasi Google Calendar API
    # 1. Gunakan Service Account (credentials.json) atau OAuth 2.0 Client
    GOOGLE_CALENDAR_ENABLED = os.environ.get('GOOGLE_CALENDAR_ENABLED', 'False').lower() in ['true', '1']
    GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
    GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'credentials.json')
    GOOGLE_SCOPES = ['https://www.googleapis.com/auth/calendar']
