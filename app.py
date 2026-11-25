"""
GlamBooking - Main Flask Application
Web server, API endpoint, dan Admin Portal untuk Make Up Artist (MUA).
"""

from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from config import Config
from services.calendar_service import CalendarService
from services import db_service

# Inisialisasi Aplikasi Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi Database SQLite
db_service.init_db()

# Inisialisasi Service Kalender & Google Calendar API adapter
calendar_service = CalendarService(Config)

def login_required(f):
    """Decorator untuk memproteksi rute khusus admin MUA"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# RUTE CLIENT-FACING (LANDING PAGE)
# ============================================================================

@app.route('/')
def home():
    """Halaman utama landing page GlamBooking"""
    return render_template('index.html', config=Config)

@app.route('/api/availability', methods=['GET'])
def get_availability():
    """
    Endpoint untuk mengecek ketersediaan tanggal kalender.
    Query parameters:
      - year (int, default 2026)
      - month (int, default 11)
    """
    try:
        year = int(request.args.get('year', 2026))
        month = int(request.args.get('month', 11))
    except ValueError:
        return jsonify({'error': 'Parameter year dan month harus berupa angka'}), 400

    availability = calendar_service.get_month_availability(year=year, month=month)
    return jsonify({
        'year': year,
        'month': month,
        'google_calendar_connected': calendar_service.google_enabled,
        'availability': availability
    })

@app.route('/api/book', methods=['POST'])
def create_booking():
    """
    Endpoint untuk membuat reservasi / booking baru oleh klien.
    Menerima data JSON, menyimpan ke database SQLite,
    dan meneruskannya ke Google Calendar jika terhubung.
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body harus berformat JSON'}), 400

    required_fields = ['package_name', 'booking_date', 'customer_name', 'customer_phone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Field {field} wajib diisi.'}), 400

    result = calendar_service.create_booking(data)
    return jsonify(result), 200

# ============================================================================
# RUTE ADMIN PORTAL MUA (LOGIN & DASHBOARD)
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Halaman login admin MUA"""
    # Jika sudah login, langsung ke dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_user'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Username atau password salah. Silakan coba lagi."

    return render_template('admin/login.html', error=error)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Dashboard utama manajemen reservasi dan ketersediaan kalender MUA"""
    bookings = db_service.get_all_bookings()
    stats = db_service.get_dashboard_stats()
    success_msg = request.args.get('msg')

    return render_template(
        'admin/dashboard.html',
        bookings=bookings,
        stats=stats,
        google_connected=calendar_service.google_enabled,
        calendar_id=Config.GOOGLE_CALENDAR_ID,
        success_msg=success_msg
    )

@app.route('/admin/booking/<int:booking_id>/confirm', methods=['POST'])
@login_required
def admin_confirm_booking(booking_id):
    """Konfirmasi pembayaran DP klien"""
    db_service.update_booking_status(booking_id, 'confirmed')
    return redirect(url_for('admin_dashboard', msg="Pembayaran DP 50% berhasil dikonfirmasi!"))

@app.route('/admin/booking/<int:booking_id>/delete', methods=['POST'])
@login_required
def admin_delete_booking(booking_id):
    """Menghapus data reservasi"""
    db_service.delete_booking(booking_id)
    return redirect(url_for('admin_dashboard', msg="Reservasi berhasil dihapus."))

@app.route('/admin/calendar/update', methods=['POST'])
@login_required
def admin_update_calendar():
    """MUA mengatur status tanggal tertentu (Penuh / Kosong / Libur)"""
    target_date = request.form.get('target_date')
    new_status = request.form.get('new_status')

    status_labels = {
        'booked': 'Penuh',
        'available': 'Tersedia',
        'closed': 'Tutup'
    }
    label = status_labels.get(new_status, 'Tersedia')

    if target_date and new_status:
        db_service.set_calendar_override(target_date, new_status, label)

    return redirect(url_for('admin_dashboard', msg=f"Status tanggal {target_date} berhasil diubah menjadi '{label}'."))

@app.route('/admin/logout')
def admin_logout():
    """Logout session admin MUA"""
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    return redirect(url_for('admin_login'))

@app.route('/api/status', methods=['GET'])
def system_status():
    """Endpoint diagnostik sistem dan integrasi Google Calendar"""
    return jsonify({
        'status': 'healthy',
        'app_name': 'GlamBooking',
        'mua_name': Config.MUA_NAME,
        'google_calendar_enabled': calendar_service.google_enabled,
        'calendar_id': Config.GOOGLE_CALENDAR_ID
    })

if __name__ == '__main__':
    print("=" * 65)
    print("✨ GlamBooking Landing Page & MUA Portal berjalan di:")
    print("   👉 Website Klien : http://127.0.0.1:5000")
    print("   👉 Login MUA     : http://127.0.0.1:5000/admin/login")
    print("   👉 Default Login : user 'admin' | pass 'glam2026'")
    print("=" * 65)
    app.run(host='127.0.0.1', port=5000, debug=Config.DEBUG)
