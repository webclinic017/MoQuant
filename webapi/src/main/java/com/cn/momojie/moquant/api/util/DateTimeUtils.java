package com.cn.momojie.moquant.api.util;

import java.text.SimpleDateFormat;
import java.util.Date;

public class DateTimeUtils {

    public static String getCurrentDt() {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        return sdf.format(new Date());
    }
}
