package com.cn.momojie.moquant.api.dao;

import com.cn.momojie.moquant.api.vo.MqShareNoteRelationVo;
import com.cn.momojie.moquant.api.vo.MqShareNoteVo;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface MqShareNoteDao {

	List<MqShareNoteVo> getByCode(@Param("ts_code") String tsCode);

	List<MqShareNoteRelationVo> getRelated(@Param("list") List<Long> idList);
}
