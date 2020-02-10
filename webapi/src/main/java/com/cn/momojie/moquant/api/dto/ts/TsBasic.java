package com.cn.momojie.moquant.api.dto.ts;

import lombok.Data;

@Data
public class TsBasic {

    private Long id;

    private String tsCode;

    private String symbol;

    private String name;

    private String area;

    private String industry;

    private String fullname;

    private String enname;

    private String market;

    private String exchange;

    private String currType;

    private String listStatus;

    private String listDate;

    private String delistDate;

    private String isHs;
}