/* ============================================================
   City Care Hospital - Main JavaScript
   ============================================================ */

// ─── TOAST NOTIFICATIONS ───────────────────────────────────
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer') || createToastContainer();
  const id = 'toast-' + Date.now();
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const bgClass = { success: 'bg-success', error: 'bg-danger', warning: 'bg-warning text-dark', info: 'bg-info' };
  const html = `
    <div id="${id}" class="toast align-items-center text-white ${bgClass[type] || 'bg-success'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body fs-6">
          ${icons[type] || '✅'} ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  const el = document.getElementById(id);
  const toast = new bootstrap.Toast(el, { delay: 4000 });
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toastContainer';
  div.className = 'toast-container position-fixed top-0 end-0 p-3';
  div.style.zIndex = '9999';
  document.body.appendChild(div);
  return div;
}

// ─── PAYMENT MODAL & LOGIC ───────────────────────────────────
let selectedPaymentMethod = null;

function selectPayment(method, btnEl) {
  selectedPaymentMethod = method;
  document.querySelectorAll('.payment-option').forEach(el => el.classList.remove('active'));
  btnEl.classList.add('active');
  const qrBox = document.getElementById('qrBox');
  if (qrBox) {
    if (method === 'UPI') {
      qrBox.style.display = 'block';
      // Trigger QR image load
      const qrImg = document.getElementById('qrImage');
      if (qrImg && qrImg.dataset.src) {
        qrImg.src = qrImg.dataset.src;
      }
    } else {
      qrBox.style.display = 'none';
    }
  }
}

function confirmPayment(actionUrl, redirectUrl) {
  if (!selectedPaymentMethod) {
    showToast('Please select a payment method.', 'warning');
    return;
  }
  document.getElementById('loadingOverlay') && (document.getElementById('loadingOverlay').classList.add('show'));

  const formData = new FormData();
  formData.append('payment_method', selectedPaymentMethod);

  fetch(actionUrl, { method: 'POST', body: formData })
    .then(r => r.json())
    .then(data => {
      document.getElementById('loadingOverlay') && (document.getElementById('loadingOverlay').classList.remove('show'));
      if (data.success) {
        showPaymentSuccess(data.message, data.transaction_id, redirectUrl);
      } else {
        showToast(data.message || 'Payment failed.', 'error');
      }
    })
    .catch(() => {
      document.getElementById('loadingOverlay') && (document.getElementById('loadingOverlay').classList.remove('show'));
      showToast('Network error. Please try again.', 'error');
    });
}

function showPaymentSuccess(message, txnId, redirectUrl) {
  const modal = document.getElementById('paymentSuccessModal');
  if (modal) {
    document.getElementById('successMessage') && (document.getElementById('successMessage').textContent = message);
    document.getElementById('txnIdDisplay') && (document.getElementById('txnIdDisplay').textContent = txnId);
    const btn = document.getElementById('viewReceiptBtn');
    if (btn) btn.onclick = () => { window.location.href = redirectUrl; };
    new bootstrap.Modal(modal).show();
  } else {
    alert(message + '\nTransaction ID: ' + txnId);
    if (redirectUrl) window.location.href = redirectUrl;
  }
}

// ─── FORM VALIDATION ───────────────────────────────────────
function validatePhone(input) {
  const val = input.value.replace(/\D/g, '');
  input.value = val;
  if (val.length > 10) input.value = val.slice(0, 10);
}

function validateAge(input) {
  const val = parseInt(input.value);
  if (val < 1) input.value = 1;
  if (val > 149) input.value = 149;
}

// ─── CONFIRM DELETE ───────────────────────────────────────
function confirmDelete(formId, entityName) {
  if (confirm(`Are you sure you want to delete this ${entityName}? This action cannot be undone.`)) {
    document.getElementById(formId).submit();
  }
}

// ─── AUTO-DISMISS ALERTS ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss flash alerts after 4s
  document.querySelectorAll('.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 4000);
  });

  // Activate Bootstrap tooltips
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // Set min date for date pickers to today
  document.querySelectorAll('input[type="date"]').forEach(el => {
    const today = new Date().toISOString().split('T')[0];
    el.setAttribute('min', today);
  });
});

// ─── PRINT RECEIPT ───────────────────────────────────────
function printReceipt() {
  window.print();
}
