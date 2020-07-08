package com.cn.momojie.moquant.api.dto;

import lombok.Data;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

@Data
@TableName("mq_share_note_relation")
public class MqShareNoteRelation {

	@TableId("id")
	private Long id;

	@TableField("create_time")
	private Date createTime;

	@TableField("update_time")
	private Date updateTime;

	@TableField("ts_code")
    private String tsCode;

	@TableField("note_id")
    private Long noteId;
}
