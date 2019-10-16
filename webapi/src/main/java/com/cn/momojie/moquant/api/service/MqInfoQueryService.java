package com.cn.momojie.moquant.api.service;

import com.cn.momojie.moquant.api.constant.SysParamKey;
import com.cn.momojie.moquant.api.constant.TrendType;
import com.cn.momojie.moquant.api.dao.MqDailyBasicDao;
import com.cn.momojie.moquant.api.dao.MqQuarterBasicDao;
import com.cn.momojie.moquant.api.dao.TsBasicDao;
import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import com.cn.momojie.moquant.api.dto.MqQuarterBasic;
import com.cn.momojie.moquant.api.dto.TsBasic;
import com.cn.momojie.moquant.api.param.MqDailyBasicParam;
import com.cn.momojie.moquant.api.util.BigDecimalUtils;
import com.cn.momojie.moquant.api.util.DateTimeUtils;
import com.cn.momojie.moquant.api.vo.MqShareDetail;
import com.cn.momojie.moquant.api.vo.MqShareTrend;
import com.cn.momojie.moquant.api.vo.PageResult;
import com.github.pagehelper.PageHelper;

import org.apache.commons.lang3.tuple.Pair;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class MqInfoQueryService {

	@Autowired
	private TsBasicDao tsBasicDao;

    @Autowired
    private MqDailyBasicDao dailyBasicDao;

    @Autowired
    private MqQuarterBasicDao quarterBasicDao;

    @Autowired
    private MqSysParamService mqSysParamService;

    public PageResult getLatestListByOrder(MqDailyBasicParam param) {
        param.setDt(getLatestDt());
        PageHelper.startPage(param.getPageNum(), param.getPageSize());
        List<MqDailyBasic> list = dailyBasicDao.selectByParam(param);
        return PageResult.fromList(list);
    }

    private String getLatestDt() {
        return mqSysParamService.getString(SysParamKey.CAL_DAILY_DONE);
    }

    public MqShareDetail getLatestByCode(String code) {
		MqShareDetail detail = new MqShareDetail();

		MqDailyBasic daily = dailyBasicDao.selectLatestByCode(code);
		BeanUtils.copyProperties(daily, detail);

		MqQuarterBasic quarter = quarterBasicDao.selectLatestByCode(code);
		BeanUtils.copyProperties(quarter, detail);

		return detail;
    }

    public MqShareTrend getTrend(String tsCode, String trendType) {
		MqShareTrend trend = new MqShareTrend();
    	TsBasic basic = tsBasicDao.selectByCode(tsCode);
    	if (basic == null) {
    		log.error("Can't find share basic of {}", tsCode);
    		return trend;
		}
    	if (TrendType.PE.equals(trendType) || TrendType.PB.equals(trendType)) {
			MqDailyBasicParam param = new MqDailyBasicParam();
			param.setTsCode(tsCode);
			List<MqDailyBasic> dailyList = dailyBasicDao.selectByParam(param);

			for (MqDailyBasic daily: dailyList) {
				if (daily.getDate().compareTo(basic.getListDate()) < 0) {
					// Filter info before list. Impossible case
					continue;
				}
				if (TrendType.PE.equals(trendType)) {
					addToTrend(trend, daily.getDate(),  daily.getDprofitPe(), null);
				} if (TrendType.PB.equals(trendType)) {
					addToTrend(trend, daily.getDate(),  daily.getPb(), null);
				}
			}
		} else if (TrendType.REVENUE.equals(trendType) || TrendType.DPROFIT.equals(trendType)) {
    		List<MqQuarterBasic> quarterList = quarterBasicDao.selectTrendByCode(tsCode);
    		Map<String, MqQuarterBasic> quarterMap = new HashMap<>();
			Iterator<MqQuarterBasic> quarterIt = quarterList.iterator();
			while (quarterIt.hasNext()) {
				MqQuarterBasic quarter = quarterIt.next();
				if (TrendType.REVENUE.equals(trendType) && quarter.getRevenuePeriod() != null && (isQ4(quarter.getRevenuePeriod()) || !quarterIt.hasNext())) {
					quarterMap.put(quarter.getRevenuePeriod(), quarter);
				} else if (TrendType.DPROFIT.equals(trendType) && quarter.getDprofitPeriod() != null && (isQ4(quarter.getDprofitPeriod()) || !quarterIt.hasNext())) {
					quarterMap.put(quarter.getDprofitPeriod(), quarter);
				}
			}

			List<String> periodList = quarterMap.keySet().stream().sorted().collect(Collectors.toList());
			MqQuarterBasic last = null;
			for (String period: periodList) {
				MqQuarterBasic quarter = quarterMap.get(period);
				if (quarter == null) {
					continue;
				}
				String quarterStr = DateTimeUtils.convertToQuarter(period);
				if (quarterStr == null) {
					continue;
				}
				if (!isQ4(quarterStr)) {
					quarterStr = quarterStr + " LTM";
				}
				if (!quarter.getReportPeriod().equals(quarter.getForecastPeriod()) && period.equals(quarter.getForecastPeriod())) {
					quarterStr = quarterStr + " (含预告)";
				}
				if (TrendType.REVENUE.equals(trendType)) {
					BigDecimal y1 = quarter.getRevenue();
					BigDecimal y2 = quarter.getRevenueYoy();
					if (!isQ4(quarterStr)) {
						y1 = quarter.getRevenueLtm();
						y2 = BigDecimalUtils.yoy(quarter.getRevenueLtm(), last.getRevenue());
					}
					addToTrend(trend, quarterStr, y1, y2);
				} else if (TrendType.DPROFIT.equals(trendType)) {
					BigDecimal y1 = quarter.getDprofit();
					BigDecimal y2 = quarter.getDprofitYoy();
					if (!isQ4(quarterStr)) {
						y1 = quarter.getDprofitLtm();
						y2 = BigDecimalUtils.yoy(quarter.getDprofitLtm(), last.getDprofit());
					}
					addToTrend(trend, quarterStr, y1, y2);
				}
				last = quarter;
			}
		} else if (TrendType.REVENUE_QUARTER.equals(trendType) || TrendType.DPROFIT_QUARTER.equals(trendType)) {
			List<MqQuarterBasic> quarterList = quarterBasicDao.selectTrendByCode(tsCode);
			Map<String, MqQuarterBasic> quarterMap = new HashMap<>();
			for (MqQuarterBasic quarter: quarterList) {
				if (TrendType.REVENUE.equals(trendType) && quarter.getRevenuePeriod() != null) {
					quarterMap.put(quarter.getRevenuePeriod(), quarter);
				} else if (TrendType.DPROFIT.equals(trendType) && quarter.getDprofitPeriod() != null) {
					quarterMap.put(quarter.getDprofitPeriod(), quarter);
				}
			}
			List<String> periodList = quarterMap.keySet().stream().sorted().collect(Collectors.toList());
			for (String period: periodList) {
				MqQuarterBasic quarter = quarterMap.get(period);
				if (quarter == null) {
					continue;
				}
				String quarterStr = DateTimeUtils.convertToQuarter(period);
				if (quarterStr == null) {
					continue;
				}
				if (!quarter.getReportPeriod().equals(quarter.getForecastPeriod()) && period.equals(quarter.getForecastPeriod())) {
					quarterStr = quarterStr + " (含预告)";
				}
				if (TrendType.REVENUE.equals(trendType)) {
					BigDecimal y1 = quarter.getQuarterRevenue();
					BigDecimal y2 = quarter.getQuarterRevenueYoy();
					addToTrend(trend, quarterStr, y1, y2);
				} else if (TrendType.DPROFIT.equals(trendType)) {
					BigDecimal y1 = quarter.getQuarterDprofit();
					BigDecimal y2 = quarter.getQuarterDprofitYoy();
					addToTrend(trend, quarterStr, y1, y2);
				}
			}
		}

    	return trend;
	}

	private Boolean isQ4(String period) {
    	return period != null && (period.endsWith("1231") || period.endsWith("Q4"));
	}

	private void addToTrend(MqShareTrend trend, String x, BigDecimal y1, BigDecimal y2) {
    	if (trend == null || x == null) {
    		return ;
		}
    	trend.getX().add(x);
    	trend.getVl1().add(y1);
    	trend.getVl2().add(y2);
	}
}
