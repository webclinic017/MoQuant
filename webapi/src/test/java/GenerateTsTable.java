import org.junit.Test;

public class GenerateTsTable {

    @Test
    public void go() {
        String[] fields = {
				"exchange,str,Y,交易所 SSE上交所 SZSE深交所","cal_date,str,Y,日历日期","is_open,str,Y,是否交易 0休市 1交易","pretrade_date,str,N,上一个交易日"
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
