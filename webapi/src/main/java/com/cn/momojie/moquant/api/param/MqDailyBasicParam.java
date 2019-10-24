package com.cn.momojie.moquant.api.param;

import lombok.Data;

@Data
public class MqDailyBasicParam {

    private Boolean orderByDate = false;

    private Boolean onlyIndicator = false;

    private String dt;

    private String tsCode;

    private Integer pageNum = 1;

    private Integer pageSize = 20;
}
