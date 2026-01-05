-- Step i: Create Master Key and Certificate in the 'master' database
USE master;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Pa$$w0rd';
CREATE CERTIFICATE StaffMgmtCert WITH SUBJECT = 'TDE Certificate for StaffManagementDB';
GO

-- Step ii: Create Database Encryption Key and Enable Encryption
USE StaffManagementDB;
GO
CREATE DATABASE ENCRYPTION KEY
WITH ALGORITHM = AES_256
ENCRYPTION BY SERVER CERTIFICATE StaffMgmtCert;
GO
ALTER DATABASE StaffManagementDB SET ENCRYPTION ON;
GO

-- Step iii: Verify Encryption State (is_encrypted = 1 means success)
SELECT name, is_encrypted FROM sys.databases WHERE name = 'StaffManagementDB';
GO
