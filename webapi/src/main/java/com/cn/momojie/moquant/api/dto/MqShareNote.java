package com.cn.momojie.moquant.api.dto;

import java.util.Date;

import lombok.Data;

@Data
public class MqShareNote {
	private Long id;

	private String tsCode;

	private Date createTime;

	private Date updateTime;

	private String noteDetail;

	private String noteConclusion;
}