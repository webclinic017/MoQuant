package com.cn.momojie.moquant.api.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.cn.momojie.moquant.api.dto.MqShareNote;
import com.cn.momojie.moquant.api.vo.MqShareNoteRelationVo;
import com.cn.momojie.moquant.api.vo.MqShareNoteVo;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface MqShareNoteDao extends BaseMapper<MqShareNote> {

	List<MqShareNoteVo> getByCode(@Param("ts_code") String tsCode);

	List<MqShareNoteRelationVo> getRelated(@Param("list") List<Long> idList);
}
