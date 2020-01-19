package com.cn.momojie.moquant.api.dto;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqForecastAdjust {

	private Long id;

	private String tsCode;

	private Integer forecastType;

	private String endDate;

	private BigDecimal dprofit;

	private String remark;

	private Boolean oneTime;
}