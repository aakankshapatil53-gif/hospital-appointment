from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import mysql.connector
import qrcode
import os
import uuid
import json
from datetime import datetime
from utils.pdf_generator import generate_appointment_receipt, generate_prescription_receipt
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'hospital_secret_key_2024'

# ─────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='3306',        
        database='hospital_db',
        consume_results=True
    )

# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ═══════════════════════════════════════════════
# PATIENT MODULE
# ═══════════════════════════════════════════════

@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        age     = request.form.get('age', '').strip()
        phone   = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        # Validation
        if not all([name, age, phone, address]):
            return render_template('patient_register.html', error='All fields are required.')
        if not phone.isdigit() or len(phone) != 10:
            return render_template('patient_register.html', error='Phone number must be 10 digits.')
        if not age.isdigit() or int(age) <= 0 or int(age) >= 150:
            return render_template('patient_register.html', error='Enter a valid age.')

        db = get_db(); cur = db.cursor()
        try:
            cur.execute("INSERT INTO patients (name, age, phone, address) VALUES (%s,%s,%s,%s)",
                        (name, int(age), phone, address))
            db.commit()
            patient_id = cur.lastrowid
            session['patient_id'] = patient_id
            session['patient_name'] = name
            return redirect(url_for('book_appointment'))
        except mysql.connector.IntegrityError:
            return render_template('patient_register.html', error='Phone number already registered.')
        finally:
            cur.close(); db.close()
    return render_template('patient_register.html')


@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        if not phone.isdigit() or len(phone) != 10:
            return render_template('patient_login.html', error='Enter a valid 10-digit phone number.')
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM patients WHERE phone=%s", (phone,))
        patient = cur.fetchone()
        cur.close(); db.close()
        if patient:
            session['patient_id'] = patient['patient_id']
            session['patient_name'] = patient['name']
            return redirect(url_for('patient_dashboard'))
        return render_template('patient_login.html', error='Phone number not found. Please register.')
    return render_template('patient_login.html')


