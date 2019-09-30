#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sanic import Sanic
from sanic.response import json

from moquant.utils.json_utils import parse
from moquant.web.basic_response import BasicResponse
import moquant.web.services.mq_basic_service as mq_basic_service

app = Sanic('MoQuant')


@app.route("/get_mq_basic", methods=['POST'])
async def mq_basic(request):
    code = 200
    message = None
    result_list = None
    body_obj = parse(request.body)
    ts_code = body_obj.get('ts_code')
    if body_obj is None or ts_code is None:
        code = 416
        message = '无提供ts_code'
    else:
        result_list = mq_basic_service.get_mq_basic(ts_code)
        if len(result_list) == 0:
            message = '未找到相应信息'
    return json({'code': code, 'message': message, 'data': result_list}, ensure_ascii=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9876)
