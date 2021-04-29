class MqQuarterMetricEnum(object):

    def __init__(self, name, explain, is_percent=False, from_name=None, is_cf_h=False):
        self.name = name
        self.from_name = name if from_name is None else from_name
        self.explain = explain
        self.is_percent = is_percent
        self.is_cf_h = is_cf_h  # 现金流量表中只有Q2和Q4有的


# income
revenue = MqQuarterMetricEnum('revenue', '营业收入')
nprofit = MqQuarterMetricEnum('nprofit', '归母净利润', from_name='n_income_attr_p')
total_nprofit = MqQuarterMetricEnum('total_nprofit', '净利润', from_name='n_income')

extract_from_income_list = [revenue, nprofit, total_nprofit]

# balance sheet
total_share = MqQuarterMetricEnum('total_share', '总股本')
notes_receiv = MqQuarterMetricEnum('notes_receiv', '应收票据')
accounts_receiv = MqQuarterMetricEnum('accounts_receiv', '应收账款')
oth_receiv = MqQuarterMetricEnum('oth_receiv', '其他应收款')
div_receiv = MqQuarterMetricEnum('div_receiv', '应收股利')
int_receiv = MqQuarterMetricEnum('int_receiv', '应收利息')
lt_rec = MqQuarterMetricEnum('lt_rec', '长期应收款')
total_cur_liab = MqQuarterMetricEnum('total_cur_liab', '流动负债合计')
total_cur_assets = MqQuarterMetricEnum('total_cur_assets', '流动资产合计')
goodwill = MqQuarterMetricEnum('goodwill', '商誉')
r_and_d = MqQuarterMetricEnum('r_and_d', '研发支出')
intan_assets = MqQuarterMetricEnum('intan_assets', '无形资产')
nassets = MqQuarterMetricEnum('nassets', '净资产', from_name='total_hldr_eqy_exc_min_int')
total_assets = MqQuarterMetricEnum('total_assets', '总资产')
oth_eqt_tools_p_shr = MqQuarterMetricEnum('oth_eqt_tools_p_shr', '优先股/永续债')
money_cap = MqQuarterMetricEnum('money_cap', '货币资金')
oth_cur_assets = MqQuarterMetricEnum('oth_cur_assets', '其他流动资产')
lt_borr = MqQuarterMetricEnum('lt_borr', '长期借款')
st_borr = MqQuarterMetricEnum('st_borr', '短期借款')
notes_payable = MqQuarterMetricEnum('notes_payable', '应付票据')
acct_payable = MqQuarterMetricEnum('acct_payable', '应付账款')
prepayment = MqQuarterMetricEnum('prepayment', '预付款项')
adv_receipts = MqQuarterMetricEnum('adv_receipts', '预收款项')
inventories = MqQuarterMetricEnum('inventories', '存货')
lt_amor_exp = MqQuarterMetricEnum('lt_amor_exp', '长期待摊费用(原待摊费用)')
total_nca = MqQuarterMetricEnum('total_nca', '非流动资产合计')
fa_avail_for_sale = MqQuarterMetricEnum('fa_avail_for_sale', '可供出售金融资产')

extract_from_bs_list = [total_share, notes_receiv, accounts_receiv, oth_receiv, div_receiv, int_receiv, lt_rec,
                        total_cur_liab,
                        total_cur_assets, goodwill, r_and_d, intan_assets, nassets, total_assets, oth_eqt_tools_p_shr,
                        money_cap, oth_cur_assets, lt_borr, st_borr, notes_payable, acct_payable, prepayment,
                        adv_receipts, inventories, lt_amor_exp, total_nca, fa_avail_for_sale]

# cash flow
n_cashflow_act = MqQuarterMetricEnum('n_cashflow_act', '经营活动产生的现金流量净额')
prov_depr_assets = MqQuarterMetricEnum('prov_depr_assets', '资产减值准备', is_cf_h=True)
depr_fa_coga_dpba = MqQuarterMetricEnum('depr_fa_coga_dpba', '固定资产折旧、油气资产折耗、生产性生物资产折旧', is_cf_h=True)
amort_intang_assets = MqQuarterMetricEnum('amort_intang_assets', '无形资产摊销', is_cf_h=True)
lt_amort_deferred_exp = MqQuarterMetricEnum('lt_amort_deferred_exp', '长期待摊费用摊销', is_cf_h=True)
loss_scr_fa = MqQuarterMetricEnum('loss_scr_fa', '固定资产报废损失', is_cf_h=True)

extract_from_cf_list = [n_cashflow_act, prov_depr_assets, depr_fa_coga_dpba, amort_intang_assets, lt_amort_deferred_exp,
                        loss_scr_fa]

# fina indicator
dprofit = MqQuarterMetricEnum('dprofit', '归母扣非净利润', from_name='profit_dedt')

