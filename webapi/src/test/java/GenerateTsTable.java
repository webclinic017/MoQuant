import org.junit.Test;

public class GenerateTsTable {

    @Test
    public void go() {
        String[] fields = {
				"ts_code,str,Y,TS代码","end_date,str,Y,分红年度","ann_date,str,Y,预案公告日","div_proc,str,Y,实施进度","stk_div,float,Y,每股送转","stk_bo_rate,float,Y,每股送股比例","stk_co_rate,float,Y,每股转增比例","cash_div,float,Y,每股分红（税后）","cash_div_tax,float,Y,每股分红（税前）","record_date,str,Y,股权登记日","ex_date,str,Y,除权除息日","pay_date,str,Y,派息日","div_listdate,str,Y,红股上市日","imp_ann_date,str,Y,实施公告日","base_date,str,N,基准日","base_share,float,N,基准股本（万）"
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
