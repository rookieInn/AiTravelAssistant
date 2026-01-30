import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/**
 * 需求：同一“公司 + 人”在 PERSON 里出现多次时，将其多个 POSITION 合并为一条，
 * 并用中文逗号“，”连接（去重且保留首次出现顺序）。
 *
 * 适用数据结构：data.ENT_INFO.PERSON（每项包含 ENTNAME / PERNAME / POSITION 等）
 */
public class MergePositionsFastjson {

    /**
     * 合并 data.ENT_INFO.PERSON：
     * - key: ENTNAME + "\u0000" + PERNAME
     * - POSITION: 去重后用中文逗号拼接
     * - 其它字段：默认保留该人首次出现的那条记录
     */
    public static String mergePersonPositions(String rawJson) {
        JSONObject root = JSON.parseObject(rawJson);
        JSONObject data = root.getJSONObject("data");
        if (data == null) return rawJson;

        JSONObject entInfo = data.getJSONObject("ENT_INFO");
        if (entInfo == null) return rawJson;

        JSONArray person = entInfo.getJSONArray("PERSON");
        if (person == null || person.isEmpty()) return rawJson;

        // 维持输入顺序：首次出现的 (ENTNAME, PERNAME) 决定输出顺序
        Map<String, JSONObject> baseRowByKey = new LinkedHashMap<>();
        Map<String, Set<String>> positionsByKey = new LinkedHashMap<>();

        for (int i = 0; i < person.size(); i++) {
            JSONObject row = person.getJSONObject(i);
            if (row == null) continue;

            String entName = trimToEmpty(row.getString("ENTNAME"));
            String perName = trimToEmpty(row.getString("PERNAME"));
            String key = entName + "\u0000" + perName;

            baseRowByKey.computeIfAbsent(key, k -> (JSONObject) row.clone());
            positionsByKey.computeIfAbsent(key, k -> new LinkedHashSet<>());

            String position = trimToEmpty(row.getString("POSITION"));
            if (!position.isEmpty()) {
                positionsByKey.get(key).add(position);
            }
        }

        JSONArray merged = new JSONArray(baseRowByKey.size());
        for (Map.Entry<String, JSONObject> e : baseRowByKey.entrySet()) {
            String key = e.getKey();
            JSONObject base = e.getValue();

            Set<String> positions = positionsByKey.get(key);
            base.put("POSITION", joinCnComma(positions));
            merged.add(base);
        }

        entInfo.put("PERSON", merged);
        return root.toJSONString();
    }

    private static String joinCnComma(Iterable<String> items) {
        if (items == null) return "";
        StringBuilder sb = new StringBuilder();
        for (String s : items) {
            if (s == null) continue;
            String v = s.trim();
            if (v.isEmpty()) continue;
            if (sb.length() > 0) sb.append('，');
            sb.append(v);
        }
        return sb.toString();
    }

    private static String trimToEmpty(String s) {
        return s == null ? "" : s.trim();
    }

    // 简单演示：把你的 JSON 字符串放到 rawJson 里即可看到 PERSON 合并效果
    public static void main(String[] args) {
        String rawJson = "{\n" +
                "  \"data\": {\n" +
                "    \"ENT_INFO\": {\n" +
                "      \"PERSON\": [\n" +
                "        {\"ENTNAME\":\"北京中数智汇科技股份有限公司\",\"PERNAME\":\"鲍涛\",\"POSITION\":\"副董事长\"},\n" +
                "        {\"ENTNAME\":\"北京中数智汇科技股份有限公司\",\"PERNAME\":\"鲍涛\",\"POSITION\":\"经理\"},\n" +
                "        {\"ENTNAME\":\"北京中数智汇科技股份有限公司\",\"PERNAME\":\"张军\",\"POSITION\":\"董事长\"}\n" +
                "      ]\n" +
                "    }\n" +
                "  }\n" +
                "}";

        String merged = mergePersonPositions(rawJson);
        System.out.println(merged);
    }
}

