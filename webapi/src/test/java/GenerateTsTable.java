import org.junit.Test;

public class GenerateTsTable {

    @Test
    public void go() {
        String[] fields = {
				"trade_date,str,Y,交易日期","ts_code,str,Y,TS股票代码","up_limit,float,Y,涨停价","down_limit,float,Y,跌停价"
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
