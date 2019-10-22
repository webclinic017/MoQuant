package com.cn.momojie.moquant.api.util;

import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Set;

import net.sourceforge.pinyin4j.PinyinHelper;
import net.sourceforge.pinyin4j.format.HanyuPinyinCaseType;
import net.sourceforge.pinyin4j.format.HanyuPinyinOutputFormat;
import net.sourceforge.pinyin4j.format.HanyuPinyinToneType;
import net.sourceforge.pinyin4j.format.HanyuPinyinVCharType;
import net.sourceforge.pinyin4j.format.exception.BadHanyuPinyinOutputFormatCombination;

public class PinYinUtil {

	private static final HanyuPinyinOutputFormat format = new HanyuPinyinOutputFormat();

	static {
		format.setCaseType(HanyuPinyinCaseType.LOWERCASE);
		format.setToneType(HanyuPinyinToneType.WITHOUT_TONE);
		format.setVCharType(HanyuPinyinVCharType.WITH_U_UNICODE);
	}

	private static void dfs(List<Set<Character>> firstList, Integer index, StringBuilder sb, Character arr[]) {
		if (index == firstList.size()) {
			if (sb.length() > 0) {
				sb.append(',');
			}
			for (Character c: arr) {
				sb.append(c);
			}
			return ;
		}
		for (Character c: firstList.get(index)) {
			arr[index] = c;
			dfs(firstList, index + 1, sb, arr);
		}
	}

	public static String convertToPyFirst(String str) {
		char[] input = str.trim().toCharArray();

		List<Set<Character>> firstList = new LinkedList<>();
		try {
			for (int i = 0; i < input.length; i++) {
				Set<Character> firstSet = new HashSet<>();
				if (Character.toString(input[i]).matches("[\u4E00-\u9FA5]+")) {
					String[] temp = PinyinHelper.toHanyuPinyinStringArray(input[i], format);
					for (String s: temp) {
						firstSet.add(s.charAt(0));
					}
				} else {
					firstSet.add(input[i]);
				}
				firstList.add(firstSet);
			}
		} catch (BadHanyuPinyinOutputFormatCombination e) {
			e.printStackTrace();
		}

		StringBuilder sb = new StringBuilder();
		Character arr[] = new Character[firstList.size()];
		dfs(firstList, 0, sb, arr);
		return sb.toString();
	}
}
