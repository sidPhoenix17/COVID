ALTER TABLE requests add COLUMN managed_by int(11);
ALTER TABLE requests add FOREIGN KEY (managed_by) REFERENCES users (id);
ALTER TABLE requests add COLUMN city varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE volunteers add COLUMN city varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
