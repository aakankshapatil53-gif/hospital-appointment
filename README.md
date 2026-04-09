# 🏥 City Care Hospital – Appointment Booking & Billing System
## Final Year Computer Science Project

---

## 📁 Project Structure

```
hospital_system/
├── app.py                        # Main Flask backend
├── requirements.txt              # Python dependencies
├── database.sql                  # MySQL database schema + seed data
├── README.md                     # This file
│
├── utils/
│   ├── __init__.py
│   └── pdf_generator.py          # PDF receipt generation
│
├── static/
│   ├── css/
│   │   └── style.css             # Main stylesheet
│   ├── js/
│   │   └── main.js               # JavaScript logic
│   ├── qrcodes/                  # (auto-used by qrcode library)
│   └── receipts/                 # (optional PDF storage)
│
└── templates/
    ├── base.html                 # Base layout with navbar
    ├── index.html                # Homepage
    ├── patient_register.html     # Patient registration
    ├── patient_login.html        # Patient login
    ├── patient_dashboard.html    # Patient's appointment list
    ├── book_appointment.html     # Book appointment form
    ├── appointment_payment.html  # Appointment payment (Cash/Card/UPI)
    ├── appointment_receipt.html  # Appointment receipt page
    ├── doctor_login.html         # Doctor login
    ├── doctor_dashboard.html     # Doctor's today appointments
    ├── add_prescription.html     # Write prescription form
    ├── prescription_payment.html # Prescription billing & payment
    ├── prescription_receipt.html # Prescription bill receipt
    ├── patient_history.html      # Patient prescription history
    ├── admin_login.html          # Admin login
    ├── admin_dashboard.html      # Admin overview with stats
    ├── admin_doctors.html        # Add/Delete doctors
    ├── admin_patients.html       # View/Delete patients
    ├── admin_appointments.html   # View/Delete appointments
    └── admin_prescriptions.html  # View all prescriptions
```

---

## ⚙️ STEP-BY-STEP SETUP INSTRUCTIONS

### Step 1 – Install Python & MySQL

- Python 3.10 or higher: https://www.python.org/downloads/
- MySQL Server 8.0: https://dev.mysql.com/downloads/installer/
- MySQL Workbench (optional but helpful): https://dev.mysql.com/downloads/workbench/

---

### Step 2 – Install Python Dependencies

Open Command Prompt or Terminal inside the `hospital_system` folder:

```bash
pip install -r requirements.txt
```

This installs:
- Flask (web framework)
- mysql-connector-python (MySQL driver)
- qrcode + Pillow (QR code generation)
- reportlab (PDF generation)

---

### Step 3 – Set Up the MySQL Database

1. Open MySQL Workbench or MySQL command line
2. Run the following command:

```sql
SOURCE /path/to/hospital_system/database.sql;
```

Or paste the contents of `database.sql` directly into MySQL Workbench and execute.

This will:
- Create the `hospital_db` database
- Create all 8 tables with proper foreign keys
- Insert sample doctors, patients, time slots
- Create admin and doctor login accounts

---

### Step 4 – Configure Database Password in app.py

Open `app.py` and find this section (around line 17):

```python
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',        # ← Change this to your MySQL root password
        database='hospital_db'
    )
```

Replace `''` with your MySQL password. For example:
```python
password='mypassword123',
```

If your MySQL username is not `root`, change `user` as well.

---

### Step 5 – Run the Application

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open your browser and go to: **http://localhost:5000**

---

## 🔐 LOGIN CREDENTIALS

### Admin Login
- URL: http://localhost:5000/admin/login
- Username: `admin`
- Password: `admin123`

### Doctor Logins
| Doctor | Username | Password |
|--------|----------|----------|
| Dr. Rajesh Sharma (Cardiology) | `dr.rajesh` | `doctor123` |
| Dr. Priya Mehta (Dermatology) | `dr.priya` | `doctor123` |
| Dr. Amit Kulkarni (Orthopaedic) | `dr.amit` | `doctor123` |
| Dr. Sunita Patil (Neurology) | `dr.sunita` | `doctor123` |
| Dr. Vivek Joshi (General) | `dr.vivek` | `doctor123` |
| Dr. Kavita Desai (Pediatrics) | `dr.kavita` | `doctor123` |

### Patient Login
- Register at: http://localhost:5000/patient/register
- Login with your registered 10-digit phone number

---

## 🔄 COMPLETE WORKFLOW

### Patient Flow:
1. Register at `/patient/register` (name, age, phone, address)
2. After registration → redirected to Book Appointment
3. Select doctor, date, time slot → Book
4. Redirected to Payment page
5. Choose Cash / Card / UPI
6. For UPI → scan QR code → click Confirm Payment
7. Payment success popup → View Receipt
8. Download PDF receipt

### Doctor Flow:
1. Login at `/doctor/login`
2. View today's confirmed appointments
3. Click "Write Prescription" for a patient
4. Enter medicines, notes, consultation fee → Save
5. Patient/staff completes prescription payment
6. View prescription bill receipt + download PDF

### Admin Flow:
1. Login at `/admin/login`
2. Dashboard shows total stats and revenue
3. Manage Doctors: Add new doctor with login credentials
4. View Patients, Appointments, Prescriptions
5. Delete records as needed

---

## 💡 FEATURES SUMMARY

| Feature | Status |
|---------|--------|
| Patient Registration | ✅ |
| Patient Login (phone-based) | ✅ |
| Doctor Management | ✅ |
| Appointment Booking | ✅ |
| Duplicate Slot Prevention | ✅ |
| Cash/Card/UPI Payment | ✅ |
| UPI QR Code Generation | ✅ |
| Dummy Payment Simulation | ✅ |
| Appointment Status Logic | ✅ |
| Doctor Portal + Prescriptions | ✅ |
| Prescription Billing | ✅ |
| PDF Receipt (Appointment) | ✅ |
| PDF Receipt (Prescription) | ✅ |
| Admin Dashboard with Stats | ✅ |
| Admin CRUD Operations | ✅ |
| Form Validation | ✅ |
| Error Handling | ✅ |
| Bootstrap 5 Professional UI | ✅ |
| Toast Notifications | ✅ |

---

## 🛠️ TROUBLESHOOTING

**Error: mysql.connector.errors.ProgrammingError**
→ Wrong MySQL password in `app.py`. Fix the `password=` field.

**Error: ModuleNotFoundError: No module named 'flask'**
→ Run: `pip install -r requirements.txt`

**Error: Access denied for user 'root'@'localhost'**
→ Check your MySQL username/password. Try running MySQL as admin.

**Port 5000 already in use**
→ Change the last line in `app.py`:
```python
app.run(debug=True, port=5001)
```

**QR code not showing**
→ Make sure `Pillow` is installed: `pip install Pillow`

---

## 📦 TECHNOLOGIES USED

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Backend | Python 3, Flask |
| Database | MySQL 8.0 |
| PDF Generation | ReportLab |
| QR Code | qrcode + Pillow |
| Icons | Bootstrap Icons |
| Fonts | Google Fonts (Nunito + Lato) |

---

*City Care Hospital Management System — Final Year CS Project*
