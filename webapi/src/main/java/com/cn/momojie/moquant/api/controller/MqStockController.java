package com.cn.momojie.moquant.api.controller;

import com.cn.momojie.moquant.api.constant.SysParamKey;
import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.service.MqDailyBasicService;
import com.cn.momojie.moquant.api.service.MqSysParamService;
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

    @Autowired
    private MqSysParamService mqSysParamService;

    @RequestMapping(path = "getPageList", method = RequestMethod.POST)
    public PageResult getPageList(@RequestBody MqDailyBasicParam param) {
        injectDt(param);
        return mqDailyBasicService.getByOrder(param);
    }

    private void injectDt(MqDailyBasicParam param) {
        String calDt = mqSysParamService.getString(SysParamKey.CAL_DAILY_DONE);
        param.setDt(calDt);
    }
}
