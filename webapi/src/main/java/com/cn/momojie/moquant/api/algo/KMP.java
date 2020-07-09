package com.cn.momojie.moquant.api.algo;


public class KMP {

    public static Integer indexOf(String s, String p) {
        Integer next[] = new Integer[p.length()];

        int x = 1;
        int now = 0;

        next[0] = 0;

        while (x < p.length()) {
            if (p.charAt(now) == p.charAt(x)) {
                now += 1;
                next[x] = now;
                x += 1;
            } else if (now > 0) {
                now = next[now];
            } else {
                next[x] = 0;
                x += 1;
            }
        }

        int target = 0; // 目标串s匹配到的位置
        int pos = 0; // 模式串p匹配到的位置

        while (target < s.length() && pos < p.length() ) {
            if (s.charAt(target) == p.charAt(pos)) {
                target += 1;
                pos += 1;
            } else if (pos == 0) {
                target += 1;
            } else {
                pos = next[pos];
            }
        }

        if (pos == p.length()) {
            return target - p.length();
        } else {
            return -1;
        }

    }
}