@app.route('/patient/dashboard')
def patient_dashboard():
    if 'patient_id' not in session:
        return redirect(url_for('patient_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, d.name AS doctor_name, d.specialization,
               ap.status AS pay_status, ap.amount, ap.payment_method, ap.transaction_id
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN appointment_payments ap ON a.appointment_id = ap.appointment_id
        WHERE a.patient_id = %s ORDER BY a.created_at DESC
    """, (session['patient_id'],))
    appointments = cur.fetchall()
    cur.close(); db.close()
    return render_template('patient_dashboard.html', appointments=appointments)


@app.route('/patient/logout')
def patient_logout():
    session.pop('patient_id', None)
    session.pop('patient_name', None)
    return redirect(url_for('index'))

# ─────────────────────────────────────────────
# BOOK APPOINTMENT
# ─────────────────────────────────────────────
@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'patient_id' not in session:
        return redirect(url_for('patient_login'))
    db = get_db(); cur = db.cursor(dictionary=True)

    if request.method == 'POST':
        doctor_id  = request.form.get('doctor_id')
        date       = request.form.get('date')
        time_slot  = request.form.get('time_slot')

        if not all([doctor_id, date, time_slot]):
            cur.execute("SELECT * FROM doctors"); doctors = cur.fetchall()
            cur.execute("SELECT * FROM time_slots"); slots = cur.fetchall()
            cur.close(); db.close()
            return render_template('book_appointment.html', doctors=doctors, slots=slots,
                                   error='All fields are required.')
        try:
            cur.execute("""INSERT INTO appointments (patient_id, doctor_id, date, time_slot)
                           VALUES (%s,%s,%s,%s)""",
                        (session['patient_id'], doctor_id, date, time_slot))
            db.commit()
            appointment_id = cur.lastrowid
            cur.close(); db.close()
            return redirect(url_for('appointment_payment', appointment_id=appointment_id))
        except mysql.connector.IntegrityError:
            cur.execute("SELECT * FROM doctors"); doctors = cur.fetchall()
            cur.execute("SELECT * FROM time_slots"); slots = cur.fetchall()
            cur.close(); db.close()
            return render_template('book_appointment.html', doctors=doctors, slots=slots,
                                   error='This time slot is already booked for the selected doctor.')

    cur.execute("SELECT * FROM doctors"); doctors = cur.fetchall()
    cur.execute("SELECT * FROM time_slots"); slots = cur.fetchall()
    cur.close(); db.close()
    return render_template('book_appointment.html', doctors=doctors, slots=slots)

# ─────────────────────────────────────────────
# APPOINTMENT PAYMENT
# ─────────────────────────────────────────────
@app.route('/appointment/payment/<int:appointment_id>', methods=['GET', 'POST'])
def appointment_payment(appointment_id):
    if 'patient_id' not in session:
        return redirect(url_for('patient_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, p.name AS patient_name, d.name AS doctor_name, d.specialization
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        WHERE a.appointment_id = %s
    """, (appointment_id,))
    appointment = cur.fetchone()
    cur.close(); db.close()
    if not appointment:
        return redirect(url_for('patient_dashboard'))
    return render_template('appointment_payment.html', appointment=appointment, amount=500)


@app.route('/appointment/pay/<int:appointment_id>', methods=['POST'])
def process_appointment_payment(appointment_id):
    if 'patient_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    payment_method = request.form.get('payment_method')
    transaction_id = 'TXN' + uuid.uuid4().hex[:10].upper()
    db = get_db(); cur = db.cursor()
    cur.execute("""INSERT INTO appointment_payments (appointment_id, payment_method, transaction_id, amount, status)
                   VALUES (%s,%s,%s,%s,'Completed')""",
                (appointment_id, payment_method, transaction_id, 500.00))
    cur.execute("UPDATE appointments SET status='Confirmed' WHERE appointment_id=%s", (appointment_id,))
    db.commit()
    cur.close(); db.close()
    return jsonify({'success': True, 'transaction_id': transaction_id, 'message': 'Payment Successful! Your appointment is confirmed.'})


@app.route('/generate-qr/<string:upi_id>/<int:amount>')
def generate_qr(upi_id, amount):
    upi_url = f"upi://pay?pa={upi_id}&pn=CityHospital&am={amount}&cu=INR&tn=AppointmentPayment"
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# ─────────────────────────────────────────────
# RECEIPTS
# ─────────────────────────────────────────────
@app.route('/appointment/receipt/<int:appointment_id>')
def appointment_receipt(appointment_id):
    if 'patient_id' not in session:
        return redirect(url_for('patient_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, p.name AS patient_name, p.phone, d.name AS doctor_name, d.specialization,
               ap.payment_method, ap.transaction_id, ap.amount, ap.status AS pay_status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN appointment_payments ap ON a.appointment_id = ap.appointment_id
        WHERE a.appointment_id = %s
    """, (appointment_id,))
    data = cur.fetchone()
    cur.close(); db.close()
    return render_template('appointment_receipt.html', data=data)


@app.route('/appointment/receipt/pdf/<int:appointment_id>')
def appointment_receipt_pdf(appointment_id):
    if 'patient_id' not in session:
        return redirect(url_for('patient_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, p.name AS patient_name, p.phone, d.name AS doctor_name, d.specialization,
               ap.payment_method, ap.transaction_id, ap.amount, ap.status AS pay_status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN appointment_payments ap ON a.appointment_id = ap.appointment_id
        WHERE a.appointment_id = %s
    """, (appointment_id,))
    data = cur.fetchone()
    cur.close(); db.close()
    pdf_buf = generate_appointment_receipt(data)
    return send_file(pdf_buf, as_attachment=True,
                     download_name=f'Appointment_Receipt_{appointment_id}.pdf',
                     mimetype='application/pdf')

# ═══════════════════════════════════════════════
# DOCTOR MODULE
# ═══════════════════════════════════════════════

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            return render_template('doctor_login.html', error='All fields required.')
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("""SELECT du.*, d.name AS doctor_name, d.specialization
                       FROM doctor_users du JOIN doctors d ON du.doctor_id = d.doctor_id
                       WHERE du.username=%s AND du.password=%s""", (username, password))
        doc = cur.fetchone()
        cur.close(); db.close()
        if doc:
            session['doctor_id'] = doc['doctor_id']
            session['doctor_name'] = doc['doctor_name']
            return redirect(url_for('doctor_dashboard'))
        return render_template('doctor_login.html', error='Invalid credentials.')
    return render_template('doctor_login.html')


@app.route('/doctor/dashboard')
def doctor_dashboard():
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))
    today = datetime.today().strftime('%Y-%m-%d')
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, p.name AS patient_name, p.age, p.phone,
               pr.prescription_id
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        LEFT JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
        WHERE a.doctor_id=%s AND a.date=%s AND a.status='Confirmed'
        ORDER BY a.time_slot
    """, (session['doctor_id'], today))
    appointments = cur.fetchall()
    cur.close(); db.close()
    return render_template('doctor_dashboard.html', appointments=appointments, today=today)


@app.route('/doctor/prescription/<int:appointment_id>', methods=['GET', 'POST'])
def add_prescription(appointment_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))
    db = get_db(); cur = db.cursor(dictionary=True)

    if request.method == 'POST':
        medicines        = request.form.get('medicines', '').strip()
        notes            = request.form.get('notes', '').strip()
        consultation_fee = request.form.get('consultation_fee', '').strip()
        if not medicines or not consultation_fee:
            cur.execute("SELECT a.*, p.name AS patient_name FROM appointments a JOIN patients p ON a.patient_id=p.patient_id WHERE a.appointment_id=%s", (appointment_id,))
            appt = cur.fetchone(); cur.close(); db.close()
            return render_template('add_prescription.html', appointment=appt, error='Medicines and fee required.')
        cur.execute("""INSERT INTO prescriptions (appointment_id, doctor_id, medicines, notes, consultation_fee)
                       VALUES (%s,%s,%s,%s,%s)""",
                    (appointment_id, session['doctor_id'], medicines, notes, float(consultation_fee)))
        db.commit()
        cur.close(); db.close()
        return redirect(url_for('prescription_saved', appointment_id=appointment_id))

    cur.execute("""SELECT a.*, p.name AS patient_name, p.age, d.specialization
                   FROM appointments a JOIN patients p ON a.patient_id=p.patient_id
                   JOIN doctors d ON a.doctor_id=d.doctor_id
                   WHERE a.appointment_id=%s""", (appointment_id,))
    appt = cur.fetchone(); cur.close(); db.close()
    return render_template('add_prescription.html', appointment=appt)


@app.route('/doctor/prescription-saved/<int:appointment_id>')
def prescription_saved(appointment_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""SELECT a.*, p.name AS patient_name, p.age, pr.prescription_id, pr.medicines, pr.notes, pr.consultation_fee
                   FROM appointments a
                   JOIN patients p ON a.patient_id = p.patient_id
                   LEFT JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
                   WHERE a.appointment_id = %s""", (appointment_id,))
    appt = cur.fetchone()
    cur.close(); db.close()
    return render_template('prescription_saved.html', appointment=appt)


