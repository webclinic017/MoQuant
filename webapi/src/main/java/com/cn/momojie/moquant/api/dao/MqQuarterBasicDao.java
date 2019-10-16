package com.cn.momojie.moquant.api.dao;

import java.util.List;

import com.cn.momojie.moquant.api.dto.MqQuarterBasic;

public interface MqQuarterBasicDao {

	MqQuarterBasic selectLatestByCode(String code);

	List<MqQuarterBasic> selectTrendByCode(String code);
}
