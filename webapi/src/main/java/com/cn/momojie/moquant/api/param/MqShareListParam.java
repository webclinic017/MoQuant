package com.cn.momojie.moquant.api.param;

import lombok.Data;

@Data
public class MqShareListParam extends MqPageParam {

    private String scoreBy;

    private String orderBy;

    private String yesterday;
}