@app.route('/doctor/patient-history/<int:patient_id>')
def patient_history(patient_id):
    if 'doctor_id' not in session:
        return redirect(url_for('doctor_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM patients WHERE patient_id=%s", (patient_id,))
    patient = cur.fetchone()
    # Full appointment history with prescription and billing info
    cur.execute("""
        SELECT a.appointment_id, a.date, a.time_slot, a.status,
               d.name AS doctor_name, d.specialization,
               pr.prescription_id, pr.medicines, pr.notes, pr.consultation_fee,
               pp.payment_method AS pres_payment_method, pp.transaction_id AS pres_txn, pp.amount AS pres_paid, pp.status AS pres_pay_status,
               ap.payment_method AS appt_payment_method, ap.transaction_id AS appt_txn, ap.amount AS appt_paid, ap.status AS appt_pay_status
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
        LEFT JOIN prescription_payments pp ON pr.prescription_id = pp.prescription_id
        LEFT JOIN appointment_payments ap ON a.appointment_id = ap.appointment_id
        WHERE a.patient_id=%s ORDER BY a.date DESC, a.time_slot DESC
    """, (patient_id,))
    history = cur.fetchall()
    cur.close(); db.close()
    return render_template('patient_history.html', patient=patient, history=history)


@app.route('/doctor/logout')
def doctor_logout():
    session.pop('doctor_id', None)
    session.pop('doctor_name', None)
    return redirect(url_for('index'))

# ─────────────────────────────────────────────
# PRESCRIPTION PAYMENT
# ─────────────────────────────────────────────
@app.route('/prescription/payment/<int:prescription_id>', methods=['GET', 'POST'])
def prescription_payment(prescription_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT pr.*, p.name AS patient_name, d.name AS doctor_name, a.date, a.time_slot
        FROM prescriptions pr
        JOIN appointments a ON pr.appointment_id = a.appointment_id
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON pr.doctor_id = d.doctor_id
        WHERE pr.prescription_id=%s
    """, (prescription_id,))
    prescription = cur.fetchone()
    cur.close(); db.close()
    return render_template('prescription_payment.html', prescription=prescription)


@app.route('/prescription/pay/<int:prescription_id>', methods=['POST'])
def process_prescription_payment(prescription_id):
    payment_method = request.form.get('payment_method')
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT consultation_fee FROM prescriptions WHERE prescription_id=%s", (prescription_id,))
    pres = cur.fetchone()
    transaction_id = 'PTXN' + uuid.uuid4().hex[:10].upper()
    cur.execute("""INSERT INTO prescription_payments (prescription_id, payment_method, transaction_id, amount, status)
                   VALUES (%s,%s,%s,%s,'Completed')""",
                (prescription_id, payment_method, transaction_id, pres['consultation_fee']))
    db.commit()
    cur.close(); db.close()
    return jsonify({'success': True, 'transaction_id': transaction_id, 'message': 'Payment Successful! Prescription Bill Paid.'})


@app.route('/prescription/receipt/<int:prescription_id>')
def prescription_receipt(prescription_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT pr.*, p.name AS patient_name, p.phone, d.name AS doctor_name, d.specialization,
               a.date, a.time_slot,
               pp.payment_method, pp.transaction_id, pp.amount AS paid_amount, pp.status AS pay_status
        FROM prescriptions pr
        JOIN appointments a ON pr.appointment_id = a.appointment_id
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON pr.doctor_id = d.doctor_id
        LEFT JOIN prescription_payments pp ON pr.prescription_id = pp.prescription_id
        WHERE pr.prescription_id=%s
    """, (prescription_id,))
    data = cur.fetchone()
    cur.close(); db.close()
    return render_template('prescription_receipt.html', data=data)


@app.route('/prescription/receipt/pdf/<int:prescription_id>')
def prescription_receipt_pdf(prescription_id):
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT pr.*, p.name AS patient_name, p.phone, d.name AS doctor_name, d.specialization,
               a.date, a.time_slot,
               pp.payment_method, pp.transaction_id, pp.amount AS paid_amount, pp.status AS pay_status
        FROM prescriptions pr
        JOIN appointments a ON pr.appointment_id = a.appointment_id
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON pr.doctor_id = d.doctor_id
        LEFT JOIN prescription_payments pp ON pr.prescription_id = pp.prescription_id
        WHERE pr.prescription_id=%s
    """, (prescription_id,))
    data = cur.fetchone()
    cur.close(); db.close()
    pdf_buf = generate_prescription_receipt(data)
    return send_file(pdf_buf, as_attachment=True,
                     download_name=f'Prescription_Receipt_{prescription_id}.pdf',
                     mimetype='application/pdf')

# ═══════════════════════════════════════════════
# ADMIN MODULE
# ═══════════════════════════════════════════════

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db(); cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        admin = cur.fetchone()
        cur.fetchall() 
        cur.close(); db.close()
        if admin:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error='Invalid credentials.')
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) AS cnt FROM patients"); patients_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM doctors"); doctors_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM appointments"); appt_count = cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM appointments WHERE status='Confirmed'"); confirmed_count = cur.fetchone()['cnt']
    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM appointment_payments WHERE status='Completed'"); appt_rev = cur.fetchone()['total']
    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM prescription_payments WHERE status='Completed'"); pres_rev = cur.fetchone()['total']
    cur.close(); db.close()
    return render_template('admin_dashboard.html',
        patients_count=patients_count, doctors_count=doctors_count,
        appt_count=appt_count, confirmed_count=confirmed_count,
        total_revenue=float(appt_rev) + float(pres_rev))


@app.route('/admin/doctors', methods=['GET', 'POST'])
def admin_doctors():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    if request.method == 'POST':
        name           = request.form.get('name', '').strip()
        specialization = request.form.get('specialization', '').strip()
        phone          = request.form.get('phone', '').strip()
        username       = request.form.get('username', '').strip()
        password       = request.form.get('password', '').strip()
        if not all([name, specialization, phone, username, password]):
            cur.execute("SELECT * FROM doctors"); doctors = cur.fetchall()
            cur.close(); db.close()
            return render_template('admin_doctors.html', doctors=doctors, error='All fields required.')
        if not phone.isdigit() or len(phone) != 10:
            cur.execute("SELECT * FROM doctors"); doctors = cur.fetchall()
            cur.close(); db.close()
            return render_template('admin_doctors.html', doctors=doctors, error='Invalid phone number.')
        try:
            cur.execute("INSERT INTO doctors (name, specialization, phone) VALUES (%s,%s,%s)", (name, specialization, phone))
            db.commit()
            doc_id = cur.lastrowid
            cur.execute("INSERT INTO doctor_users (doctor_id, username, password) VALUES (%s,%s,%s)", (doc_id, username, password))
            db.commit()
        except mysql.connector.IntegrityError:
            cur.execute("SELECT * FROM doctors"); doctors = cur.fetchall()
            cur.close(); db.close()
            return render_template('admin_doctors.html', doctors=doctors, error='Phone or username already exists.')
    cur.execute("SELECT * FROM doctors ORDER BY created_at DESC"); doctors = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin_doctors.html', doctors=doctors)


@app.route('/admin/doctors/delete/<int:doctor_id>', methods=['POST'])
def delete_doctor(doctor_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor()
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    cur.fetchall()
    cur.execute("DELETE FROM prescription_payments WHERE prescription_id IN "
                "(SELECT prescription_id FROM prescriptions WHERE doctor_id=%s)", (doctor_id,))
    cur.fetchall()
    cur.execute("DELETE FROM prescriptions WHERE doctor_id=%s", (doctor_id,))
    cur.fetchall()
    cur.execute("DELETE FROM appointment_payments WHERE appointment_id IN "
                "(SELECT appointment_id FROM appointments WHERE doctor_id=%s)", (doctor_id,))
    cur.fetchall()
    cur.execute("DELETE FROM appointments WHERE doctor_id=%s", (doctor_id,))
    cur.fetchall()
    cur.execute("DELETE FROM doctor_users WHERE doctor_id=%s", (doctor_id,))
    cur.fetchall()
    cur.execute("DELETE FROM doctors WHERE doctor_id=%s", (doctor_id,))
    cur.fetchall()
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    cur.fetchall()
    db.commit(); cur.close(); db.close()
    return redirect(url_for('admin_doctors'))

@app.route('/admin/patients')
def admin_patients():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM patients ORDER BY created_at DESC")
    patients = cur.fetchall(); cur.close(); db.close()
    return render_template('admin_patients.html', patients=patients)


@app.route('/admin/patients/delete/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor()
    # Disable FK checks, delete, re-enable
    cur.execute("SET FOREIGN_KEY_CHECKS=0")
    cur.fetchall()
    cur.execute("DELETE FROM prescription_payments WHERE prescription_id IN "
                "(SELECT prescription_id FROM prescriptions WHERE appointment_id IN "
                "(SELECT appointment_id FROM appointments WHERE patient_id=%s))", (patient_id,))
    cur.fetchall()
    cur.execute("DELETE FROM prescriptions WHERE appointment_id IN "
                "(SELECT appointment_id FROM appointments WHERE patient_id=%s)", (patient_id,))
    cur.fetchall()
    cur.execute("DELETE FROM appointment_payments WHERE appointment_id IN "
                "(SELECT appointment_id FROM appointments WHERE patient_id=%s)", (patient_id,))
    cur.fetchall()
    cur.execute("DELETE FROM appointments WHERE patient_id=%s", (patient_id,))
    cur.fetchall()
    cur.execute("DELETE FROM patients WHERE patient_id=%s", (patient_id,))
    cur.fetchall()
    cur.execute("SET FOREIGN_KEY_CHECKS=1")
    cur.fetchall()
    db.commit(); cur.close(); db.close()
    return redirect(url_for('admin_patients'))


@app.route('/admin/appointments/delete/<int:appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor()
    # Delete child records first, then parent
    cur.execute("DELETE FROM prescription_payments WHERE prescription_id IN "
                "(SELECT prescription_id FROM prescriptions WHERE appointment_id=%s)", (appointment_id,))
    cur.fetchall()
    cur.execute("DELETE FROM prescriptions WHERE appointment_id=%s", (appointment_id,))
    cur.fetchall()
    cur.execute("DELETE FROM appointment_payments WHERE appointment_id=%s", (appointment_id,))
    cur.fetchall()
    cur.execute("DELETE FROM appointments WHERE appointment_id=%s", (appointment_id,))
    cur.fetchall()
    db.commit(); cur.close(); db.close()
    return redirect(url_for('admin_appointments'))

@app.route('/admin/prescriptions')
def admin_prescriptions():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
    SELECT pr.*, p.name AS patient_name, d.name AS doctor_name, a.date,
           pp.payment_method, pp.transaction_id, pp.amount AS paid_amount, pp.status AS pay_status
    FROM prescriptions pr
    JOIN appointments a ON pr.appointment_id = a.appointment_id
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN doctors d ON pr.doctor_id = d.doctor_id
    LEFT JOIN prescription_payments pp ON pr.prescription_id = pp.prescription_id
    ORDER BY pr.prescription_id DESC
""")
    prescriptions = cur.fetchall(); cur.close(); db.close()
    return render_template('admin_prescriptions.html', prescriptions=prescriptions)

@app.route('/admin/billing/<int:prescription_id>', methods=['GET', 'POST'])
def admin_billing(prescription_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT pr.*, p.name AS patient_name, p.phone, d.name AS doctor_name, d.specialization,
               a.date, a.time_slot,
               pp.payment_method, pp.transaction_id, pp.amount AS paid_amount, pp.status AS pay_status
        FROM prescriptions pr
        JOIN appointments a ON pr.appointment_id = a.appointment_id
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON pr.doctor_id = d.doctor_id
        LEFT JOIN prescription_payments pp ON pr.prescription_id = pp.prescription_id
        WHERE pr.prescription_id=%s
    """, (prescription_id,))
    prescription = cur.fetchone()
    cur.close(); db.close()
    return render_template('admin_billing.html', prescription=prescription)


@app.route('/admin/billing/pay/<int:prescription_id>', methods=['POST'])
def admin_process_billing(prescription_id):
    if not session.get('admin'):
        return jsonify({'success': False, 'message': 'Not authorized'})
    payment_method = request.form.get('payment_method')
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT consultation_fee FROM prescriptions WHERE prescription_id=%s", (prescription_id,))
    pres = cur.fetchone()
    transaction_id = 'ATXN' + uuid.uuid4().hex[:10].upper()
    cur.execute("""INSERT INTO prescription_payments (prescription_id, payment_method, transaction_id, amount, status)
                   VALUES (%s,%s,%s,%s,'Completed')""",
                (prescription_id, payment_method, transaction_id, pres['consultation_fee']))
    db.commit()
    cur.close(); db.close()
    return jsonify({'success': True, 'transaction_id': transaction_id, 'message': 'Billing completed successfully!'})


@app.route('/admin/appointments')
def admin_appointments():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT a.*, p.name AS patient_name, d.name AS doctor_name,
               ap.payment_method, ap.transaction_id, ap.amount, ap.status AS pay_status
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
        LEFT JOIN appointment_payments ap ON a.appointment_id = ap.appointment_id
        ORDER BY a.appointment_id DESC
    """)
    appointments = cur.fetchall()
    cur.close(); db.close()
    return render_template('admin_appointments.html', appointments=appointments)


# ─────────────────────────────────────────────
# MEDICINE & DIAGNOSIS SUGGESTIONS API
# ─────────────────────────────────────────────

SPECIALTY_DATA = {
    'Orthopaedic': {
        'diagnoses': [
            'Fracture (Bone Break)', 'Arthritis', 'Joint Pain',
            'Muscle Strain / Ligament Injury', 'Back Pain / Slip Disc', 'Osteoporosis'
        ],
        'medicines': [
            'Tab. Paracetamol 500mg — 3 times daily for 5 days',
            'Tab. Ibuprofen 400mg — twice daily after meals for 5 days',
            'Tab. Diclofenac 50mg — twice daily for 3 days',
            'Tab. Calcium Carbonate 500mg — once daily for 30 days',
            'Tab. Vitamin D3 60000 IU — once weekly for 8 weeks',
        ]
    },
    'Cardiologist': {
        'diagnoses': [
            'Hypertension (High Blood Pressure)', 'Coronary Artery Disease',
            'Heart Failure', 'Arrhythmia (Irregular Heartbeat)', 'Angina (Chest Pain)'
        ],
        'medicines': [
            'Tab. Aspirin 75mg — once daily after breakfast',
            'Tab. Atorvastatin 10mg — once daily at night',
            'Tab. Metoprolol 25mg — once daily in the morning',
            'Tab. Amlodipine 5mg — once daily',
            'Tab. Clopidogrel 75mg — once daily after meals',
        ]
    },
    'Dermatologist': {
        'diagnoses': [
            'Acne', 'Eczema', 'Psoriasis', 'Fungal Infection', 'Dermatitis'
        ],
        'medicines': [
            'Clotrimazole 1% Cream — apply twice daily for 2 weeks',
            'Hydrocortisone 1% Cream — apply thin layer twice daily for 7 days',
            'Benzoyl Peroxide 2.5% Gel — apply at night for 4 weeks',
            'Ketoconazole 2% Shampoo / Cream — use as directed for 2 weeks',
            'Calamine Lotion — apply on affected area 3 times daily',
        ]
    },
    'Pediatrician': {
        'diagnoses': [
            'Common Cold', 'Fever', 'Diarrhea', 'Asthma', 'Chickenpox'
        ],
        'medicines': [
            'Syp. Paracetamol 125mg/5ml — 5ml every 6 hrs if fever (weight-based dose)',
            'Syp. Amoxicillin 125mg/5ml — twice daily for 5 days',
            'ORS Sachet — dissolve in 200ml water, give after each loose stool',
            'Salbutamol Inhaler 100mcg — 1–2 puffs as needed for wheeze',
            'Syp. Cetirizine 5mg/5ml — once daily at night for allergy',
        ]
    },
}

@app.route('/api/specialty-suggestions')
def specialty_suggestions():
    specialization = request.args.get('specialization', '').strip()
    data = SPECIALTY_DATA.get(specialization, {'diagnoses': [], 'medicines': []})
    return jsonify(data)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
