BEGIN TRANSACTION;

-- Create the table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='test_table' AND xtype='U')
BEGIN
    CREATE TABLE test_table (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        created_at DATETIME DEFAULT GETDATE()
    );
END

-- Insert data into the table
INSERT INTO test_table (name) VALUES ('Test Name 1'), ('Test Name 2');

-- Update data in the table
UPDATE test_table SET name = 'Updated Name' WHERE id = 1;

-- Select data from the table
SELECT * FROM test_table;

-- Commit the transaction
COMMIT;