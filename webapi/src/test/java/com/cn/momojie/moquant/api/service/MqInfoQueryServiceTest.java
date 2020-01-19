package com.cn.momojie.moquant.api.service;

import org.junit.Assert;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;

import com.cn.momojie.moquant.api.SpringBaseTest;
import com.cn.momojie.moquant.api.param.MqCodePageParam;
import com.cn.momojie.moquant.api.vo.MqShareDetail;
import com.cn.momojie.moquant.api.vo.PageResult;

public class MqInfoQueryServiceTest extends SpringBaseTest {

	@Autowired
	private MqInfoQueryService service;

	@Test
	public void testNote() {
		MqCodePageParam param = new MqCodePageParam();
		param.setTsCode("000055.SZ");
		PageResult result = service.getNotes(param);
		Assert.assertTrue(result.getTotal() > 0);

		param.setTsCode("");
		PageResult result2 = service.getNotes(param);
		Assert.assertTrue(result2.getTotal() > 0);
	}
}
