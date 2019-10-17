package com.cn.momojie.moquant.api.dao;

import java.util.List;

import com.cn.momojie.moquant.api.dto.MqQuarterBasic;
import com.cn.momojie.moquant.api.param.MqQuarterBasicParam;

public interface MqQuarterBasicDao {

	MqQuarterBasic selectLatestByCode(String code);

	List<MqQuarterBasic> selectTrendByParam(MqQuarterBasicParam param);
}
