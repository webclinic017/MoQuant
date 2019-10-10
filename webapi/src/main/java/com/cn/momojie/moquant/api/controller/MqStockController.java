package com.cn.momojie.moquant.api.controller;

import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.service.MqDailyBasicService;
import com.cn.momojie.moquant.api.vo.ModelResult;
import com.cn.momojie.moquant.api.vo.PageResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class MqStockController {

    @Autowired
    private MqDailyBasicService mqDailyBasicService;

    @RequestMapping(path = "getPageList", method = RequestMethod.POST)
    public PageResult getPageList(@RequestBody MqDailyBasicParam param) {
        return mqDailyBasicService.getLatestListByOrder(param);
    }

    @RequestMapping(path = "getLatestByCode", method = RequestMethod.POST)
    public MqDailyBasic getLatestByCode(@RequestBody String tsCode) {
        return mqDailyBasicService.getLatestByCode(tsCode);
    }
}
