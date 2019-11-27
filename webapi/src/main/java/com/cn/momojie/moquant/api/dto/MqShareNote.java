package com.cn.momojie.moquant.api.dto;

import java.util.Date;

public class MqShareNote {
    private Long id;

    private String tsCode;

    private Date createTime;

    private Date updateTime;

    private String noteDetail;

    private String noteConclusion;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTsCode() {
        return tsCode;
    }

    public void setTsCode(String tsCode) {
        this.tsCode = tsCode == null ? null : tsCode.trim();
    }

    public Date getCreateTime() {
        return createTime;
    }

    public void setCreateTime(Date createTime) {
        this.createTime = createTime;
    }

    public Date getUpdateTime() {
        return updateTime;
    }

    public void setUpdateTime(Date updateTime) {
        this.updateTime = updateTime;
    }

    public String getNoteDetail() {
        return noteDetail;
    }

    public void setNoteDetail(String noteDetail) {
        this.noteDetail = noteDetail == null ? null : noteDetail.trim();
    }

    public String getNoteConclusion() {
        return noteConclusion;
    }

    public void setNoteConclusion(String noteConclusion) {
        this.noteConclusion = noteConclusion == null ? null : noteConclusion.trim();
    }
}