package com.cn.momojie.moquant.api.dto;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqQuarterBasic {

	private String tsCode;

	private String updateDate;

	private String reportPeriod;

	private String forecastPeriod;

	private String shareName;

	private String revenuePeriod;

	private BigDecimal revenue;

	private BigDecimal revenueLy;

	private BigDecimal revenueYoy;

	private BigDecimal quarterRevenue;

	private BigDecimal quarterRevenueLy;

	private BigDecimal quarterRevenueYoy;

	private BigDecimal revenueLtm;

	private String nprofitPeriod;

	private BigDecimal nprofit;

	private BigDecimal nprofitLy;

	private BigDecimal nprofitYoy;

	private BigDecimal quarterNprofit;

	private BigDecimal quarterNprofitLy;

	private BigDecimal quarterNprofitYoy;

	private BigDecimal nprofitLtm;

	private String dprofitPeriod;

	private BigDecimal dprofit;

	private BigDecimal dprofitLy;

	private BigDecimal dprofitYoy;

	private BigDecimal quarterDprofit;

	private BigDecimal quarterDprofitLy;

	private BigDecimal quarterDprofitYoy;

	private BigDecimal dprofitLtm;

	private BigDecimal eps;

	private BigDecimal nassets;

	private BigDecimal dividend;

	private BigDecimal dividendLtm;

	private BigDecimal dividendProfitRatio;

	private BigDecimal receiveRisk;

	private BigDecimal liquidityRisk;

	private BigDecimal intangibleRisk;

}