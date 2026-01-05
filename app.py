from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkeychangeinprod"

# DB server name
SERVER_NAME = r"MCLAPPY"
# Database name
DATABASE_NAME = "StaffManagementDB"

# Optional: SQL Login (else Windows auth)
USE_SQL_LOGIN = False
DB_USER = "appuser"
DB_PASSWORD = "StrongPass123!"


def build_conn_str():
    base = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE={DATABASE_NAME};"
        "TrustServerCertificate=yes;"
    )
    if USE_SQL_LOGIN:
        return base + f"UID={DB_USER};PWD={DB_PASSWORD};"
    return base + "Trusted_Connection=yes;"


CONN_STR = build_conn_str()

def get_conn():
    return pyodbc.connect(CONN_STR)
def is_logged_in():
    return "user_id" in session
def is_admin():
    return is_logged_in() and session.get("role") == "Admin"
def is_manager():
    return is_logged_in() and session.get("role") == "Manager"
def get_role_id(conn, role_name: str):
    cur = conn.cursor()
    cur.execute("SELECT RoleID FROM Roles WHERE RoleName = ?", (role_name,))
    row = cur.fetchone()
    return row[0] if row else None

@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/testdb")
def testdb():
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Staff")
        cnt = cur.fetchone()[0]
        return f"DB OK. Staff rows = {cnt}"
    except Exception as e:
        return f"DB FAIL: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = None
        try:
            conn = get_conn()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    u.UserID,
                    u.Username,
                    u.Password,
                    s.StaffID,
                    s.FullName,
                    r.RoleName
                FROM Users u
                JOIN Staff s ON u.StaffID = s.StaffID
                JOIN Roles r ON s.RoleID = r.RoleID
                WHERE u.Username = ?
                """,
                (username,),
            )

            row = cur.fetchone()
            if not row:
                error = "noaccount"
            else:
                user_id, uname, pwd_hash, staff_id, full_name, role_name = row

                if not check_password_hash(pwd_hash, password):
                    error = "wrongpassword"
                else:
                    session["user_id"] = user_id
                    session["staff_id"] = staff_id
                    session["username"] = uname
                    session["full_name"] = full_name
                    session["role"] = role_name

                    if role_name == "Admin":
                        return redirect(url_for("dashboardA"))
                    elif role_name == "Manager":
                        return redirect(url_for("dashboardM"))
                    else:
                        return redirect(url_for("staff"))

        except Exception as e:
            print("DB ERROR (login):", repr(e))
            error = "dberror"
        finally:
            if conn:
                conn.close()

    return render_template("index.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboardA")
def dashboardA():
    if not is_admin():
        return redirect(url_for("login"))

    return render_template(
        "DashboardA.html",
        full_name=session.get("full_name"),
        role=session.get("role"),
        username=session.get("username"),
    )


@app.route("/dashboardM")
def dashboardM():
    if not is_manager():
        return redirect(url_for("login"))

    return render_template(
        "DashboardM.html",
        full_name=session.get("full_name"),
        role=session.get("role"),
        username=session.get("username"),
    )


@app.route("/staff")
def staff():
    if not is_logged_in():
        return redirect(url_for("login"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        staff_id = session["staff_id"]

        # Personal profile
        cur.execute(
            """
            SELECT s.StaffID, s.FullName, s.Email, s.Phone, r.RoleName
            FROM Staff s
            JOIN Roles r ON s.RoleID = r.RoleID
            WHERE s.StaffID = ?
            """,
            (staff_id,),
        )
        profile = cur.fetchone()

        # Shifts
        cur.execute(
            """
            SELECT ShiftID, ShiftStart, ShiftEnd, Status
            FROM Shifts
            WHERE StaffID = ?
            ORDER BY ShiftStart DESC
            """,
            (staff_id,),
        )
        shifts = cur.fetchall()

        return render_template("Staff.html", profile=profile, shifts=shifts)

    except Exception as e:
        return f"Staff Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


# Admin Staff CRUD
@app.route("/admin/staff")
def admin_staff():
    if not is_admin():
        return redirect(url_for("login"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT s.StaffID, s.FullName, s.Email, s.Phone, r.RoleName
            FROM Staff s
            JOIN Roles r ON s.RoleID = r.RoleID
            ORDER BY s.StaffID
            """
        )
        rows = cur.fetchall()

        return render_template("AdminStaff.html", stafflist=rows)

    except Exception as e:
        return f"AdminStaff Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/admin/staff/create", methods=["POST"])
