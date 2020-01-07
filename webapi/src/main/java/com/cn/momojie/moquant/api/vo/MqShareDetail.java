package com.cn.momojie.moquant.api.vo;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqShareDetail {

	private String tsCode;

	private String shareName;

	private BigDecimal totalShare;

	private BigDecimal close;

	private BigDecimal marketValue;

	private BigDecimal pb;

	private BigDecimal dprofitPe;

	private BigDecimal dprofitPeg;

	private String updateDate;

	private String reportPeriod;

	private String forecastPeriod;

	private String revenuePeriod;

	private BigDecimal revenue;

	private BigDecimal revenueLy;

	private BigDecimal revenueYoy;

	private BigDecimal quarterRevenue;

	private BigDecimal quarterRevenueLy;

	private BigDecimal quarterRevenueYoy;

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

	private BigDecimal nassets;

	private String forecastReason;

	private BigDecimal growScore;

	private BigDecimal dividendYields;

	private BigDecimal dividendProfitRatio;

	private BigDecimal valScore;

	private BigDecimal receiveRisk;

	private BigDecimal liquidityRisk;

	private BigDecimal intangibleRisk;
}
