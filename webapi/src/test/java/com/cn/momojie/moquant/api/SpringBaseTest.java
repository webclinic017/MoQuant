package com.cn.momojie.moquant.api;

import org.junit.runner.RunWith;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.TestExecutionListeners;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.context.support.DependencyInjectionTestExecutionListener;
import org.springframework.test.context.support.DirtiesContextTestExecutionListener;
import org.springframework.test.context.web.ServletTestExecutionListener;

import lombok.extern.slf4j.Slf4j;

@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(locations = {"classpath:applicationContext.xml"}, inheritLocations = true)
@TestExecutionListeners({ServletTestExecutionListener.class, DependencyInjectionTestExecutionListener.class,
		DirtiesContextTestExecutionListener.class})
@Slf4j
public abstract class SpringBaseTest {
}
