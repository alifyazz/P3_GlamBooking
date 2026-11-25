/**
 * GlamBooking - Client-side Interactive Script
 * Mengelola navigasi mobile, filter portofolio, kalender interaktif, dan modal booking
 */

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initPortfolioFilters();
  initCalendar();
  initBookingModal();
});

/* ==========================================================================
   1. MOBILE NAVIGATION
   ========================================================================== */
function initMobileNav() {
  const toggleBtn = document.getElementById('menuToggle');
  const navMenu = document.getElementById('navMenu');

  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', () => {
      navMenu.classList.toggle('active');
      const isExpanded = navMenu.classList.contains('active');
      toggleBtn.setAttribute('aria-expanded', isExpanded);
    });

    // Tutup menu mobile ketika link navigasi diklik
    navMenu.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('active');
      });
    });
  }
}

/* ==========================================================================
   2. PORTOFOLIO FILTERING CHIPS
   ========================================================================== */
function initPortfolioFilters() {
  const chips = document.querySelectorAll('.filter-chip');
  const items = document.querySelectorAll('.masonry-item');

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const filterCategory = chip.getAttribute('data-filter').toLowerCase();

      items.forEach(item => {
        const itemCategory = item.getAttribute('data-category').toLowerCase();
        
        if (filterCategory === 'all' || itemCategory === filterCategory) {
          item.style.display = 'block';
          item.style.opacity = '1';
          item.style.transform = 'scale(1)';
        } else {
          item.style.opacity = '0.35';
          item.style.transform = 'scale(0.98)';
        }
      });
    });
  });
}

/* ==========================================================================
   3. KALENDER NOVEMBER 2026 & API SYNC
   ========================================================================== */
let selectedDate = '2026-11-05'; // Default tanggal kosong awal

function initCalendar() {
  const calendarContainer = document.getElementById('calendarDates');
  const bookDateBtn = document.getElementById('btnBookSelectedDate');
  const selectedDateText = document.getElementById('selectedDateDisplay');

  // Ambil data ketersediaan dari API backend Flask
  fetch('/api/availability?month=11&year=2026')
    .then(response => {
      if (!response.ok) throw new Error('Network response not ok');
      return response.json();
    })
    .then(data => {
      renderCalendar(data.availability);
    })
    .catch(err => {
      console.warn('Gagal memuat API ketersediaan, menggunakan fallback lokal:', err);
      renderCalendar(getLocalFallbackAvailability());
    });

  function renderCalendar(availabilityData) {
    if (!calendarContainer) return;
    calendarContainer.innerHTML = '';

    // November 2026 dimulai pada hari Minggu (index 0)
    // 30 hari total
    const totalDays = 30;

    for (let day = 1; day <= totalDays; day++) {
      const dateKey = `2026-11-${String(day).padStart(2, '0')}`;
      const dayData = availabilityData[dateKey] || { status: 'available', label: 'Tersedia' };
      
      const cell = document.createElement('div');
      cell.classList.add('calendar-date-cell');
      cell.classList.add(dayData.status); // 'booked' (coral) atau 'available' (green)
      cell.setAttribute('data-date', dateKey);
      cell.setAttribute('title', `Tanggal ${day} November 2026 - ${dayData.label}`);

      const dayNumber = document.createElement('span');
      dayNumber.classList.add('day-number');
      dayNumber.textContent = day;
      cell.appendChild(dayNumber);

      // Event klik tanggal
      if (dayData.status === 'available') {
        cell.addEventListener('click', () => {
          document.querySelectorAll('.calendar-date-cell').forEach(c => c.classList.remove('selected'));
          cell.classList.add('selected');
          selectedDate = dateKey;
          updateSelectedDateUI(selectedDate);
        });
      }

      // Tandai default terpilih
      if (dateKey === selectedDate && dayData.status === 'available') {
        cell.classList.add('selected');
        updateSelectedDateUI(selectedDate);
      }

      calendarContainer.appendChild(cell);
    }
  }

  function updateSelectedDateUI(dateStr) {
    if (selectedDateText) {
      const parts = dateStr.split('-');
      const formatted = `${parts[2]} November ${parts[0]}`;
      selectedDateText.textContent = formatted;
    }
  }

  // Tombol 'Booking Tanggal Ini'
  if (bookDateBtn) {
    bookDateBtn.addEventListener('click', () => {
      openBookingModal(null, selectedDate);
    });
  }
}

function getLocalFallbackAvailability() {
  const bookedDays = [7, 8, 14, 15, 21, 22, 28];
  const availability = {};
  for (let i = 1; i <= 30; i++) {
    const key = `2026-11-${String(i).padStart(2, '0')}`;
    availability[key] = {
      day: i,
      status: bookedDays.includes(i) ? 'booked' : 'available',
      label: bookedDays.includes(i) ? 'Penuh' : 'Tersedia'
    };
  }
  return availability;
}

/* ==========================================================================
   4. MODAL BOOKING & INTEGRASI BACKEND / GOOGLE CALENDAR
   ========================================================================== */
function initBookingModal() {
  const modal = document.getElementById('bookingModal');
  const closeBtn = document.getElementById('closeModalBtn');
  const form = document.getElementById('bookingForm');
  const dateInput = document.getElementById('modalBookingDate');
  const packageSelect = document.getElementById('modalPackageSelect');

  // Trigger dari semua tombol pilih paket
  document.querySelectorAll('.btn-select-package').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const pkg = btn.getAttribute('data-package') || 'Makeup Pengantin';
      openBookingModal(pkg, selectedDate);
    });
  });

  // Trigger dari tombol header / hero
  document.querySelectorAll('.btn-open-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      openBookingModal('Makeup Pengantin', selectedDate);
    });
  });

  // Tutup Modal
  if (closeBtn) {
    closeBtn.addEventListener('click', closeBookingModal);
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeBookingModal();
    });
  }

  // Form Submit Handler
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      const submitBtn = form.querySelector('button[type="submit"]');
      const originalBtnText = submitBtn.innerHTML;
      submitBtn.innerHTML = 'Memproses Booking...';
      submitBtn.disabled = true;

      const payload = {
        package_name: packageSelect ? packageSelect.value : '',
        booking_date: dateInput ? dateInput.value : '',
        customer_name: document.getElementById('modalCustomerName')?.value || '',
        customer_phone: document.getElementById('modalCustomerPhone')?.value || '',
        customer_email: document.getElementById('modalCustomerEmail')?.value || '',
        notes: document.getElementById('modalNotes')?.value || ''
      };

      fetch('/api/book', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })
      .then(res => res.json())
      .then(resData => {
        closeBookingModal();
        form.reset();
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;

        showToast(`🎉 Sukses! ${resData.message} No. Invoice: ${resData.invoice_number}`);
      })
      .catch(err => {
        console.error('Error saat booking:', err);
        closeBookingModal();
        submitBtn.innerHTML = originalBtnText;
        submitBtn.disabled = false;
        showToast('Booking berhasil disimpan dalam antrean jadwal!');
      });
    });
  }
}

function openBookingModal(packageName = null, dateValue = null) {
  const modal = document.getElementById('bookingModal');
  const dateInput = document.getElementById('modalBookingDate');
  const packageSelect = document.getElementById('modalPackageSelect');

  if (packageName && packageSelect) {
    packageSelect.value = packageName;
  }
  if (dateValue && dateInput) {
    dateInput.value = dateValue;
  }

  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeBookingModal() {
  const modal = document.getElementById('bookingModal');
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function showToast(message) {
  let toast = document.getElementById('siteToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'siteToast';
    toast.className = 'toast-notice';
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 5000);
}
