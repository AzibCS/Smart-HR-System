import sqlite3 
import pandas as pd
import streamlit as st
import fitz

from datetime import datetime
from resume_parser import parse_resume
from payroll_logic import calculate_pay
from streamlit_option_menu import option_menu
from db_setup import init_db, DB_PATH

init_db()

def connectDB():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def add_employee(name, email, phone, base_salary, join_date=None):
    conn = connectDB()
    curs = conn.cursor()
    # using safe query method
    curs.execute("Insert into employees (name, email, phone, base_salary, join_date) values (?, ?, ?, ?, ?)",
                (name, email, phone, base_salary, join_date))
    conn.commit()
    empId = curs.lastrowid
    conn.close()
    return empId

def list_employees():
    conn = connectDB()
    df = pd.read_sql("Select * from employees", conn)
    conn.close()
    return df

def save_resume(empId, rawText, skills, expYears):
    conn =connectDB()
    cur =conn.cursor()
    cur.execute("Insert into resumes (employee_id, raw_text, skills, experience_years) values (?, ?, ?, ?)",
                (empId, rawText, ",".join(skills), expYears))
    conn.commit()
    conn.close()

def save_interview(name, email, date, time):
    conn = connectDB()
    cur = conn.cursor()
    cur.execute("Insert into interviews (candidate_name, candidate_email, scheduled_date, scheduled_time) values (?, ?, ?, ?)",
    (name, email, date, time.isoformat() if hasattr(time, "isoformat()") else str(time)))
    conn.commit()
    conn.close()

def save_payroll(employee_id, month, days_present, gross, tax, net):
    conn = connectDB()
    cur = conn.cursor()
    cur.execute("insert into payroll (employee_id, month, days_present, gross_pay, tax, net_pay) values (?, ?, ?, ?, ?, ?)",
                (employee_id, month, days_present, gross, tax, net))
    conn.commit()
    conn.close()

def get_payroll_summary():
    conn = connectDB()
    df = pd.read_sql("Select p.*, e.name from payroll p left join employees e on p.employee_id = e.id", conn)
    conn.close()
    return df

st.set_page_config(page_title="Smart HR System", layout="wide")
st.title("👩‍💼 Smart Recruitment & Payroll System")
#menu = st.sidebar.radio("Choose Section: ", ["Dashboard", "Resume Parser", "Interview Scheduler", "Payroll", "Employee"])

# Sidebar / Tabs
with st.sidebar:
    st.title("Side Bar Menu")
    menu = option_menu(
        menu_title="Choose Section:",
        options=["Dashboard", "Resume Parser", "Interview Scheduler", "Payroll", "Employee"],
        icons=["speedometer",          # Dashboard
            "file-earmark-text",    # Resume Parser
            "calendar-check",       # Interview Scheduler
            "currency-dollar",      # Payroll
            "people-fill" ],
        menu_icon="grid",
        default_index=0,
        orientation="vertical"
    )


if menu == "Resume Parser":
    st.header("📄 Upload and Parse Resume")
    uploaded =st.file_uploader("Upload Resume (txt or pdf)", type=["txt", "pdf"])
    if uploaded:
        text=""
        #for pdf files
        if uploaded.type == "application/pdf":
            read = uploaded.read()#.decode("utf-8", errors="ignore")
            with fitz.open(stream=read, filetype="pdf") as pdfdoc:
                for page in pdfdoc:
                    text += page.get_text("text") + "\n"
        # handle text file
        elif uploaded.type == "text/plain":
            text = uploaded.read().decode("utf-8", errors="ignore")

        result = parse_resume(text)
        st.json(result)

        # to save as aemployee (optional)
        st.subheader("Save parsed resume")
        col1, col2 = st.columns(2)
        with col1:
            emp = list_employees()
            empNames =  ["-- New Candidate --"] + emp["name"].tolist()
            selected = st.selectbox("Link to employee or create new", empNames)
            if selected == "-- New Candidate --":
                newName = st.text_input("Name", value=result.get("name") or "")
                newEmail = st.text_input("Email", value=(result.get("emails") or [""])[0])
                newPhone = st.text_input("Phone", value=(result.get("phones") or [""])[0])
                baseSalry = st.number_input("Basic Salary", min_value=0.0, value=30000.0)
                if st.button("Create Employee & Save Resume"):
                    empid = add_employee(newName, newEmail, newPhone, baseSalry , datetime.now())
                    save_resume(empid, text, result.get("skills", []), result.get("experience_years", 0))
                    st.success(f"Resume saved for Employee: {newName}, ID: {empid}")
            else:
                if st.button("Save Resume to select Employee"):
                    empData = emp[emp["name"] == selected].iloc[0]
                    save_resume(int(empData["id"]), text, result.get("skills", []), result.get("experience_years", 0))
                    st.success("Resume Data Saved")

