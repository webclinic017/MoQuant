class MqQuarterIndicator(object):

    def __init__(self, name, explain, is_percent=False, from_name=None):
        self.name = name
        self.from_name = name if from_name is None else from_name
        self.explain = explain
        self.is_percent = is_percent


# income
revenue = MqQuarterIndicator('revenue', '营业收入')
nprofit = MqQuarterIndicator('nprofit', '归母净利润', from_name='n_income_attr_p')
total_nprofit = MqQuarterIndicator('total_nprofit', '净利润', from_name='n_income')

extract_from_income_list = [revenue, nprofit, total_nprofit]

# balance sheet
total_share = MqQuarterIndicator('total_share', '总股本')
notes_receiv = MqQuarterIndicator('notes_receiv', '应收票据')
accounts_receiv = MqQuarterIndicator('accounts_receiv', '应收账款')
oth_receiv = MqQuarterIndicator('oth_receiv', '其他应收款')
lt_rec = MqQuarterIndicator('lt_rec', '长期应收款')
total_cur_liab = MqQuarterIndicator('total_cur_liab', '流动负债合计')
total_cur_assets = MqQuarterIndicator('total_cur_assets', '流动资产合计')
goodwill = MqQuarterIndicator('goodwill', '商誉')
r_and_d = MqQuarterIndicator('r_and_d', '研发支出')
intan_assets = MqQuarterIndicator('intan_assets', '无形资产')
nassets = MqQuarterIndicator('nassets', '净资产', from_name='total_hldr_eqy_exc_min_int')
total_assets = MqQuarterIndicator('total_assets', '总资产')
oth_eqt_tools_p_shr = MqQuarterIndicator('oth_eqt_tools_p_shr', '优先股/永续债')
money_cap = MqQuarterIndicator('money_cap', '货币资金')
oth_cur_assets = MqQuarterIndicator('oth_cur_assets', '其他流动资产')
lt_borr = MqQuarterIndicator('lt_borr', '长期借款')
st_borr = MqQuarterIndicator('st_borr', '短期借款')

extract_from_bs_list = [total_share, notes_receiv, accounts_receiv, oth_receiv, lt_rec, total_cur_liab,
                        total_cur_assets, goodwill, r_and_d, intan_assets, nassets, total_assets, oth_eqt_tools_p_shr,
                        money_cap, oth_cur_assets, lt_borr, st_borr]

# cash flow
n_cashflow_act = MqQuarterIndicator('n_cashflow_act', '经营活动产生的现金流量净额')

extract_from_cf_list = [n_cashflow_act]

# fina indicator
dprofit = MqQuarterIndicator('dprofit', '归母扣非净利润', from_name='profit_dedt')

extract_from_fi_list = [dprofit]

# forecast
forecast_nprofit = MqQuarterIndicator('nprofit', '归母净利润')
forecast_dprofit = MqQuarterIndicator('dprofit', '归母扣非净利润')

extract_from_forecast_list = [revenue, forecast_nprofit, forecast_dprofit]

# ltm
revenue_quarter = MqQuarterIndicator('revenue_quarter', '营业收入-单季')
revenue_ltm = MqQuarterIndicator('revenue_ltm', '营业收入-LTM')
nprofit_quarter = MqQuarterIndicator('nprofit_quarter', '归母净利润-单季')
nprofit_ltm = MqQuarterIndicator('nprofit_ltm', '归母净利润-LTM')
dprofit_quarter = MqQuarterIndicator('dprofit_quarter', '归母扣非净利润-单季')
dprofit_ltm = MqQuarterIndicator('dprofit_ltm', '归母扣非净利润-LTM')
cal_ltm_list = [revenue, nprofit, dprofit]

# avg
nassets_ltm_avg = MqQuarterIndicator('nassets_ltm_avg', '净资产-LTM平均')
total_assets_ltm_avg = MqQuarterIndicator('total_assets_ltm_avg', '总资产-LTM平均')
cal_avg_list = [nassets, total_assets]

# du pont
roe = MqQuarterIndicator('roe', '净资产收益率')
dprofit_margin = MqQuarterIndicator('dprofit_margin', '净利率', is_percent=True)
turnover_rate = MqQuarterIndicator('turnover_rate', '周转率', is_percent=True)
equity_multiplier = MqQuarterIndicator('equity_multiplier', '权益乘数', is_percent=True)

# risk
receive_risk = MqQuarterIndicator('receive_risk', '应收风险', is_percent=True)
liquidity_risk = MqQuarterIndicator('liquidity_risk', '流动性风险', is_percent=True)
intangible_risk = MqQuarterIndicator('intangible_risk', '无形风险', is_percent=True)
cash_debt_rate = MqQuarterIndicator('cash_debt_rate', '存贷比', is_percent=True)

all_indicators_list = [
    # income
    revenue, nprofit, total_nprofit,
    # balance sheet
    total_share, notes_receiv, accounts_receiv, oth_receiv, lt_rec, total_cur_liab,
    total_cur_assets, goodwill, r_and_d, intan_assets, nassets, total_assets, oth_eqt_tools_p_shr,
    money_cap, oth_cur_assets, lt_borr, st_borr,
    # cash flow
    n_cashflow_act,
    # fina
    dprofit,
    # ltm
    revenue_quarter, revenue_ltm, nprofit_quarter, nprofit_ltm, dprofit_quarter, dprofit_ltm,
    # avg
    nassets_ltm_avg, total_assets_ltm_avg,
    # du pont
    roe, dprofit_margin, turnover_rate, equity_multiplier,
    # risk
    receive_risk, liquidity_risk, intangible_risk, cash_debt_rate
]

all_indicators_map = {}
for i in all_indicators_list:  # type: MqQuarterIndicator
    all_indicators_map[i.name] = i


def is_percent_indicator(name: str) -> bool:
    i = all_indicators_map[name]
    return i is not None and i.is_percent
