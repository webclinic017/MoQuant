package com.cn.momojie.moquant.api.service;

import com.cn.momojie.moquant.api.constant.SysParamKey;
import com.cn.momojie.moquant.api.constant.TrendType;
import com.cn.momojie.moquant.api.dao.*;
import com.cn.momojie.moquant.api.dto.MqDailyBasic;
import com.cn.momojie.moquant.api.dto.MqForecastAgg;
import com.cn.momojie.moquant.api.dto.MqMessage;
import com.cn.momojie.moquant.api.dto.MqQuarterBasic;
import com.cn.momojie.moquant.api.dto.ts.TsBasic;
import com.cn.momojie.moquant.api.param.*;
import com.cn.momojie.moquant.api.util.BigDecimalUtils;
import com.cn.momojie.moquant.api.util.DateTimeUtils;
import com.cn.momojie.moquant.api.util.PinYinUtil;
import com.cn.momojie.moquant.api.vo.*;
import com.github.pagehelper.PageHelper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

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
    private MqShareNoteDao noteDao;

    @Autowired
    private MqForecastAggDao forecastAggDao;

    @Autowired
    private MqMessageDao messageDao;

    @Autowired
    private MqSysParamService mqSysParamService;

    public PageResult getLatestListByOrder(MqDailyBasicParam param) {
        param.setDt(getLatestDt());
        PageHelper.startPage(param.getPageNum(), param.getPageSize());
        List<MqDailyBasic> list = dailyBasicDao.selectByParam(param);
        return PageResult.fromList(list);
    }

    public PageResult getGrowList(MqShareListParam param) {
    	param.setDt(getLatestDt());
    	param.setScoreBy("grow_score");
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		List<MqDailyBasic> list = dailyBasicDao.getScoreList(param);
		return PageResult.fromList(list);
	}

	public PageResult getValList(MqShareListParam param) {
		param.setDt(getLatestDt());
		param.setScoreBy("val_score");
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		List<MqDailyBasic> list = dailyBasicDao.getScoreList(param);
		return PageResult.fromList(list);
	}

    private String getLatestDt() {
        return mqSysParamService.getString(SysParamKey.CAL_DAILY_DONE);
    }

    public MqShareDetail getLatestByCode(String code) {
		MqShareDetail detail = new MqShareDetail();

		MqDailyBasic daily = dailyBasicDao.selectLatestByCode(code);
		if (daily != null) {
			BeanUtils.copyProperties(daily, detail);
		}

		MqQuarterBasic quarter = quarterBasicDao.selectLatestByCode(code);
		if (quarter != null) {
			BeanUtils.copyProperties(quarter, detail);
		}

		return detail;
    }

	public MqShareTrend getTrendFromDaily(MqTrendParam input, TsBasic basic,
			Function<MqDailyBasic, BigDecimal> y1Get, Function<MqDailyBasic, BigDecimal> y2Get) {
		MqShareTrend trend = new MqShareTrend();
		String tsCode = input.getTsCode();
		String trendType = input.getTrendType();
		MqDailyBasicParam param = new MqDailyBasicParam();
		param.setTsCode(tsCode);
		param.setForTrend(trendType);
		param.setOrderByDate(true);
		List<MqDailyBasic> dailyList = dailyBasicDao.selectByParam(param);

		for (MqDailyBasic daily: dailyList) {
			if (daily.getDate().compareTo(basic.getListDate()) < 0) {
				// Filter info before list. Impossible case
				continue;
			}
			BigDecimal y1 = null, y2 = null;
			if (y1Get != null) {
				y1 = y1Get.apply(daily);
			}
			if (y2Get != null) {
				y2 = y2Get.apply(daily);
			}
			if (y1 != null) {
				addToTrend(trend, daily.getDate(), y1, y2);
			}
		}
		return trend;
	}

    public MqShareTrend getTrendFromQuarter(MqTrendParam input, Function<MqQuarterBasic, String> quarterGet,
			Function<MqQuarterBasic, BigDecimal> y1Get, Function<MqQuarterBasic, BigDecimal> y2Get,
			Boolean calYoyOnY2InYear) {
		MqShareTrend trend = new MqShareTrend();
		String tsCode = input.getTsCode();
		String trendType = input.getTrendType();
		MqQuarterBasicParam param = new MqQuarterBasicParam();
		param.setTsCode(tsCode);
		param.setTrendType(trendType);
		List<MqQuarterBasic> quarterList = quarterBasicDao.selectTrendByParam(param);
		Map<String, MqQuarterBasic> quarterMap = new HashMap<>();
		Iterator<MqQuarterBasic> quarterIt = quarterList.iterator();
		while (quarterIt.hasNext()) {
			MqQuarterBasic quarter = quarterIt.next();
			String period = quarterGet.apply(quarter);
			if (StringUtils.isEmpty(period)) {
				continue;
			}
			if (TrendType.isYear(trendType)) {
				if (isQ4(period) || !quarterIt.hasNext()) {
					quarterMap.put(period, quarter);
				}
			} else {
				quarterMap.put(period, quarter);
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
			if (TrendType.isYear(trendType) && !isQ4(quarterStr)) {
				quarterStr = quarterStr + " LTM";
			}
			if (!quarter.getReportPeriod().equals(quarter.getForecastPeriod()) && period.equals(quarter.getForecastPeriod())) {
				quarterStr = quarterStr + " (含预告)";
			}
			BigDecimal y1 = null, y2 = null;
			if (y1Get != null) {
				y1 = y1Get.apply(quarter);
			}
			if (y2Get != null) {
				y2 = y2Get.apply(quarter);
				if (TrendType.isYear(trendType) && calYoyOnY2InYear) {
					if (last != null) {
						BigDecimal lastValue = y2Get.apply(last);
						y2 = BigDecimalUtils.yoy(y2, lastValue);
					} else {
						y2 = BigDecimal.ZERO;
					}
				}
			}
			if (y1 != null) {
				addToTrend(trend, quarterStr, y1, y2);
				last = quarter;
			}
		}
		return trend;
	}

	public MqShareTrend getTrend(MqTrendParam input) {
		MqShareTrend trend = new MqShareTrend();
		String tsCode = input.getTsCode();
		String trendType = input.getTrendType();
		if (tsCode == null || trendType == null) {
			return trend;
		}
    	TsBasic basic = tsBasicDao.selectByCode(tsCode);
    	if (basic == null) {
    		log.error("Can't find share basic of {}", tsCode);
    		return trend;
		}
    	Boolean isYear = TrendType.isYear(trendType);
    	if (TrendType.PE.equals(trendType)) {
    		return getTrendFromDaily(input, basic, MqDailyBasic::getDprofitPe, null);
		} else if (TrendType.PB.equals(trendType)) {
			return getTrendFromDaily(input, basic, MqDailyBasic::getPb, null);
		} else if (TrendType.DIVIDEND.equals(trendType)) {
			return getTrendFromDaily(input, basic, MqDailyBasic::getDividendYields, null);
		} else if (TrendType.REVENUE_YEAR.equals(trendType) || TrendType.REVENUE_QUARTER.equals(trendType)) {
    		return getTrendFromQuarter(input, MqQuarterBasic::getRevenuePeriod,
					isYear ? MqQuarterBasic::getRevenue : MqQuarterBasic::getQuarterRevenue,
					isYear ? MqQuarterBasic::getRevenueLtm : MqQuarterBasic::getQuarterRevenueYoy,
					isYear);
		} else if (TrendType.DPROFIT_YEAR.equals(trendType) || TrendType.DPROFIT_QUARTER.equals(trendType)) {
			return getTrendFromQuarter(input, MqQuarterBasic::getDprofitPeriod,
					isYear ? MqQuarterBasic::getDprofit : MqQuarterBasic::getQuarterDprofit,
					isYear ? MqQuarterBasic::getDprofitLtm : MqQuarterBasic::getQuarterDprofitYoy,
					isYear);
		} else if (TrendType.NPROFIT_YEAR.equals(trendType) || TrendType.NPROFIT_QUARTER.equals(trendType)) {
			return getTrendFromQuarter(input, MqQuarterBasic::getNprofitPeriod,
					isYear ? MqQuarterBasic::getNprofit : MqQuarterBasic::getQuarterNprofit,
					isYear ? MqQuarterBasic::getNprofitLtm : MqQuarterBasic::getQuarterNprofitYoy,
					isYear);
		} else if (TrendType.DIVIDEND_PROFIT.equals(trendType)) {
    		return getTrendFromQuarter(input, MqQuarterBasic::getForecastPeriod,
					MqQuarterBasic::getDividendProfitRatio, null, false);
		} else if (TrendType.ROE.equals(trendType)) {
			return getTrendFromQuarter(input, MqQuarterBasic::getDprofitPeriod, MqQuarterBasic::getRoe,
					null, false);
		} else if (TrendType.DPROFIT_MARGIN.equals(trendType)) {
			return getTrendFromQuarter(input, MqQuarterBasic::getDprofitPeriod, MqQuarterBasic::getDprofitMargin,
					null, false);
		} else if (TrendType.TURNOVER_RATE.equals(trendType)) {
			return getTrendFromQuarter(input, MqQuarterBasic::getRevenuePeriod, MqQuarterBasic::getTurnoverRate,
					null, false);
		} else if (TrendType.EM.equals(trendType)) {
			return getTrendFromQuarter(input, MqQuarterBasic::getForecastPeriod, MqQuarterBasic::getEquityMultiplier,
					null, false);
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
    	if (y1 == null && y2 == null) {
    		return ;
		}
    	if (x.length() == 8) {
    		x = x.substring(0, 4) + '-' + x.substring(4, 6) + '-' + x.substring(6, 8);
		}
    	trend.getX().add(x);
    	trend.getVl1().add(y1);
    	trend.getVl2().add(y2);
	}

	public List<ShareListItem> getAllShare() {
		List<TsBasic> list = tsBasicDao.getAllForSearchList();
		return list.stream().map(i -> {
			ShareListItem ret = new ShareListItem();
			ret.setTsCode(i.getTsCode());
			ret.setName(i.getName());
			ret.setPy(PinYinUtil.convertToPyFirst(i.getName()));
			return ret;
		}).collect(Collectors.toList());
	}

	public PageResult<MqShareNoteVo> getNotes(MqCodePageParam param) {
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		if ("all".equals(param.getTsCode())) {
			param.setTsCode(null);
		}
		List<MqShareNoteVo> noteList = noteDao.getByCode(param.getTsCode());
		List<Long> noteIdList = noteList.stream().map(MqShareNoteVo::getId).collect(Collectors.toList());
		List<MqShareNoteRelationVo> relationList = noteDao.getRelated(noteIdList);
		Map<Long, List<MqShareNoteRelationVo>> relationMap = relationList.stream().collect(Collectors.groupingBy(MqShareNoteRelationVo::getNoteId));
		for (MqShareNoteVo note: noteList) {
			note.setRelatedShareList(relationMap.get(note.getId()));
			if (note.getRelatedShareList() == null) {
				note.setRelatedShareList(new ArrayList<>());
			}
		}
		return PageResult.fromList(noteList);
	}

	public MqForecastInfo getForecastInfo(String code) {
		MqForecastInfo result = new MqForecastInfo();

		MqQuarterBasic quarter = quarterBasicDao.selectLatestByCode(code);

		if (quarter.getReportPeriod() == null || quarter.getForecastPeriod() == null) {
			return result;
		}
		if (quarter.getReportPeriod().equals(quarter.getForecastPeriod())) {
			return result;
		}
		result.setPeriod(quarter.getForecastPeriod());
		result.setDprofit(quarter.getDprofit());
		result.setLatest(true);

		MqForecastAgg forecast = forecastAggDao.selectLatest(quarter.getTsCode());
		if (forecast != null) {
			result.setForecastReason(forecast.getChangedReason());
			result.setAdjustReason(forecast.getManualAdjustReason());
			result.setOneTime(forecast.getOneTime());
			result.setFromManual(forecast.getFromManual());
		}

		return result;
	}

	public PageResult<MqMessage> getLatestReportList(MqMessageParam param) {
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		return PageResult.fromList(messageDao.getLatestByType(param.getMsgType()));
	}
}
