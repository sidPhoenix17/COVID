ALTER TABLE requests add COLUMN managed_by int(11);
ALTER TABLE requests add FOREIGN KEY (managed_by) REFERENCES users (id);