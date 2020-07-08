package com.cn.momojie.moquant.api.param.manage;

import java.util.Set;

import lombok.Data;

@Data
public class NoteEditParam {

	private Long id;

	private String eventBrief;

	private String noteDetail;

	private String noteConclusion;

	private Set<String> tsCodeList;
}