extract_from_fi_list = [dprofit]

# express
express_nprofit = MqQuarterMetricEnum('dprofit', '归母扣非净利润', from_name='n_income')
extract_from_express_list = [revenue, express_nprofit, total_assets, nassets]

# forecast
extract_from_forecast_list = [nprofit]

# dividend
dividend = MqQuarterMetricEnum('dividend', '分红总额')
dividend_ratio = MqQuarterMetricEnum('dividend_ratio', '分红率', is_percent=True)
dividend_ltm = MqQuarterMetricEnum('dividend_ltm', '分红LTM', from_name='dividend')

# ltm
revenue_quarter = MqQuarterMetricEnum('revenue_quarter', '营业收入-单季', from_name='revenue')
revenue_ltm = MqQuarterMetricEnum('revenue_ltm', '营业收入-LTM', from_name='revenue_quarter')
nprofit_quarter = MqQuarterMetricEnum('nprofit_quarter', '归母净利润-单季', from_name='nprofit')
nprofit_ltm = MqQuarterMetricEnum('nprofit_ltm', '归母净利润-LTM', from_name='nprofit_quarter')
dprofit_quarter = MqQuarterMetricEnum('dprofit_quarter', '归母扣非净利润-单季', from_name='dprofit')
dprofit_ltm = MqQuarterMetricEnum('dprofit_ltm', '归母扣非净利润-LTM', from_name='dprofit_quarter')

cal_quarter_list = [revenue_quarter, nprofit_quarter, dprofit_quarter]
cal_ltm_list = [revenue_ltm, nprofit_ltm, dprofit_ltm, dividend_ltm]

# avg
nassets_ltm_avg = MqQuarterMetricEnum('nassets_ltm_avg', '净资产-LTM平均', from_name='nassets')
total_assets_ltm_avg = MqQuarterMetricEnum('total_assets_ltm_avg', '总资产-LTM平均', from_name='total_assets')
cal_avg_list = [nassets_ltm_avg, total_assets_ltm_avg]

# du pont
roe = MqQuarterMetricEnum('roe', '净资产收益率')
dprofit_margin = MqQuarterMetricEnum('dprofit_margin', '净利率', is_percent=True)
turnover_rate = MqQuarterMetricEnum('turnover_rate', '周转率', is_percent=True)
equity_multiplier = MqQuarterMetricEnum('equity_multiplier', '权益乘数', is_percent=True)

# risk
receive_risk = MqQuarterMetricEnum('receive_risk', '应收风险', is_percent=True)
liquidity_risk = MqQuarterMetricEnum('liquidity_risk', '流动性风险', is_percent=True)
intangible_risk = MqQuarterMetricEnum('intangible_risk', '无形风险', is_percent=True)
cash_debt_rate = MqQuarterMetricEnum('cash_debt_rate', '存贷比', is_percent=True)

risk_point = MqQuarterMetricEnum('risk_point', '风险点数', is_percent=True)

# fill
fill_dividend = MqQuarterMetricEnum('dividend', '分红总额', from_name='')
fill_dprofit = MqQuarterMetricEnum('dprofit', '归母扣非净利润', from_name='nprofit')
fill_after_copy_fail_list = [fill_dividend, fill_dprofit]

# fcf
total_receivable = MqQuarterMetricEnum('total_receivable', '应收款项总和')
total_payable = MqQuarterMetricEnum('total_payable', '应付款项总和')
fcf = MqQuarterMetricEnum('fcf', '自由现金流')

fcf_quarter = MqQuarterMetricEnum('fcf_quarter', '自由现金流-单季', from_name='fcf')
fcf_ltm = MqQuarterMetricEnum('fcf_ltm', '自由现金流-LTM', from_name='fcf')

complex_quarter_list = []
complex_ltm_list = []

all_indicators_list = extract_from_income_list + extract_from_bs_list + extract_from_cf_list + extract_from_fi_list + \
                      extract_from_forecast_list + cal_quarter_list + cal_ltm_list + cal_avg_list + \
                      [
                          # dividend
                          dividend, dividend_ratio,
                          # du pont
                          roe, dprofit_margin, turnover_rate, equity_multiplier,
                          # risk
                          receive_risk, liquidity_risk, intangible_risk, cash_debt_rate,
                          risk_point,
                          # fcf
                          total_receivable, total_payable, fcf, fcf_quarter, fcf_ltm
                      ]

all_indicators_map = {}
for i in all_indicators_list:  # type: MqQuarterMetricEnum
    all_indicators_map[i.name] = i


def is_percent_indicator(name: str) -> bool:
    i = all_indicators_map[name]
    return i is not None and i.is_percent


def find_by_name(name: str) -> MqQuarterMetricEnum:
    """
    根据指标名称返回定义
    :param name: 名称
    :return:
    """
    return all_indicators_map[name] if name in all_indicators_map else None
