package com.cn.momojie.moquant.api.param;

import lombok.Data;

@Data
public class MqDailyBasicParam extends MqCodePageParam {

    private Boolean orderByDate = false;

    private Boolean onlyIndicator = false;

    private String dt;
}
