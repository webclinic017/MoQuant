package com.cn.momojie.moquant.api.dao;

import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import com.cn.momojie.moquant.api.dto.MqForecastAdjust;

@Repository
public interface MqForecastAdjustDao {

	MqForecastAdjust selectOne(@Param("ts_code") String tsCode, @Param("end_date") String period, @Param("forecast_type") Integer forecastType);
}
