package com.cn.momojie.moquant.api.dao;

import java.util.List;

import org.apache.ibatis.annotations.Param;

import com.cn.momojie.moquant.api.dto.MqShareNote;

public interface MqShareNoteDao {

	List<MqShareNote> getByCode(@Param("ts_code") String tsCode);
}
