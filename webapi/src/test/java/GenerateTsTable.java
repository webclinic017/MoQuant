import org.junit.Test;

public class GenerateTsTable {

    @Test
    public void go() {
        String[] fields = {
                "ts_code,str,TS股票代码","trade_date,str,交易日期","close,float,当日收盘价","turnover_rate,float,换手率（%）","turnover_rate_f,float,换手率（自由流通股）","volume_ratio,float,量比","pe,float,市盈率（总市值/净利润）","pe_ttm,float,市盈率（TTM）","pb,float,市净率（总市值/净资产）","ps,float,市销率","ps_ttm,float,市销率（TTM）","dv_ratio,float,股息率 （%）","dv_ttm,float,股息率（TTM）（%）","total_share,float,总股本 （万股）","float_share,float,流通股本 （万股）","free_share,float,自由流通股本 （万）","total_mv,float,总市值 （万元）","circ_mv,float,流通市值（万元）"
        };
        for (String field: fields) {
            String[] splits = field.split(",");
            String fieldName = splits[0];
            String fieldType = null;
            switch (splits[1]) {
                case "str":
                    fieldType = "String(10)";
                    break;
                case "float":
                    fieldType = "DECIMAL(30, 10)";
                    break;
                case "int":
                    fieldType = "INT";
                    break;
            }
            String comment = splits[splits.length - 1];
            System.out.println(String.format("%s = Column('%s', %s, comment='%s')", fieldName, fieldName, fieldType, comment));
        }
    }
}
