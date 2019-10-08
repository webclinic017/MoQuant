package com.cn.momojie.moquant.api.vo;

import com.github.pagehelper.PageInfo;
import lombok.Data;

import java.util.List;

@Data
public class PageResult<T> {

    private Long total;

    private List<T> list;

    public static <T> PageResult fromList(List<T> l) {
        PageInfo<T> info = new PageInfo<>(l);
        PageResult<T> result = new PageResult<>();
        result.setTotal(info.getTotal());
        result.setList(info.getList());
        return result;
    }
}
