package com.cn.momojie.moquant.api.vo;

import lombok.Data;

@Data
public class OperationResp {

	private Boolean success;

	private String msg;

	public static OperationResp of(Boolean success, String msg) {
		OperationResp r = new OperationResp();
		r.setSuccess(success);
		r.setMsg(msg);
		return r;
	}

	public static OperationResp ok(String msg) {
		return of(true, msg);
	}

	public static OperationResp ok() {
		return ok("操作成功");
	}

	public static OperationResp fail(String msg) {
		return of(false, msg);
	}

	public static OperationResp fail() {
		return fail("操作失败");
	}
}
