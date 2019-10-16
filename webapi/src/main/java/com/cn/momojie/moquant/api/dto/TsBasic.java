package com.cn.momojie.moquant.api.dto;

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

    public String getSymbol() {
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol == null ? null : symbol.trim();
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name == null ? null : name.trim();
    }

    public String getArea() {
        return area;
    }

    public void setArea(String area) {
        this.area = area == null ? null : area.trim();
    }

    public String getIndustry() {
        return industry;
    }

    public void setIndustry(String industry) {
        this.industry = industry == null ? null : industry.trim();
    }

    public String getFullname() {
        return fullname;
    }

    public void setFullname(String fullname) {
        this.fullname = fullname == null ? null : fullname.trim();
    }

    public String getEnname() {
        return enname;
    }

    public void setEnname(String enname) {
        this.enname = enname == null ? null : enname.trim();
    }

    public String getMarket() {
        return market;
    }

    public void setMarket(String market) {
        this.market = market == null ? null : market.trim();
    }

    public String getExchange() {
        return exchange;
    }

    public void setExchange(String exchange) {
        this.exchange = exchange == null ? null : exchange.trim();
    }

    public String getCurrType() {
        return currType;
    }

    public void setCurrType(String currType) {
        this.currType = currType == null ? null : currType.trim();
    }

    public String getListStatus() {
        return listStatus;
    }

    public void setListStatus(String listStatus) {
        this.listStatus = listStatus == null ? null : listStatus.trim();
    }

    public String getListDate() {
        return listDate;
    }

    public void setListDate(String listDate) {
        this.listDate = listDate == null ? null : listDate.trim();
    }

    public String getDelistDate() {
        return delistDate;
    }

    public void setDelistDate(String delistDate) {
        this.delistDate = delistDate == null ? null : delistDate.trim();
    }

    public String getIsHs() {
        return isHs;
    }

    public void setIsHs(String isHs) {
        this.isHs = isHs == null ? null : isHs.trim();
    }
}