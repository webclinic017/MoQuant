package com.cn.momojie.moquant.api.dto;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("mq_share_note")
public class MqShareNote {

	@TableId(value = "id", type = IdType.AUTO)
	private Long id;

	@TableField("create_time")
	private Date createTime;

	@TableField("update_time")
	private Date updateTime;

	@TableField("event_brief")
	private String eventBrief;

	@TableField("note_detail")
	private String noteDetail;

	@TableField("note_conclusion")
	private String noteConclusion;
}