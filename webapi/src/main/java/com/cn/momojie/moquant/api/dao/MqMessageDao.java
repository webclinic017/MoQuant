package com.cn.momojie.moquant.api.dao;

import java.util.List;

import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import com.cn.momojie.moquant.api.dto.MqMessage;

@Repository
public interface MqMessageDao {

	List<MqMessage> getLatestByType(@Param("msg_type") Integer messageType);
}
