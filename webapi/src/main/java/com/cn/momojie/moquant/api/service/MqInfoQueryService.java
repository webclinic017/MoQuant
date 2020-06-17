package com.cn.momojie.moquant.api.service;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

import com.cn.momojie.moquant.api.constant.MqIndicatorEnum;
import org.apache.commons.collections.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.cn.momojie.moquant.api.constant.MqReportType;
import com.cn.momojie.moquant.api.dao.*;
import com.cn.momojie.moquant.api.dto.MqDailyIndicator;
import com.cn.momojie.moquant.api.dto.MqMessage;
import com.cn.momojie.moquant.api.dto.MqQuarterIndicator;
import com.cn.momojie.moquant.api.dto.MqShareAll;
import com.cn.momojie.moquant.api.dto.ts.TsBasic;
import com.cn.momojie.moquant.api.dto.ts.TsForecast;
import com.cn.momojie.moquant.api.param.*;
import com.cn.momojie.moquant.api.util.DateTimeUtils;
import com.cn.momojie.moquant.api.util.PinYinUtil;
import com.cn.momojie.moquant.api.vo.*;
import com.github.pagehelper.PageHelper;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class MqInfoQueryService {

	@Autowired
	private TsBasicDao tsBasicDao;

	@Autowired
	private TsForecastDao tsForecastDao;

    @Autowired
    private MqDailyIndicatorDao dailyIndicatorDao;

    @Autowired
    private MqQuarterIndicatorDao quarterIndicatorDao;

    @Autowired
    private MqShareNoteDao noteDao;

    @Autowired
    private MqMessageDao messageDao;

    public PageResult getLatestListByOrder(MqDailyBasicParam param) {
        return null;
    }

    public PageResult getGrowList(MqShareListParam param) {
    	param.setUnderDate(DateTimeUtils.getTodayDt());
    	param.setScoreBy("grow_score");
		List<String> codeList = dailyIndicatorDao.getScoreList(param);
		PageResult<MqShareAll> result = new PageResult<>();
		result.setTotal(Long.valueOf(codeList.size()));

		Map<String, TsBasic> basicMap = getBasicMap(codeList);
		Map<String, Map<String, MqDailyIndicator>> dailyMap = getDailyLatest(codeList, Arrays.asList("pe"));
		Map<String, Map<String, MqQuarterIndicator>> quarterMap = getQuarterLatest(codeList, Arrays.asList("revenue_quarter", "dprofit_quarter"));

		List<MqShareAll> pageList = new ArrayList<>(codeList.size());

		for (String tsCode: codeList) {
			MqShareAll all = new MqShareAll();
			all.setTsCode(tsCode);

			TsBasic basic = basicMap.get(tsCode);
			if (basic == null) {
				log.error("Can't find ts_basic of {}", tsCode);
			} else {
				all.setShareName(basic.getName());
			}

			all.setDailyIndicators(dailyMap.getOrDefault(tsCode, new HashMap<>()));
			all.setQuarterIndicators(quarterMap.getOrDefault(tsCode, new HashMap<>()));
			pageList.add(all);
		}
		result.setList(pageList);

		return result;
	}

	public PageResult getValList(MqShareListParam param) {
		param.setUnderDate(DateTimeUtils.getTodayDt());
		param.setScoreBy("val_score");
		List<String> codeList = dailyIndicatorDao.getScoreList(param);
		PageResult<MqShareAll> result = new PageResult<>();
		result.setTotal(Long.valueOf(codeList.size()));

		Map<String, TsBasic> basicMap = getBasicMap(codeList);
		Map<String, Map<String, MqDailyIndicator>> dailyMap = getDailyLatest(codeList, Arrays.asList("pe", "pb", "dividend_yields"));
		Map<String, Map<String, MqQuarterIndicator>> quarterMap = getQuarterLatest(codeList, Arrays.asList(""));

		List<MqShareAll> pageList = new ArrayList<>(codeList.size());

		for (String tsCode: codeList) {
			MqShareAll all = new MqShareAll();
			all.setTsCode(tsCode);

			TsBasic basic = basicMap.get(tsCode);
			if (basic == null) {
				log.error("Can't find ts_basic of {}", tsCode);
			} else {
				all.setShareName(basic.getName());
			}

			all.setDailyIndicators(dailyMap.getOrDefault(tsCode, new HashMap<>()));
			all.setQuarterIndicators(quarterMap.getOrDefault(tsCode, new HashMap<>()));
			pageList.add(all);
		}

		result.setList(pageList);
		return result;
	}

	private Map<String, TsBasic> getBasicMap(Collection<String> codeList) {
		Map<String, TsBasic> result = new HashMap<>();
		if (CollectionUtils.isEmpty(codeList)) {
			return result;
		}

		List<TsBasic> basicList = tsBasicDao.selectByCodes(codeList);
		for (TsBasic basic: basicList) {
			result.put(basic.getTsCode(), basic);
		}

		return result;
	}

	private Map<String, Map<String, MqDailyIndicator>> getDailyLatest(Collection<String> codeList, Collection<String> nameList) {
		Map<String, Map<String, MqDailyIndicator>> codeNameMap = new HashMap<>();
		if (CollectionUtils.isEmpty(codeList)) {
			return codeNameMap;
		}

		List<MqDailyIndicator> indicatorList = dailyIndicatorDao.getDailyLatest(codeList, nameList,
				DateTimeUtils.getTodayDt());
		for (MqDailyIndicator i: indicatorList) {
			String tsCode = i.getTsCode();
			String name = i.getName();
			if (!codeNameMap.containsKey(tsCode)) {
				codeNameMap.put(tsCode, new HashMap<>());
			}
			Map<String, MqDailyIndicator> nameMap = codeNameMap.get(tsCode);
			nameMap.put(name, i);
		}

		return codeNameMap;
	}

	private Map<String, Map<String, MqQuarterIndicator>> getQuarterLatest(Collection<String> codeList, Collection<String> nameList) {
		Map<String, Map<String, MqQuarterIndicator>> codeNameMap = new HashMap<>();
		if (CollectionUtils.isEmpty(codeList)) {
			return codeNameMap;
		}

		List<MqQuarterIndicator> indicatorList = quarterIndicatorDao.getQuarterLatest(codeList, nameList,
				DateTimeUtils.getTodayDt(), DateTimeUtils.getDtFromDelta(-365));
		for (MqQuarterIndicator i: indicatorList) {
			String tsCode = i.getTsCode();
			String name = i.getName();
			if (!codeNameMap.containsKey(tsCode)) {
				codeNameMap.put(tsCode, new HashMap<>());
			}
			Map<String, MqQuarterIndicator> nameMap = codeNameMap.get(tsCode);
			nameMap.put(name, i);
		}

		return codeNameMap;
	}

    public MqShareAll getLatestByCode(String tsCode) {
		List<String> codeList = Arrays.asList(tsCode);

		Map<String, TsBasic> basicMap = getBasicMap(codeList);
		Map<String, Map<String, MqDailyIndicator>> dailyMap = getDailyLatest(codeList, null);
		Map<String, Map<String, MqQuarterIndicator>> quarterMap = getQuarterLatest(codeList, null);

		MqShareAll all = new MqShareAll();
		all.setTsCode(tsCode);

		TsBasic basic = basicMap.get(tsCode);
		if (basic == null) {
			log.error("Can't find ts_basic of {}", tsCode);
		} else {
			all.setShareName(basic.getName());
		}

		all.setDailyIndicators(dailyMap.getOrDefault(tsCode, new HashMap<>()));
		all.setQuarterIndicators(quarterMap.getOrDefault(tsCode, new HashMap<>()));

    	return all;
    }

	public MqShareTrend getTrend(MqTrendParam input) {
		MqShareTrend trend = new MqShareTrend();

		MqIndicatorEnum i = MqIndicatorEnum.fromName(input.getIndicatorName());
		if (i == null) {
			log.error("找不到对应的指标");
			return trend;
		}

		if (i.isDaily) {
			List<MqDailyIndicator> list = dailyIndicatorDao.getTrend(input.getTsCode(), i.name);
			for (MqDailyIndicator mdi: list) {
				addToTrend(trend, mdi.getUpdateDate(), mdi.getValue(), null);
			}
		} else {
			List<MqQuarterIndicator> list = quarterIndicatorDao.getTrend(input.getTsCode(), i.name);
			for (MqQuarterIndicator mqi: list) {
				addToTrend(trend, DateTimeUtils.convertToQuarter(mqi.getPeriod()), mqi.getValue(), mqi.getYoy());
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
		List<MqShareNoteRelationVo> relationList = CollectionUtils.isEmpty(noteIdList) ? new ArrayList<>() : noteDao.getRelated(noteIdList);
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
		MqForecastInfo info = new MqForecastInfo();

		Map<String, Map<String, MqQuarterIndicator>> codeNameMap = getQuarterLatest(Arrays.asList(code), Arrays.asList("nprofit", "dprofit"));
		Map<String, MqQuarterIndicator> nameMap = codeNameMap.get(code);
		if (nameMap == null) {
			return info;
		}

		MqQuarterIndicator nprofit = nameMap.get("nprofit");
		if (nprofit == null) {
			return info;
		}

		String period = nprofit.getPeriod();
		Integer reportType = nprofit.getReportType();

		if (reportType == null || !(
				(reportType & (1 << MqReportType.EXPRESS)) > 0 || (reportType & (1 << MqReportType.FORECAST)) > 0
		)) {
			return info;
		}

		info.setPeriod(period);

		TsForecast forecast = tsForecastDao.selectOne(code, period);
		if (forecast != null && forecast.getChangeReason() != null) {
			info.setLatest(true);
			info.setForecastReason(forecast.getChangeReason());
		}


		if (nprofit != null && nprofit.getValue() != null) {
			info.setNprofit(nprofit.getValue());
		}

		MqQuarterIndicator dprofit = nameMap.get("dprofit");
		if (dprofit != null && dprofit.getValue() != null) {
			info.setDprofit(dprofit.getValue());
		}

		return info;
	}

	public PageResult<MqMessage> getLatestReportList(MqMessageParam param) {
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		return PageResult.fromList(messageDao.getLatestByType(param.getMsgType()));
	}
}
