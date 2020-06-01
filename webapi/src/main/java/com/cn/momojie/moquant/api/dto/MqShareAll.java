package com.cn.momojie.moquant.api.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.util.Map;

@Data
public class MqShareAll {

	private String tsCode;

	private String shareName;

	private Map<String, MqDailyIndicator> dailyIndicators;

	private Map<String, MqQuarterIndicator> quarterIndicators;
}