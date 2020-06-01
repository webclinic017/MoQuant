package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.dto.MqDailyIndicator;
import com.cn.momojie.moquant.api.dto.MqShareAll;
import com.cn.momojie.moquant.api.param.MqShareListParam;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.Collection;
import java.util.List;

@Repository
public interface MqDailyIndicatorDao {

    List<MqShareAll> getScoreList(MqShareListParam param);

    List<MqDailyIndicator> getDailyLatest(@Param("codeList") Collection<String> codeList,
			@Param("nameList") Collection<String> nameList,
			@Param("yesterday") String yesterday);
}