def admin_staff_create():
    if not is_admin():
        return redirect(url_for("login"))

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    role = request.form.get("role", "").strip()

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not fullname or not email or not role or not username or not password:
        return redirect(url_for("admin_staff"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        role_id = get_role_id(conn, role)
        if role_id is None:
            return "Invalid role."

        # Username must be unique
        cur.execute("SELECT 1 FROM Users WHERE Username = ?", (username,))
        if cur.fetchone():
            return "Username already exists. Please choose another."

        # Insert Staff and get new StaffID
        cur.execute(
            """
            INSERT INTO Staff (FullName, Email, Phone, RoleID)
            OUTPUT INSERTED.StaffID
            VALUES (?, ?, ?, ?)
            """,
            (fullname, email, phone, role_id),
        )
        new_staff_id = cur.fetchone()[0]

        # Insert Users with hashed password
        pwd_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO Users (Username, Password, StaffID) VALUES (?, ?, ?)",
            (username, pwd_hash, new_staff_id),
        )

        conn.commit()
        return redirect(url_for("admin_staff"))

    except Exception as e:
        return f"Create Staff+User Error: {repr(e)}"
    finally:
        if conn:
            conn.close()

# Manager Staff CRUD Page

@app.route("/manager/staff")
def manager_staff():
    if not is_manager():
        return redirect(url_for("login"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT s.StaffID, s.FullName, s.Email, s.Phone, r.RoleName
            FROM Staff s
            JOIN Roles r ON s.RoleID = r.RoleID
            ORDER BY s.StaffID
        """)
        rows = cur.fetchall()

        return render_template("ManagerStaff.html", stafflist=rows)

    except Exception as e:
        return f"ManagerStaff Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/manager/staff/create", methods=["POST"])
def manager_staff_create():
    if not is_manager():
        return redirect(url_for("login"))

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    if not fullname or not email or not username or not password:
        return redirect(url_for("manager_staff"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Force role to Staff (manager cannot assign roles)
        staff_role_id = get_role_id(conn, "Staff")
        if staff_role_id is None:
            return "Role 'Staff' not found in Roles table."

        # Username unique
        cur.execute("SELECT 1 FROM Users WHERE Username = ?", (username,))
        if cur.fetchone():
            return "Username already exists. Please choose another."

        # Create staff record
        cur.execute("""
            INSERT INTO Staff (FullName, Email, Phone, RoleID)
            OUTPUT INSERTED.StaffID
            VALUES (?, ?, ?, ?)
        """, (fullname, email, phone, staff_role_id))
        new_staff_id = cur.fetchone()[0]

        # Create login user
        pwd_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO Users (Username, Password, StaffID) VALUES (?, ?, ?)",
            (username, pwd_hash, new_staff_id)
        )

        conn.commit()
        return redirect(url_for("manager_staff"))

    except Exception as e:
        return f"Manager Create Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/manager/staff/update/<int:staff_id>", methods=["POST"])
def manager_staff_update(staff_id):
    if not is_manager():
        return redirect(url_for("login"))

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not fullname or not email:
        return redirect(url_for("manager_staff"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Managers cannot change RoleID, only update these fields
        cur.execute("""
            UPDATE Staff
            SET FullName = ?, Email = ?, Phone = ?
            WHERE StaffID = ?
        """, (fullname, email, phone, staff_id))

        conn.commit()
        return redirect(url_for("manager_staff"))

    except Exception as e:
        return f"Manager Update Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/manager/staff/delete/<int:staff_id>", methods=["POST"])
def manager_staff_delete(staff_id):
    if not is_manager():
        return redirect(url_for("login"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # delete children first (FKs)
        cur.execute("DELETE FROM Shifts WHERE StaffID = ?", (staff_id,))
        cur.execute("DELETE FROM Users WHERE StaffID = ?", (staff_id,))
        cur.execute("DELETE FROM Staff WHERE StaffID = ?", (staff_id,))

        conn.commit()
        return redirect(url_for("manager_staff"))

    except Exception as e:
        return f"Manager Delete Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/admin/staff/update/<int:staff_id>", methods=["POST"])
def admin_staff_update(staff_id):
    if not is_admin():
        return redirect(url_for("login"))

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    role = request.form.get("role", "").strip()

    if not fullname or not email or not role:
        return redirect(url_for("admin_staff"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        role_id = get_role_id(conn, role)
        if role_id is None:
            return "Invalid role."

        cur.execute(
            """
            UPDATE Staff
            SET FullName = ?, Email = ?, Phone = ?, RoleID = ?
            WHERE StaffID = ?
            """,
            (fullname, email, phone, role_id, staff_id),
        )

        conn.commit()
        return redirect(url_for("admin_staff"))

    except Exception as e:
        return f"Update Staff Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


@app.route("/admin/staff/delete/<int:staff_id>", methods=["POST"])
def admin_staff_delete(staff_id):
    if not is_admin():
        return redirect(url_for("login"))

    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()

        # delete children first (FKs)
        cur.execute("DELETE FROM Shifts WHERE StaffID = ?", (staff_id,))
        cur.execute("DELETE FROM Users WHERE StaffID = ?", (staff_id,))
        cur.execute("DELETE FROM Staff WHERE StaffID = ?", (staff_id,))

        conn.commit()
        return redirect(url_for("admin_staff"))

    except Exception as e:
        return f"Delete Staff Error: {repr(e)}"
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    app.run(debug=True)
