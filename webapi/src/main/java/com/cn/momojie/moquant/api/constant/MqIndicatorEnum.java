package com.cn.momojie.moquant.api.constant;


public enum MqIndicatorEnum {

    PE(true, "pe"),
    PB(true, "pb"),
    REVENUE(false, "revenue"),
    NPROFIT(false, "nprofit"),
    DPROFIT(false, "dprofit"),
    DIVIDEND_YIELDS(true, "dividend_yields"),
    DIVIDEND_RATIO(false, "dividend_ratio"),
    ROE(false, "roe"),
    DPROFIT_MARGIN(false, "dprofit_margin"),
    TURNOVER_RATE(false, "turnover_rate"),
    EQUITY_MULTIPLIER(false, "equity_multiplier"),
    ;

    private Boolean isDaily;

    private String name;

    MqIndicatorEnum(Boolean isDaily, String name) {
        this.isDaily = isDaily;
        this.name = name;
    }

    public static MqIndicatorEnum fromName(String name) {
        for (MqIndicatorEnum i: values()) {
            if (i.name.equals(name)) {
                return i;
            }
        }
        return null;
    }
}
