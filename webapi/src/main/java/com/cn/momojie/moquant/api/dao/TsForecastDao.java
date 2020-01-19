package com.cn.momojie.moquant.api.dao;

import org.apache.ibatis.annotations.Param;

import com.cn.momojie.moquant.api.dto.ts.TsForecast;

public interface TsForecastDao {

	TsForecast selectOne(@Param("ts_code") String tsCode, @Param("period") String period);
}
