package com.cn.momojie.moquant.api.dao;

import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import com.cn.momojie.moquant.api.dto.MqForecastAgg;

@Repository
public interface MqForecastAggDao {

	MqForecastAgg selectLatest(@Param("ts_code") String code);
}
