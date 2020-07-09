package com.cn.momojie.moquant.api.vo;

import lombok.Data;

@Data
public class OperationResp<T> {

	private Boolean success;

	private String msg;

	private T data;

	public static <T> OperationResp of(Boolean success, String msg, T data) {
		OperationResp r = new OperationResp();
		r.setSuccess(success);
		r.setMsg(msg);
		r.setData(data);
		return r;
	}

	public static <T> OperationResp ok(String msg, T data) {
		return of(true, msg, data);
	}

	public static <T> OperationResp ok(T data) {
		return ok("操作成功");
	}

	public static <T> OperationResp fail(String msg, T data) {
		return of(false, msg, data);
	}

	public static <T> OperationResp fail(T data) {
		return fail("操作失败", data);
	}
}
