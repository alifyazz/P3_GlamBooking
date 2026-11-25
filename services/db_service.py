"""
GlamBooking - Database Service Layer (SQLite)
Menyimpan data reservasi klien dan pengaturan tanggal kalender secara persisten.
"""

import sqlite3
import os
from datetime import datetime
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inisialisasi tabel SQLite dan data awal jika database baru dibuat"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabel Reservasi / Bookings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            package_name TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel Override Ketersediaan Kalender
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calendar_overrides (
            date_str TEXT PRIMARY KEY,
            status TEXT NOT NULL, -- 'available', 'booked', 'closed'
            label TEXT NOT NULL
        )
    """)

    # Cek apakah tabel bookings masih kosong, jika ya beri data demo
    cursor.execute("SELECT COUNT(*) FROM bookings")
    count = cursor.fetchone()[0]
    if count == 0:
        demo_bookings = [
            (
                "INV-GLAM-26110701",
                "Makeup Pengantin",
                "2026-11-07",
                "Aisyah Putri & Rizky",
                "081234567890",
                "aisyah.putri@email.com",
                "Akad & Resepsi di Hotel Mulia, siap jam 06:00 pagi",
                "confirmed"
            ),
            (
                "INV-GLAM-26111402",
                "Makeup Pengantin",
                "2026-11-14",
                "Clara Clarissa",
                "081987654321",
                "clara.c@email.com",
                "Sunda Siger Modern, butuh 2x retouch prosesi",
                "confirmed"
            ),
            (
                "INV-GLAM-26112003",
                "Makeup Wisuda",
                "2026-11-20",
                "Dina Rahmawati",
                "085712349999",
                "dina.rahma@email.com",
                "Wisuda UI Balairung, request look flawless peach natural",
                "pending"
            )
        ]
        cursor.executemany("""
            INSERT INTO bookings (
                invoice_number, package_name, booking_date, customer_name,
                customer_phone, customer_email, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_bookings)

    # Inisialisasi default slot penuh kalender (weekend) di calendar_overrides
    cursor.execute("SELECT COUNT(*) FROM calendar_overrides")
    override_count = cursor.fetchone()[0]
    if override_count == 0:
        default_booked_days = [7, 8, 14, 15, 21, 22, 28]
        for d in default_booked_days:
            date_str = f"2026-11-{d:02d}"
            cursor.execute("""
                INSERT OR REPLACE INTO calendar_overrides (date_str, status, label)
                VALUES (?, 'booked', 'Penuh')
            """, (date_str,))
        
        default_closed_days = [2, 9, 16, 23, 29]
        for d in default_closed_days:
            date_str = f"2026-11-{d:02d}"
            cursor.execute("""
                INSERT OR REPLACE INTO calendar_overrides (date_str, status, label)
                VALUES (?, 'closed', 'Tutup')
            """, (date_str,))

    conn.commit()
    conn.close()

def get_all_bookings():
    """Mengambil semua daftar reservasi, diurutkan dari yang terbaru"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM bookings ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    bookings = [dict(row) for row in rows]
    conn.close()
    return bookings

def add_booking(booking_data):
    """Menambahkan data reservasi baru"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (
            invoice_number, package_name, booking_date, customer_name,
            customer_phone, customer_email, notes, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        booking_data['invoice_number'],
        booking_data['package_name'],
        booking_data['booking_date'],
        booking_data['customer_name'],
        booking_data['customer_phone'],
        booking_data['customer_email'],
        booking_data.get('notes', ''),
        booking_data.get('status', 'pending')
    ))
    conn.commit()
    booking_id = cursor.lastrowid
    conn.close()
    return booking_id

def update_booking_status(booking_id, new_status):
    """Mengubah status reservasi (pending / confirmed / cancelled)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings SET status = ? WHERE id = ?
    """, (new_status, booking_id))
    conn.commit()
    conn.close()
    return True

def delete_booking(booking_id):
    """Menghapus data reservasi"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM bookings WHERE id = ?
    """, (booking_id,))
    conn.commit()
    conn.close()
    return True

def get_calendar_overrides():
    """Mengambil data custom status tanggal kalender"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date_str, status, label FROM calendar_overrides")
    rows = cursor.fetchall()
    overrides = {row['date_str']: {'status': row['status'], 'label': row['label']} for row in rows}
    conn.close()
    return overrides

def set_calendar_override(date_str, status, label):
    """MUA mengatur status tanggal tertentu (available / booked / closed)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO calendar_overrides (date_str, status, label)
        VALUES (?, ?, ?)
    """, (date_str, status, label))
    conn.commit()
    conn.close()
    return True

def get_dashboard_stats():
    """Mengambil ringkasan metrik dashboard untuk MUA"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'pending'")
    pending_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'confirmed'")
    confirmed_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM calendar_overrides WHERE status = 'booked'")
    booked_dates_count = cursor.fetchone()[0]

    conn.close()
    return {
        'total_bookings': total_bookings,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'booked_dates_count': booked_dates_count
    }
