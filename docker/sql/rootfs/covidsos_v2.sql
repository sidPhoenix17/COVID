ALTER TABLE requests add COLUMN managed_by int(11);
ALTER TABLE requests add FOREIGN KEY (managed_by) REFERENCES users (id);
ALTER TABLE requests add COLUMN city varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE volunteers add COLUMN city varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE `support_orgs` ADD `website` varchar(255) COLLATE 'utf8_unicode_ci' NULL;
ALTER TABLE volunteers add COLUMN whatsapp_id varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE users add COLUMN whatsapp_id varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE requests add COLUMN whatsapp_id varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;


DROP TABLE IF EXISTS `request_sms_urls`;
CREATE TABLE `request_sms_urls` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `r_uuid` varchar(32) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `url_type` varchar(50) NOT NULL,
  `url` varchar(1000) CHARACTER SET utf8 COLLATE utf8_unicode_ci NOT NULL,
  `sent_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


ALTER TABLE requests add COLUMN filled_by_name varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL;
ALTER TABLE requests add COLUMN filled_by_mob_number bigint(20) DEFAULT NULL;