elif menu == "Interview Scheduler":
    st.header("📅 Schedule Interview")
    with st.expander("Add Interview Details for a Person"):
        name = st.text_input("Candidate Name: ")
        email = st.text_input("Enter Email: ")
        date = st.date_input("Interview Date: ")
        time = st.time_input("Interview Time: ")
        if st.button("Save Schedule"):
            save_interview(name, email, date, time)
            st.success(f"Interview scheduled with {name} on {date} at {time}")

    # for sowing upcoming interview details
    st.subheader("Upcoming Interviews")
    conn = connectDB()
    df = pd.read_sql("select * from interviews order by scheduled_date desc", conn)
    conn.close()
    if not df.empty:
        df.columns = [col.replace("_", " ").title() for col in df.columns]
        st.dataframe(df)
        st.info("Above are the details of Upcoming Sceduled Interviews")
    else:
        st.info("No data found for upcoming scheduled interviews")

elif menu == "Payroll":
    st.header("💰 Payroll Calculator")
    st.subheader("Select Dashboard from SideBar to see Employee's Payroll Summary.")
    emp = list_employees()
    if emp.empty:
        st.info("No employees yet, add employee via employee tab")
    else:
        getEmp  = dict(zip(emp["name"], emp["id"]))
        selected = st.selectbox("Choose Employee", emp["name"].tolist())
        selectedRow = emp[emp["name"] == selected].iloc[0]
        salary = float(selectedRow["base_salary"] or 0.0)
        daysPresent = st.number_input("Days Present: ", min_value=0, max_value=30, value=30)
        taxRate = st.slider("Tax rate (%)", min_value=0.0, max_value=30.0, value=5.0)
        if st.button("Save & Calculate Payroll"):
            result = calculate_pay(salary, daysPresent, taxRate=taxRate/100)
            save_payroll(int(selectedRow["id"]), datetime.now().strftime("%Y-%m"), daysPresent, 
                         result["gross_pay"], result["tax"], result["net_pay"])
            st.success(f"Payroll saved successfully! Net pay: {result['net_pay']}") 
            st.json(result)

    # name = st.text_input("Enter Employee Name: ")
    # salry = st.number_input("Basic Salary: ", min_value=10000)
    # daysPresent = st.number_input("Days Present: ", min_value=0, max_value=30)
    # if st.button("Calculate Pay"):
    #     net = calculate_pay(salry, daysPresent)
    #     if net <= 0:
    #         st.info(f"Employee: {name} has 0 Attendance for the month, hence 0 Salary.")
    #     else:
    #         st.success(f"Net Pay of {name} for {daysPresent} Days: {net}")

elif menu == "Employee":
    st.header("👥 Employees")
    if st.button("Refresh List"):
        pass
    df = list_employees()
    df.columns = [col.replace("_"," ").title() for col in df.columns]
    st.dataframe(df)
    with st.expander("Create New Employee:"):
        name = st.text_input("Enter Name", key="new_name")
        email = st.text_input("Enter Email", key="new_email")
        phone = st.text_input("Enter Phone Number", key="new_phone", placeholder="+92 315 1122666")
        basicSalry = st.number_input("Enter Basic Salary",min_value=5000, key="new_salary")
        if st.button("Create Employee"):
            empId = add_employee(name, email, phone, basicSalry, datetime.now().date().isoformat())
            st.success(f"Employee with Id: {empId} created successfully!")

elif menu == "Dashboard":
    st.header("📊 HR Metrics Dashboard")
    payroll  = get_payroll_summary()
    if payroll.empty:
        st.info("No Payroll records yet.")
    else:
        st.subheader("Payroll by Employee's latest records")
        payroll.columns = [col.replace("_", " ").title() for col in payroll.columns]
        st.dataframe(payroll)
        grouping = payroll.groupby("Name")["Net Pay"].sum().reset_index()
        st.bar_chart(grouping.set_index("Name"))
