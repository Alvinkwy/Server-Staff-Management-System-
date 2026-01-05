-- Step i: Create the Server Audit (Defines where logs are saved)
USE master;
GO
CREATE SERVER AUDIT StaffMgmt_Audit
TO FILE ( FILEPATH = 'C:\StaffMgmt_Audit\' ); -- Ensure this folder exists on your VM
GO
ALTER SERVER AUDIT StaffMgmt_Audit WITH (STATE = ON);
GO

-- Step ii: Create the Database Audit Specification (Defines what to track)
USE StaffManagementDB;
GO
CREATE DATABASE AUDIT SPECIFICATION StaffMgmt_Audit_Spec
FOR SERVER AUDIT StaffMgmt_Audit
ADD (INSERT, UPDATE, DELETE ON dbo.Staff BY public),
ADD (INSERT, UPDATE, DELETE ON dbo.Shifts BY public),
ADD (INSERT, UPDATE, DELETE ON dbo.Users BY public)
WITH (STATE = ON);
GO

SELECT * FROM sys.fn_get_audit_file('C:\StaffMgmt_Audit\StaffMgmt_Audit_4DAF7C18-58AB-4148-A5C3-4601FA235015_0_134119124277800000.sqlaudit', DEFAULT,DEFAULT);