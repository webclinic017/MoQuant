package com.cn.momojie.moquant.api.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class MqDailyBasic {

    private String tsCode;

	private String shareName;

	private MqDailyIndicator growScore;
}