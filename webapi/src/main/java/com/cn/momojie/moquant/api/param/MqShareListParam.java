package com.cn.momojie.moquant.api.param;

import lombok.Data;

@Data
public class MqShareListParam extends MqDailyBasicParam {

    private String scoreBy;

    private String orderBy;
}
