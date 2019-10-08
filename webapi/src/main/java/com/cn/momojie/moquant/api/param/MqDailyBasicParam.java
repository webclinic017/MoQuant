package com.cn.momojie.moquant.api.param;

import lombok.Data;

@Data
public class MqDailyBasicParam {

    private Boolean g;

    private Boolean peg;

    private String dt;

    private Integer pageNum = 1;

    private Integer pageSize = 20;
}
