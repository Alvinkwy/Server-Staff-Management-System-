USE StaffManagementDB;
GO

-- 1. Create a test user with only SELECT permission
CREATE USER MaskTestUser WITHOUT LOGIN;
GRANT SELECT ON Staff TO MaskTestUser;
GO

-- 2. View data as the Test User (Masking should be ACTIVE)
EXECUTE AS USER = 'MaskTestUser';
SELECT FullName, Email, Phone FROM Staff;
REVERT;
GO

-- 3. View data as yourself (Admin) (Masking should NOT be active)
SELECT FullName, Email, Phone FROM Staff;

