package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.dto.ts.TsBasic;

import java.util.Collection;
import java.util.List;

import org.apache.ibatis.annotations.Param;

public interface TsBasicDao {

	TsBasic selectByCode(String code);

	List<TsBasic> getAllForSearchList();

	List<TsBasic> selectByCodes(@Param("list") Collection<String> codeList);
}
