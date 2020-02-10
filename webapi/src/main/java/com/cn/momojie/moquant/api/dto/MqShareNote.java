package com.cn.momojie.moquant.api.dto;

import java.util.Date;

import lombok.Data;

@Data
public class MqShareNote {
	private Long id;

	private Date createTime;

	private Date updateTime;

	private String eventBrief;

	private String noteDetail;

	private String noteConclusion;
}