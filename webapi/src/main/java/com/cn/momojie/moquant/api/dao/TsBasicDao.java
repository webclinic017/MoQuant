package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.dto.TsBasic;

import java.util.List;

public interface TsBasicDao {

	TsBasic selectByCode(String code);

	List<TsBasic> getAllForSearchList();
}
