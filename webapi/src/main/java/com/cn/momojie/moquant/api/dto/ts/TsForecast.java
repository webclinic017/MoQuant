package com.cn.momojie.moquant.api.dto.ts;

import java.math.BigDecimal;

import lombok.Data;

@Data
public class TsForecast {
    private Long id;

    private String tsCode;

    private String annDate;

    private String endDate;

    private String type;

    private BigDecimal pChangeMin;

    private BigDecimal pChangeMax;

    private BigDecimal netProfitMin;

    private BigDecimal netProfitMax;

    private BigDecimal lastParentNet;

    private String firstAnnDate;

    private String summary;

    private String changeReason;
}