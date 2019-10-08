package com.cn.momojie.moquant.api.dao;

import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface MqSysParamDao {

    String getByKey(@Param("key") String key);
}
