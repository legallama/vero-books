import uuid
from datetime import datetime
from app.extensions import db

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    ssn_last4 = db.Column(db.String(4))
    
    pay_type = db.Column(db.String(20), default='SALARY') # SALARY, HOURLY
    pay_rate = db.Column(db.Numeric(15, 2), default=0.00)
    pay_frequency = db.Column(db.String(20), default='BIWEEKLY') # WEEKLY, BIWEEKLY, MONTHLY
    
    status = db.Column(db.String(20), default='ACTIVE') # ACTIVE, INACTIVE, TERMINATED
    hired_at = db.Column(db.Date)
    
    # Tax Settings
    filing_status = db.Column(db.String(20), default='SINGLE')
    federal_allowances = db.Column(db.Integer, default=0)
    state_allowances = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    paychecks = db.relationship('Paycheck', back_populates='employee')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class PayrollRun(db.Model):
    __tablename__ = 'payroll_runs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    
    total_gross = db.Column(db.Numeric(15, 2), default=0.00)
    total_taxes = db.Column(db.Numeric(15, 2), default=0.00)
    total_net = db.Column(db.Numeric(15, 2), default=0.00)
    
    status = db.Column(db.String(20), default='DRAFT') # DRAFT, APPROVED, PAID, VOID
    journal_entry_id = db.Column(db.String(36), db.ForeignKey('journal_entries.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paychecks = db.relationship('Paycheck', back_populates='payroll_run')
    journal_entry = db.relationship('JournalEntry')

class Paycheck(db.Model):
    __tablename__ = 'paychecks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payroll_run_id = db.Column(db.String(36), db.ForeignKey('payroll_runs.id'), nullable=False)
    employee_id = db.Column(db.String(36), db.ForeignKey('employees.id'), nullable=False)
    
    gross_pay = db.Column(db.Numeric(15, 2), default=0.00)
    federal_tax = db.Column(db.Numeric(15, 2), default=0.00)
    state_tax = db.Column(db.Numeric(15, 2), default=0.00)
    social_security = db.Column(db.Numeric(15, 2), default=0.00)
    medicare = db.Column(db.Numeric(15, 2), default=0.00)
    other_deductions = db.Column(db.Numeric(15, 2), default=0.00)
    net_pay = db.Column(db.Numeric(15, 2), default=0.00)
    
    memo = db.Column(db.Text)
    
    employee = db.relationship('Employee', back_populates='paychecks')
    payroll_run = db.relationship('PayrollRun', back_populates='paychecks')
