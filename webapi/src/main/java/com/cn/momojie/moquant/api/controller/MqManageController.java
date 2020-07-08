package com.cn.momojie.moquant.api.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;

import com.cn.momojie.moquant.api.param.manage.NoteEditParam;
import com.cn.momojie.moquant.api.service.MqManageService;
import com.cn.momojie.moquant.api.vo.OperationResp;

@Controller
@RequestMapping("/manage")
public class MqManageController {

	@Autowired
	private MqManageService manageService;

	@RequestMapping(path = "addNote", method = RequestMethod.POST)
	public OperationResp addNote(@RequestBody NoteEditParam input) {
		return manageService.editNote(input, true);
	}

	@RequestMapping(path = "editNote", method = RequestMethod.POST)
	public OperationResp editNote(@RequestBody NoteEditParam input) {
		return manageService.editNote(input, false);
	}
}
