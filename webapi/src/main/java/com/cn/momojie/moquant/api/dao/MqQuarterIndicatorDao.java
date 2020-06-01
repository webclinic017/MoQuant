package com.cn.momojie.moquant.api.dao;

import java.util.Collection;
import java.util.List;

import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import com.cn.momojie.moquant.api.dto.MqQuarterIndicator;

@Repository
public interface MqQuarterIndicatorDao {

	List<MqQuarterIndicator> getQuarterLatest(@Param("codeList") Collection<String> codeList,
			@Param("nameList") Collection<String> nameList,
			@Param("fromPeriod") String fromPeriod);
}
