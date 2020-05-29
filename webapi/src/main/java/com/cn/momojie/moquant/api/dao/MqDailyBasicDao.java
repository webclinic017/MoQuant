package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.dto.MqDailyIndicator;
import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import com.cn.momojie.moquant.api.param.MqShareListParam;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.Collection;
import java.util.List;

@Repository
public interface MqDailyBasicDao {

    List<MqDailyBasic> getScoreList(MqShareListParam param);

    List<MqDailyIndicator> getDailyLatest(@Param("codeList") Collection<String> codeList, @Param("yesterday") String yesterday);
}
