package com.cn.momojie.moquant.api.service;

import com.cn.momojie.moquant.api.constant.SysParamKey;
import com.cn.momojie.moquant.api.dao.MqDailyBasicDao;
import com.cn.momojie.moquant.api.dao.MqQuarterBasicDao;
import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import com.cn.momojie.moquant.api.dto.MqQuarterBasic;
import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.vo.MqShareDetail;
import com.cn.momojie.moquant.api.vo.PageResult;
import com.github.pagehelper.PageHelper;

import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class MqInfoQueryService {

    @Autowired
    private MqDailyBasicDao dailyBasicDao;

    @Autowired
    private MqQuarterBasicDao quarterBasicDao;

    @Autowired
    private MqSysParamService mqSysParamService;

    public PageResult getLatestListByOrder(MqDailyBasicParam param) {
        param.setDt(getLatestDt());
        PageHelper.startPage(param.getPageNum(), param.getPageSize());
        List<MqDailyBasic> list = dailyBasicDao.selectByParam(param);
        return PageResult.fromList(list);
    }

    private String getLatestDt() {
        return mqSysParamService.getString(SysParamKey.CAL_DAILY_DONE);
    }

    public MqShareDetail getLatestByCode(String code) {
		MqShareDetail detail = new MqShareDetail();

		MqDailyBasic daily = dailyBasicDao.selectLatestByCode(code);
		BeanUtils.copyProperties(daily, detail);

		MqQuarterBasic quarter = quarterBasicDao.selectLatestByCode(code);
		BeanUtils.copyProperties(quarter, detail);

		return detail;
    }
}
