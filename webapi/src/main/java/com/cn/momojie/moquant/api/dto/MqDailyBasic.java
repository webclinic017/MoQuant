package com.cn.momojie.moquant.api.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class MqDailyBasic {

    private String tsCode;

    private String shareName;

    private String date;

    private Boolean isTradeDay;

    private BigDecimal totalShare;

    private BigDecimal close;

    private BigDecimal marketValue;

    private BigDecimal pb;

    private String dprofitPeriod;

    private BigDecimal dprofitEps;

    private BigDecimal quarterDprofitYoy;

    private BigDecimal dprofitPe;

    private BigDecimal dprofitPeg;
}