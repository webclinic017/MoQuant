package com.cn.momojie.moquant.api.dto;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqQuarterIndicator {

	private String tsCode;

	private String period;

	private Integer reportType;

	private String name;

	private BigDecimal value;

	private BigDecimal yoy;

	private BigDecimal mom;

	private String updateDate;
}
