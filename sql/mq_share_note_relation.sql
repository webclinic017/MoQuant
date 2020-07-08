DROP TABLE if EXISTS `mq_share_note_relation`;

CREATE TABLE `mq_share_note_relation` (
	`id` BIGINT(20) NOT NULL AUTO_INCREMENT COMMENT 'id',
	`ts_code` VARCHAR(10) NOT NULL COMMENT 'TS股票代码' COLLATE 'utf8_general_ci',
	`note_id` BIGINT(20) NOT NULL COMMENT '日记ID',
	`create_time` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
	`update_time` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
	PRIMARY KEY (`id`),
	UNIQUE KEY (`ts_code`, `note_id`)
)
COLLATE='utf8_general_ci'
ENGINE=InnoDB
;
