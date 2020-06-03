package com.cn.momojie.moquant.api.dao;

import java.util.Collection;
import java.util.List;

import org.apache.ibatis.annotations.Param;

import com.cn.momojie.moquant.api.dto.MqDailyIndicator;
import com.cn.momojie.moquant.api.dto.MqShareAll;
import com.cn.momojie.moquant.api.param.MqShareListParam;

public interface MqDailyIndicatorDao {

    List<String> getScoreList(MqShareListParam param);

    List<MqDailyIndicator> getDailyLatest(@Param("codeList") Collection<String> codeList,
			@Param("nameList") Collection<String> nameList,
			@Param("underDate") String underDate);
}
