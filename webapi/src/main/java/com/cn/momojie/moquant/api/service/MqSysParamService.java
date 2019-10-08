package com.cn.momojie.moquant.api.service;

import com.cn.momojie.moquant.api.dao.MqSysParamDao;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class MqSysParamService {

    @Autowired
    private MqSysParamDao dao;

    public String getString(String key) {
        return dao.getByKey(key);
    }
}
