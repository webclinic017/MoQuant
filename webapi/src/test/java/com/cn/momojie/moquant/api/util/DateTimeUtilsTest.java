package com.cn.momojie.moquant.api.util;

import org.junit.Assert;
import org.junit.Test;

public class DateTimeUtilsTest {

	@Test
	public void testDt() {
		Assert.assertTrue(DateTimeUtils.getTodayDt().compareTo(DateTimeUtils.getYesterdayDt()) > 0);
	}
}
