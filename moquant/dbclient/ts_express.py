from sqlalchemy import Column, BIGINT, Index, String, DECIMAL, INT

from moquant.dbclient.base import Base


class StockExpress(Base):
    __tablename__ = 'ts_express'
    __table_args__ = (
        Index('code_date', 'ts_code', 'ann_date'),
        Index('code_period', 'ts_code', 'end_date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}
    )

    id = Column('id', BIGINT, primary_key=True, comment='id', autoincrement=True)
    ts_code = Column('ts_code', String(10), comment='TS股票代码')
    ann_date = Column('ann_date', String(10), comment='公告日期')
    end_date = Column('end_date', String(10), comment='报告期')
    revenue = Column('revenue', DECIMAL(30, 10), comment='营业收入(元)')
    operate_profit = Column('operate_profit', DECIMAL(30, 10), comment='营业利润(元)')
    total_profit = Column('total_profit', DECIMAL(30, 10), comment='利润总额(元)')
    n_income = Column('n_income', DECIMAL(30, 10), comment='归母净利润(元)')
    total_assets = Column('total_assets', DECIMAL(30, 10), comment='总资产(元)')
    total_hldr_eqy_exc_min_int = Column('total_hldr_eqy_exc_min_int', DECIMAL(30, 10), comment='股东权益合计(不含少数股东权益)(元)')
    diluted_eps = Column('diluted_eps', DECIMAL(30, 10), comment='每股收益(摊薄)(元)')
    diluted_roe = Column('diluted_roe', DECIMAL(30, 10), comment='净资产收益率(摊薄)(%)')
    yoy_net_profit = Column('yoy_net_profit', DECIMAL(30, 10), comment='去年同期修正后净利润')
    bps = Column('bps', DECIMAL(30, 10), comment='每股净资产')
    yoy_sales = Column('yoy_sales', DECIMAL(30, 10), comment='同比增长率:营业收入')
    yoy_op = Column('yoy_op', DECIMAL(30, 10), comment='同比增长率:营业利润')
    yoy_tp = Column('yoy_tp', DECIMAL(30, 10), comment='同比增长率:利润总额')
    yoy_dedu_np = Column('yoy_dedu_np', DECIMAL(30, 10), comment='同比增长率:归属母公司股东的净利润')
    yoy_eps = Column('yoy_eps', DECIMAL(30, 10), comment='同比增长率:基本每股收益')
    yoy_roe = Column('yoy_roe', DECIMAL(30, 10), comment='同比增减:加权平均净资产收益率')
    growth_assets = Column('growth_assets', DECIMAL(30, 10), comment='比年初增长率:总资产')
    yoy_equity = Column('yoy_equity', DECIMAL(30, 10), comment='比年初增长率:归属母公司的股东权益')
    growth_bps = Column('growth_bps', DECIMAL(30, 10), comment='比年初增长率:归属于母公司股东的每股净资产')
    or_last_year = Column('or_last_year', DECIMAL(30, 10), comment='去年同期营业收入')
    op_last_year = Column('op_last_year', DECIMAL(30, 10), comment='去年同期营业利润')
    tp_last_year = Column('tp_last_year', DECIMAL(30, 10), comment='去年同期利润总额')
    np_last_year = Column('np_last_year', DECIMAL(30, 10), comment='去年同期净利润')
    eps_last_year = Column('eps_last_year', DECIMAL(30, 10), comment='去年同期每股收益')
    open_net_assets = Column('open_net_assets', DECIMAL(30, 10), comment='期初净资产')
    open_bps = Column('open_bps', DECIMAL(30, 10), comment='期初每股净资产')
    perf_summary = Column('perf_summary', String(5000), comment='业绩简要说明')
    is_audit = Column('is_audit', INT, comment='是否审计： 1是 0否')
    remark = Column('remark', String(5000), comment='备注')

