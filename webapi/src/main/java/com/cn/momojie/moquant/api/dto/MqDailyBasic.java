package com.cn.momojie.moquant.api.dto;

import java.math.BigDecimal;

public class MqDailyBasic {
    private String tsCode;

    private String date;

    private String shareName;

    private String reportSeason;

    private String forecastSeason;

    private BigDecimal totalShare;

    private BigDecimal close;

    private BigDecimal marketValue;

    private BigDecimal seasonRevenue;

    private BigDecimal seasonRevenueLy;

    private BigDecimal seasonRevenueYoy;

    private BigDecimal seasonNprofit;

    private BigDecimal seasonNprofitLy;

    private BigDecimal seasonNprofitYoy;

    private BigDecimal nprofitLtm;

    private BigDecimal nprofitEps;

    private BigDecimal nprofitPe;

    private BigDecimal nprofitPeg;

    private BigDecimal seasonDprofit;

    private BigDecimal seasonDprofitLy;

    private BigDecimal seasonDprofitYoy;

    private BigDecimal dprofitLtm;

    private BigDecimal dprofitEps;

    private BigDecimal dprofitPe;

    private BigDecimal dprofitPeg;

    private BigDecimal nassets;

    private BigDecimal pb;

    private Boolean isTradeDay;

    public String getTsCode() {
        return tsCode;
    }

    public void setTsCode(String tsCode) {
        this.tsCode = tsCode == null ? null : tsCode.trim();
    }

    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date == null ? null : date.trim();
    }

    public String getShareName() {
        return shareName;
    }

    public void setShareName(String shareName) {
        this.shareName = shareName == null ? null : shareName.trim();
    }

    public String getReportSeason() {
        return reportSeason;
    }

    public void setReportSeason(String reportSeason) {
        this.reportSeason = reportSeason == null ? null : reportSeason.trim();
    }

    public String getForecastSeason() {
        return forecastSeason;
    }

    public void setForecastSeason(String forecastSeason) {
        this.forecastSeason = forecastSeason == null ? null : forecastSeason.trim();
    }

    public BigDecimal getTotalShare() {
        return totalShare;
    }

    public void setTotalShare(BigDecimal totalShare) {
        this.totalShare = totalShare;
    }

    public BigDecimal getClose() {
        return close;
    }

    public void setClose(BigDecimal close) {
        this.close = close;
    }

    public BigDecimal getMarketValue() {
        return marketValue;
    }

    public void setMarketValue(BigDecimal marketValue) {
        this.marketValue = marketValue;
    }

    public BigDecimal getSeasonRevenue() {
        return seasonRevenue;
    }

    public void setSeasonRevenue(BigDecimal seasonRevenue) {
        this.seasonRevenue = seasonRevenue;
    }

    public BigDecimal getSeasonRevenueLy() {
        return seasonRevenueLy;
    }

    public void setSeasonRevenueLy(BigDecimal seasonRevenueLy) {
        this.seasonRevenueLy = seasonRevenueLy;
    }

    public BigDecimal getSeasonRevenueYoy() {
        return seasonRevenueYoy;
    }

    public void setSeasonRevenueYoy(BigDecimal seasonRevenueYoy) {
        this.seasonRevenueYoy = seasonRevenueYoy;
    }

    public BigDecimal getSeasonNprofit() {
        return seasonNprofit;
    }

    public void setSeasonNprofit(BigDecimal seasonNprofit) {
        this.seasonNprofit = seasonNprofit;
    }

    public BigDecimal getSeasonNprofitLy() {
        return seasonNprofitLy;
    }

    public void setSeasonNprofitLy(BigDecimal seasonNprofitLy) {
        this.seasonNprofitLy = seasonNprofitLy;
    }

    public BigDecimal getSeasonNprofitYoy() {
        return seasonNprofitYoy;
    }

    public void setSeasonNprofitYoy(BigDecimal seasonNprofitYoy) {
        this.seasonNprofitYoy = seasonNprofitYoy;
    }

    public BigDecimal getNprofitLtm() {
        return nprofitLtm;
    }

    public void setNprofitLtm(BigDecimal nprofitLtm) {
        this.nprofitLtm = nprofitLtm;
    }

    public BigDecimal getNprofitEps() {
        return nprofitEps;
    }

    public void setNprofitEps(BigDecimal nprofitEps) {
        this.nprofitEps = nprofitEps;
    }

    public BigDecimal getNprofitPe() {
        return nprofitPe;
    }

    public void setNprofitPe(BigDecimal nprofitPe) {
        this.nprofitPe = nprofitPe;
    }

    public BigDecimal getNprofitPeg() {
        return nprofitPeg;
    }

    public void setNprofitPeg(BigDecimal nprofitPeg) {
        this.nprofitPeg = nprofitPeg;
    }

    public BigDecimal getSeasonDprofit() {
        return seasonDprofit;
    }

    public void setSeasonDprofit(BigDecimal seasonDprofit) {
        this.seasonDprofit = seasonDprofit;
    }

    public BigDecimal getSeasonDprofitLy() {
        return seasonDprofitLy;
    }

    public void setSeasonDprofitLy(BigDecimal seasonDprofitLy) {
        this.seasonDprofitLy = seasonDprofitLy;
    }

    public BigDecimal getSeasonDprofitYoy() {
        return seasonDprofitYoy;
    }

    public void setSeasonDprofitYoy(BigDecimal seasonDprofitYoy) {
        this.seasonDprofitYoy = seasonDprofitYoy;
    }

    public BigDecimal getDprofitLtm() {
        return dprofitLtm;
    }

    public void setDprofitLtm(BigDecimal dprofitLtm) {
        this.dprofitLtm = dprofitLtm;
    }

    public BigDecimal getDprofitEps() {
        return dprofitEps;
    }

    public void setDprofitEps(BigDecimal dprofitEps) {
        this.dprofitEps = dprofitEps;
    }

    public BigDecimal getDprofitPe() {
        return dprofitPe;
    }

    public void setDprofitPe(BigDecimal dprofitPe) {
        this.dprofitPe = dprofitPe;
    }

    public BigDecimal getDprofitPeg() {
        return dprofitPeg;
    }

    public void setDprofitPeg(BigDecimal dprofitPeg) {
        this.dprofitPeg = dprofitPeg;
    }

    public BigDecimal getNassets() {
        return nassets;
    }

    public void setNassets(BigDecimal nassets) {
        this.nassets = nassets;
    }

    public BigDecimal getPb() {
        return pb;
    }

    public void setPb(BigDecimal pb) {
        this.pb = pb;
    }

    public Boolean getIsTradeDay() {
        return isTradeDay;
    }

    public void setIsTradeDay(Boolean isTradeDay) {
        this.isTradeDay = isTradeDay;
    }
}