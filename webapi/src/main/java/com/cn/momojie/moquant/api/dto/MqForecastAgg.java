package com.cn.momojie.moquant.api.dto;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class MqForecastAgg {
    private String tsCode;

    private String annDate;

    private String endDate;

    private BigDecimal revenue;

    private BigDecimal revenueLy;

    private BigDecimal nprofit;

    private BigDecimal nprofitLy;

    private BigDecimal dprofit;

    private BigDecimal dprofitLy;

    private String changedReason;

    private String manualAdjustReason;

    private Boolean fromManual;

    private Boolean oneTime;
}