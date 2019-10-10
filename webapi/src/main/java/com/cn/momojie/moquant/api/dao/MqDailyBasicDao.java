package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MqDailyBasicDao {

    List<MqDailyBasic> selectByParam(MqDailyBasicParam param);

    MqDailyBasic selectLatestByCode(@Param("tsCode") String tsCode, @Param("dt") String dt);
}
