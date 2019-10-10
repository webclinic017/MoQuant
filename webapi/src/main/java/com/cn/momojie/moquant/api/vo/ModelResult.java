package com.cn.momojie.moquant.api.vo;

import lombok.Data;

@Data
public class ModelResult<T> {

    private T data;

    public static <T> ModelResult of(T data) {
        ModelResult result = new ModelResult();
        result.setData(data);
        return result;
    }
}
