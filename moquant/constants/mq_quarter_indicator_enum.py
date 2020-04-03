class MqQuarterIndicator(object):

    def __init__(self, name, explain, from_name = None):
        self.name = name
        self.from_name = name if from_name is None else from_name
        self.explain = explain


# income
revenue = MqQuarterIndicator('revenue', '营业收入')
nprofit = MqQuarterIndicator('nprofit', '归母净利润', 'n_income_attr_p')
total_nprofit = MqQuarterIndicator('total_nprofit', '净利润', 'n_income')

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
nassets = MqQuarterIndicator('nassets', '净资产', 'total_hldr_eqy_exc_min_int')
oth_eqt_tools_p_shr = MqQuarterIndicator('oth_eqt_tools_p_shr', '优先股')
money_cap = MqQuarterIndicator('money_cap', '货币资金')
oth_cur_assets = MqQuarterIndicator('oth_cur_assets', '其他流动资产')
lt_borr = MqQuarterIndicator('lt_borr', '长期借款')
st_borr = MqQuarterIndicator('st_borr', '短期借款')

extract_from_bs_list = [total_share, notes_receiv, accounts_receiv, oth_receiv, lt_rec, total_cur_liab,
                        total_cur_assets, goodwill, r_and_d, intan_assets, nassets, oth_eqt_tools_p_shr,
                        money_cap, oth_cur_assets, lt_borr, st_borr]

# cash flow
n_cashflow_act = MqQuarterIndicator('n_cashflow_act', '经营活动产生的现金流量净额')

extract_from_cf_list = [n_cashflow_act]

# fina indicator
dprofit = MqQuarterIndicator('dprofit', '归母扣非净利润', 'profit_dedt')

extract_from_fi_list = [dprofit]

# forecast
forecast_nprofit = MqQuarterIndicator('nprofit', '归母净利润')
forecast_dprofit = MqQuarterIndicator('dprofit', '归母扣非净利润')

extract_from_forecast_list = [revenue, forecast_nprofit, forecast_dprofit]

# ltm

cal_ltm_list = [revenue, ]