package com.cn.momojie.moquant.api.vo;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqForecastInfo {

	private Boolean latest = false;

	private String period = "";

	private BigDecimal nprofit = BigDecimal.ZERO;

	private BigDecimal dprofit = BigDecimal.ZERO;

	private String forecastReason = "";

	private String adjustReason = "";

	private Boolean oneTime = false;

	private Boolean fromManual = false;
}
