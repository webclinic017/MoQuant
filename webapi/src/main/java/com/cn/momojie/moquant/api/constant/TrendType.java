package com.cn.momojie.moquant.api.constant;

import org.apache.commons.lang3.StringUtils;

public class TrendType {

	public static final String PE = "PE";

	public static final String PB = "PB";

	public static final String REVENUE_YEAR = "REVENUE_YEAR";

	public static final String REVENUE_QUARTER = "REVENUE_QUARTER";

	public static final String DPROFIT_YEAR = "DPROFIT_YEAR";

	public static final String DPROFIT_QUARTER = "DPROFIT_QUARTER";

	public static final String NPROFIT_YEAR = "NPROFIT_YEAR";

	public static final String NPROFIT_QUARTER = "NPROFIT_QUARTER";

	public static final String DIVIDEND = "DIVIDEND";

	public static final String DIVIDEND_PROFIT = "DIVIDEND_PROFIT";

	public static final String ROE = "ROE";

	public static final String DPROFIT_MARGIN = "DPROFIT_MARGIN";

	public static final String TURNOVER_RATE = "TURNOVER_RATE";

	public static final String EM = "EM";

	public static Boolean isYear(String t) {
		if (StringUtils.isEmpty(t)) {
			return false;
		}
		if (t.endsWith("_YEAR")) {
			return true;
		}
		if (DIVIDEND_PROFIT.equals(t) || ROE.equals(t) || DPROFIT_MARGIN.equals(t)
			|| TURNOVER_RATE.equals(t) || EM.equals(t)) {
			return true;
		}
		return false;
	}
}
