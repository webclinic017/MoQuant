package com.cn.momojie.moquant.api.dao;

import java.util.List;

import org.apache.ibatis.annotations.Param;

import com.cn.momojie.moquant.api.dto.MqMessage;

public interface MqMessageDao {

	List<MqMessage> getLatestByType(@Param("msg_type") Integer messageType);
}
