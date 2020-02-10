package com.cn.momojie.moquant.api.vo;

import com.cn.momojie.moquant.api.dto.MqShareNote;
import com.cn.momojie.moquant.api.dto.ts.TsBasic;
import lombok.Data;

import java.util.List;

@Data
public class MqShareNoteVo extends MqShareNote {

    private List<MqShareNoteRelationVo> relatedShareList;
}
