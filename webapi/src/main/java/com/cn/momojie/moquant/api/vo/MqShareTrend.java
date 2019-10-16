package com.cn.momojie.moquant.api.vo;

import java.math.BigDecimal;
import java.util.LinkedList;
import java.util.List;

import lombok.Data;

@Data
public class MqShareTrend {

	private List<String> x = new LinkedList<>();

	private List<BigDecimal> vl1 = new LinkedList<>();

	private List<BigDecimal> vl2 = new LinkedList<>();
}
