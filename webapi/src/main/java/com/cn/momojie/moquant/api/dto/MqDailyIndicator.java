package com.cn.momojie.moquant.api.dto;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqDailyIndicator {

	private String tsCode;

	private String updateDate;

	private String period;

	private Integer reportType;

	private String name;

	private BigDecimal value;
}
