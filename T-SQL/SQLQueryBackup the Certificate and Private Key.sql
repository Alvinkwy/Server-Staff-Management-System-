USE master;
GO

BACKUP CERTIFICATE StaffMgmtCert 
TO FILE = 'C:\TDE\StaffMgmtCert.cer'
WITH PRIVATE KEY (
     FILE = 'C:\TDE\StaffMgmtCert.pvk',
     ENCRYPTION BY PASSWORD = 'Pa$$w0rd'
);