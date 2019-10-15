package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.dto.MqQuarterBasic;

public interface MqQuarterBasicDao {

	MqQuarterBasic selectLatestByCode(String code);
}
