USE StaffManagementDB;
GO

-- Masking the Email column with the built-in email function
ALTER TABLE Staff
ALTER COLUMN Email ADD MASKED WITH (FUNCTION = 'email()');

-- Partial masking for the Phone column (shows first 2 and last 2 digits)
ALTER TABLE Staff
ALTER COLUMN Phone ADD MASKED WITH (FUNCTION = 'partial(2, "XXX", 2)');
GO