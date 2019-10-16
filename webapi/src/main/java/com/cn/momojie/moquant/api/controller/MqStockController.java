package com.cn.momojie.moquant.api.controller;

import com.cn.momojie.moquant.api.param.MqTrendParam;
import com.cn.momojie.moquant.api.vo.MqShareTrend;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

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

    @RequestMapping(path = "getTrendByCode", method = RequestMethod.POST)
    public MqShareTrend getTrendByCode(@RequestBody MqTrendParam param) {
        return mqInfoQueryService.getTrend(param);
    }
}
