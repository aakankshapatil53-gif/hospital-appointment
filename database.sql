-- ============================================================
-- Hospital Appointment Booking and Billing System
-- Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS hospital_db;
USE hospital_db;

-- ============================================================
-- TABLE: patients
-- ============================================================
CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL CHECK (age > 0 AND age < 150),
    phone VARCHAR(15) NOT NULL UNIQUE,
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: doctors
-- ============================================================
CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE: time_slots
-- ============================================================
CREATE TABLE IF NOT EXISTS time_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_time VARCHAR(20) NOT NULL
);

-- ============================================================
-- TABLE: appointments
-- ============================================================
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    date DATE NOT NULL,
    time_slot VARCHAR(20) NOT NULL,
    status ENUM('Pending Payment', 'Confirmed', 'Cancelled') DEFAULT 'Pending Payment',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE,
    UNIQUE KEY unique_slot (doctor_id, date, time_slot)
);

-- ============================================================
-- TABLE: appointment_payments
-- ============================================================
CREATE TABLE IF NOT EXISTS appointment_payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    payment_method ENUM('Cash', 'Card', 'UPI') NOT NULL,
    transaction_id VARCHAR(50) UNIQUE,
    amount DECIMAL(10,2) NOT NULL DEFAULT 500.00,
    status ENUM('Pending', 'Completed') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: prescriptions
-- ============================================================
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL,
    doctor_id INT NOT NULL,
    notes TEXT,
    medicines TEXT NOT NULL,
    consultation_fee DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: prescription_payments
-- ============================================================
CREATE TABLE IF NOT EXISTS prescription_payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    payment_method ENUM('Cash', 'Card', 'UPI') NOT NULL,
    transaction_id VARCHAR(50) UNIQUE,
    amount DECIMAL(10,2) NOT NULL,
    status ENUM('Pending', 'Completed') DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE: admin
-- ============================================================
CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- ============================================================
-- TABLE: doctor_users (for doctor login)
-- ============================================================
CREATE TABLE IF NOT EXISTS doctor_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id) ON DELETE CASCADE
);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default time slots
INSERT INTO time_slots (slot_time) VALUES
('09:00 AM'), ('09:30 AM'), ('10:00 AM'), ('10:30 AM'),
('11:00 AM'), ('11:30 AM'), ('12:00 PM'), ('02:00 PM'),
('02:30 PM'), ('03:00 PM'), ('03:30 PM'), ('04:00 PM'),
('04:30 PM'), ('05:00 PM');

-- Default admin (username: admin, password: admin123)
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

-- Sample Doctors
INSERT INTO doctors (name, specialization, phone) VALUES
(' Diksha Jadhav', 'Dermatologist', '9876543211'),
(' Shreyas Joshi', 'Neurologist', '9876543213'),
(' Kunal Pagare', 'General Physician', '9876543214'),
(' Sai Khairnar', 'Cardiologist', '9876543210'),
(' Aakanksha Patil', 'Pediatrician', '9876543215');

-- Doctor login accounts (password: doctor123 for all)
INSERT INTO doctor_users (doctor_id, username, password) VALUES
(1, 'dr.diksha', 'doctor123'),
(2, 'dr.shreyas', 'doctor123'),
(3, 'dr.kunal', 'doctor123'),
(4, 'dr.sai', 'doctor123'),
(5, 'dr.aakanksha', 'doctor123');

-- Sample Patients
INSERT INTO patients (name, age, phone, address) VALUES
('Bhumika Nikam', 20, '9123456789', 'Nashik, Maharashtra'),
('Aashish Ingle', 28, '9123456780', 'Pune, Maharashtra'),
('Krushna Chavan', 52, '9123456781', 'Mumbai, Maharashtra');
