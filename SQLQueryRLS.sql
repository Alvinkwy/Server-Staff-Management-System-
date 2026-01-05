USE StaffManagementDB;
GO

-- ==================================================
-- STEP 1: CLEANUP
-- ==================================================
DROP SECURITY POLICY IF EXISTS StaffFilter;
DROP FUNCTION IF EXISTS Security.fn_securitypredicate;
DROP SCHEMA IF EXISTS Security;
DROP USER IF EXISTS AdminUser;
DROP USER IF EXISTS ManagerUser;
DROP USER IF EXISTS StaffUser; -- <--- New User
GO

-- ==================================================
-- STEP 2: CREATE TEST USERS (Now with StaffUser!)
-- ==================================================
CREATE USER AdminUser WITHOUT LOGIN;
CREATE USER ManagerUser WITHOUT LOGIN;
CREATE USER StaffUser WITHOUT LOGIN; -- <--- New User

GRANT SELECT ON Staff TO AdminUser;
GRANT SELECT ON Staff TO ManagerUser;
GRANT SELECT ON Staff TO StaffUser;
GO

-- ==================================================
-- STEP 3: CREATE THE 3-TIER LOGIC
-- ==================================================
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'Security')
    EXEC('CREATE SCHEMA Security');
GO

CREATE OR ALTER FUNCTION Security.fn_securitypredicate(@TargetRoleID AS int)  
    RETURNS TABLE  
WITH SCHEMABINDING  
AS  
    RETURN SELECT 1 AS fn_securitypredicate_result
    WHERE 
        -- RULE 1: AdminUser sees EVERYTHING
        (USER_NAME() = 'AdminUser') 
        
        OR 
        
        -- RULE 2: ManagerUser sees everyone EXCEPT Admins (RoleID 1)
        (USER_NAME() = 'ManagerUser' AND @TargetRoleID <> 1)
        
        OR

        -- RULE 3: StaffUser sees ONLY Staff (RoleID 3)
        (USER_NAME() = 'StaffUser' AND @TargetRoleID = 3);
GO

-- ==================================================
-- STEP 4: APPLY THE POLICY
-- ==================================================
CREATE SECURITY POLICY StaffFilter
ADD FILTER PREDICATE Security.fn_securitypredicate(RoleID)
ON dbo.Staff
WITH (STATE = ON);
GO

-- ==================================================
-- STEP 5: THE FINAL TEST (Now with 3 Views)
-- ==================================================

-- TEST 1: Admin View (Should see everything: RoleID 1, 2, 3)
EXECUTE AS USER = 'AdminUser';
SELECT FullName, RoleID FROM Staff;
REVERT;

-- TEST 2: Manager View (Should see RoleID 2, 3. NO RoleID 1)
EXECUTE AS USER = 'ManagerUser';
SELECT FullName, RoleID FROM Staff;
REVERT;

-- TEST 3: Staff View (Should see ONLY RoleID 3)
EXECUTE AS USER = 'StaffUser';
SELECT FullName, RoleID FROM Staff;
REVERT;