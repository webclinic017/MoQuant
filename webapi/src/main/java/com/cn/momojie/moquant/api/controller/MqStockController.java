package com.cn.momojie.moquant.api.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.service.MqInfoQueryService;
import com.cn.momojie.moquant.api.vo.MqShareDetail;
import com.cn.momojie.moquant.api.vo.PageResult;

@RestController
public class MqStockController {

    @Autowired
    private MqInfoQueryService mqInfoQueryService;

    @RequestMapping(path = "getPageList", method = RequestMethod.POST)
    public PageResult getPageList(@RequestBody MqDailyBasicParam param) {
        return mqInfoQueryService.getLatestListByOrder(param);
    }

    @RequestMapping(path = "getLatestByCode", method = RequestMethod.POST)
    public MqShareDetail getLatestByCode(@RequestBody String tsCode) {
        return mqInfoQueryService.getLatestByCode(tsCode);
    }
}
