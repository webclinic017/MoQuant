package com.cn.momojie.moquant.api.dto;

import lombok.Data;

import java.util.Date;

@Data
public class MqShareNoteRelation {

    private String tsCode;

    private Long noteId;

    private Date createTime;

    private Date updateTime;
}
