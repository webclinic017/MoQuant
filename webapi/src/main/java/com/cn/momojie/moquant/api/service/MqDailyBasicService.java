package com.cn.momojie.moquant.api.service;

import com.cn.momojie.moquant.api.constant.SysParamKey;
import com.cn.momojie.moquant.api.dao.MqDailyBasicDao;
import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.vo.PageResult;
import com.github.pagehelper.PageHelper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class MqDailyBasicService {

    @Autowired
    private MqDailyBasicDao dao;

    @Autowired
    private MqSysParamService mqSysParamService;

    public PageResult getLatestListByOrder(MqDailyBasicParam param) {
        param.setDt(getLatestDt());
        PageHelper.startPage(param.getPageNum(), param.getPageSize());
        List<MqDailyBasic> list = dao.selectByParam(param);
        return PageResult.fromList(list);
    }

    private String getLatestDt() {
        return mqSysParamService.getString(SysParamKey.CAL_DAILY_DONE);
    }

    public MqDailyBasic getLatestByCode(String code) {
        return dao.selectLatestByCode(code, getLatestDt());
    }
}
