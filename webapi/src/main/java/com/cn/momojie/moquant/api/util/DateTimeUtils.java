package com.cn.momojie.moquant.api.util;

import java.text.SimpleDateFormat;
import java.util.Date;

import lombok.extern.slf4j.Slf4j;

@Slf4j
public class DateTimeUtils {

    public static String getCurrentDt() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        return sdf.format(new Date());
    }

    public static String convertToQuarter(String period) {
    	try {
			Integer year = Integer.valueOf(period.substring(0, 4));
			Integer month = Integer.valueOf(period.substring(4, 6));
			Integer quarter = 0;
			if (month > 0 && month <= 12 && month % 3 == 0) {
				quarter = month / 3;
			}
			if (quarter != 0) {
				return String.format("%04d Q%d", year, quarter);
			}
		} catch (Exception e) {
    		log.error("Fail to convert period to xxxxQx. {}", period);
		}
    	return null;
	}
}
