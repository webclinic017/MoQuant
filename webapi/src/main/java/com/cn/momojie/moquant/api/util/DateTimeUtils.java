package com.cn.momojie.moquant.api.util;

import java.time.format.DateTimeFormatter;
import java.util.Calendar;
import java.util.Date;

import org.apache.commons.lang3.time.FastDateFormat;

import lombok.extern.slf4j.Slf4j;

@Slf4j
public class DateTimeUtils {

	private static final FastDateFormat DT_FORMAT = FastDateFormat.getInstance("yyyyMMdd");

    public static String getTodayDt() {
        return getDt(new Date());
    }

    public static String getYesterdayDt() {
    	return getDtFromDelta(-1);
	}

    public static String getDt(Date d) {
		return DT_FORMAT.format(d);
	}

	public static String getDtFromDelta(Integer dayDelta) {
		Calendar c = Calendar.getInstance();
		c.add(Calendar.DATE, dayDelta);
		return getDt(c.getTime());
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
				return String.format("%04d-Q%d", year, quarter);
			}
		} catch (Exception e) {
    		log.error("Fail to convert period to xxxxQx. {}", period);
		}
    	return null;
	}
}
