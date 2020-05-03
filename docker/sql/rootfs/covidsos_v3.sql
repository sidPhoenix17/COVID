DROP TABLE IF EXISTS `schedule`;
create table schedule (
                           id int8 not null AUTO_INCREMENT,
                           created_at TIMESTAMP not null DEFAULT CURRENT_TIMESTAMP,
                           created_by varchar(255) not null,
                           is_deleted boolean not null,
                           updated_at TIMESTAMP not null DEFAULT CURRENT_TIMESTAMP,
                           updated_by varchar(255),
                           cron_expression varchar(255),
                           task_ref varchar(255),
                           primary key (id)
);