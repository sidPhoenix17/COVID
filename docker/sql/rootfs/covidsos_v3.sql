DROP TABLE IF EXISTS `reasons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `reasons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reason` varchar(255) NOT NULL,
  `description` varchar(512) DEFAULT NULL,
  `action` ENUM('DEFAULT', 'REQUEST_REJECTION', 'REQUEST_ACCEPTANCE') NOT NULL,
  `severity` ENUM('DEFAULT', 'LOW', 'MEDIUM', 'HIGH') NOT NULL,
  `custom_message` varchar(512) DEFAULT NULL,
  `is_deleted` varchar(255) NOT NULL DEFAULT false ,
  `created_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `image_url` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE requests add COLUMN reason int(11);
ALTER TABLE requests add FOREIGN KEY (reason) REFERENCES reasons (id);