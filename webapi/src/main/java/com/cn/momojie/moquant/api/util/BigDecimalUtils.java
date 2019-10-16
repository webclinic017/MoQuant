package com.cn.momojie.moquant.api.util;

import java.math.BigDecimal;
import java.math.RoundingMode;

public class BigDecimalUtils {

    public static BigDecimal notNull(BigDecimal num) {
        return num == null ? BigDecimal.ZERO : num;
    }

    public static Boolean isZero(BigDecimal num) {
        return BigDecimal.ZERO.equals(num);
    }

    public static BigDecimal abs(BigDecimal num) {
        return num == null ? BigDecimal.ZERO : num.abs();
    }

    public static BigDecimal add(BigDecimal... nums) {
        BigDecimal result = BigDecimal.ZERO;
        for (BigDecimal num: nums) {
            if (num != null) {
                result = result.add(num);
            }
        }
        return result;
    }

    public static BigDecimal sub(BigDecimal to, BigDecimal... nums) {
        BigDecimal result = to == null ? BigDecimal.ZERO : to;
        for (BigDecimal num: nums) {
            if (num != null) {
                result = result.subtract(num);
            }
        }
        return result;
    }

    public static BigDecimal divide(BigDecimal a, BigDecimal b, int scale) {
        if (a == null || b == null || isZero(b)) {
            return BigDecimal.ZERO;
        }
        return a.setScale(scale, RoundingMode.HALF_DOWN).divide(b, BigDecimal.ROUND_HALF_DOWN);
    }

    public static BigDecimal divide(BigDecimal a, BigDecimal b) {
        return divide(a, b, 10);
    }

    public static BigDecimal yoy(BigDecimal now, BigDecimal last) {
        return divide(sub(now, last), abs(last));
    }
}
