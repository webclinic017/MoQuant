package com.cn.momojie.moquant.api.service;

import java.math.BigDecimal;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.apache.commons.collections.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.cn.momojie.moquant.api.dao.*;
import com.cn.momojie.moquant.api.dto.*;
import com.cn.momojie.moquant.api.dto.ts.TsBasic;
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
    	param.setYesterday(DateTimeUtils.getYesterdayDt());
    	param.setScoreBy("grow_score");
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		List<MqShareAll> list = dailyIndicatorDao.getScoreList(param);
		PageResult<MqShareAll> result = PageResult.fromList(list);

		List<String> codeList = list.stream().map(MqShareAll::getTsCode).collect(Collectors.toList());

		Map<String, TsBasic> basicMap = getBasicMap(codeList);
		Map<String, Map<String, MqDailyIndicator>> dailyMap = getDailyLatest(codeList, Arrays.asList("pe"));
		Map<String, Map<String, MqQuarterIndicator>> quarterMap = getQuarterLatest(codeList, Arrays.asList("peg"));

		List<MqShareAll> pageList = new ArrayList<>(list.size());

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

		return result;
	}

	public PageResult getValList(MqShareListParam param) {
		param.setScoreBy("val_score");
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		List<MqShareAll> list = dailyIndicatorDao.getScoreList(param);
		return PageResult.fromList(list);
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
				DateTimeUtils.getYesterdayDt());
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
				DateTimeUtils.getYesterdayDt());
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

    public MqShareDetail getLatestByCode(String code) {
		return null;
    }

	public MqShareTrend getTrendFromDaily(MqTrendParam input, TsBasic basic,
			Function<MqShareAll, BigDecimal> y1Get, Function<MqShareAll, BigDecimal> y2Get) {
		return null;
	}

    public MqShareTrend getTrendFromQuarter(MqTrendParam input, Function<MqQuarterBasic, String> quarterGet,
			Function<MqQuarterBasic, BigDecimal> y1Get, Function<MqQuarterBasic, BigDecimal> y2Get,
			Boolean calYoyOnY2InYear) {
		return null;
	}

	public MqShareTrend getTrend(MqTrendParam input) {
		return null;
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
		return null;
	}

	public PageResult<MqMessage> getLatestReportList(MqMessageParam param) {
		PageHelper.startPage(param.getPageNum(), param.getPageSize());
		return PageResult.fromList(messageDao.getLatestByType(param.getMsgType()));
	}
}
