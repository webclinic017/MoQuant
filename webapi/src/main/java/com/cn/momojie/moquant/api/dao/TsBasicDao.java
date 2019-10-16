package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.dto.TsBasic;

public interface TsBasicDao {

	TsBasic selectByCode(String code);
}
