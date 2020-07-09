package com.cn.momojie.moquant.api.service;

import java.util.HashMap;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.cn.momojie.moquant.api.dao.MqShareNoteDao;
import com.cn.momojie.moquant.api.dao.MqShareNoteRelationDao;
import com.cn.momojie.moquant.api.dto.MqShareNote;
import com.cn.momojie.moquant.api.dto.MqShareNoteRelation;
import com.cn.momojie.moquant.api.param.manage.NoteEditParam;
import com.cn.momojie.moquant.api.vo.OperationResp;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class MqManageService {

	@Autowired
	private MqShareNoteDao noteDao;

	@Autowired
	private MqShareNoteRelationDao noteRelationDao;

	/**
	 * 编辑日志
	 *
	 * @param input 日志主体
	 * @param add 是否新增
	 * @return
	 */
	public OperationResp editNote(NoteEditParam input, Boolean add) {
		if (StringUtils.isEmpty(input.getEventBrief())) {
			return OperationResp.fail("简述不能为空", null);
		}
		if (!add && (input.getId() == null || Long.valueOf(0).equals(input.getId()))) {
			return OperationResp.fail("编辑ID为空", null);
		}

		MqShareNote note = new MqShareNote();
		note.setId(input.getId());
		note.setEventBrief(input.getEventBrief());
		note.setNoteDetail(input.getNoteDetail());
		note.setNoteConclusion(input.getNoteConclusion());

		try {
			if (add) {
				noteDao.insert(note);
			} else {
				noteDao.updateById(note);
			}

			Map<String, Object> queryMap = new HashMap<>();
			queryMap.put("note_id", note.getId());
			noteRelationDao.deleteByMap(queryMap);

			for (String tsCode : input.getTsCodeList()) {
				MqShareNoteRelation r = new MqShareNoteRelation();
				r.setTsCode(tsCode);
				r.setNoteId(note.getId());
				noteRelationDao.insert(r);
			}

		} catch (Exception e) {
			log.error("编辑插入数据库失败", e);
			return OperationResp.fail("编辑插入数据库失败", null);
		}

		return OperationResp.ok("保存日记成功", note.getId());
	}


}
