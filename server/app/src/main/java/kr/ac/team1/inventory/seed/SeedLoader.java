package kr.ac.team1.inventory.seed;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import kr.ac.team1.inventory.domain.Category;
import kr.ac.team1.inventory.domain.SituationGoal;
import kr.ac.team1.inventory.domain.SituationPick;
import kr.ac.team1.inventory.domain.SituationRule;
import kr.ac.team1.inventory.domain.TestedTool;
import kr.ac.team1.inventory.domain.Tool;
import kr.ac.team1.inventory.domain.ToolPair;
import kr.ac.team1.inventory.repo.CategoryRepository;
import kr.ac.team1.inventory.repo.SituationGoalRepository;
import kr.ac.team1.inventory.repo.SituationPickRepository;
import kr.ac.team1.inventory.repo.SituationRuleRepository;
import kr.ac.team1.inventory.repo.TestedToolRepository;
import kr.ac.team1.inventory.repo.ToolPairRepository;
import kr.ac.team1.inventory.repo.ToolRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

/**
 * 서버를 켤 때 DB가 비어 있으면 JSON 파일(분야·도구·판정·시험 결과)을 한 번 넣는다.
 * 파일은 build.gradle이 server/sample-data/ 와 web/app/src/data/ 에서 복사해 온다(seed/).
 */
@Component
public class SeedLoader implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(SeedLoader.class);

    private final ObjectMapper mapper;

    @jakarta.persistence.PersistenceContext
    private jakarta.persistence.EntityManager em;
    private final CategoryRepository categories;
    private final ToolRepository tools;
    private final ToolPairRepository pairs;
    private final TestedToolRepository tested;
    private final SituationRuleRepository rules;
    private final SituationPickRepository picks;
    private final SituationGoalRepository goals;

    public SeedLoader(ObjectMapper mapper, CategoryRepository categories, ToolRepository tools,
                      ToolPairRepository pairs, TestedToolRepository tested, SituationRuleRepository rules,
                      SituationPickRepository picks, SituationGoalRepository goals) {
        this.mapper = mapper;
        this.categories = categories;
        this.tools = tools;
        this.pairs = pairs;
        this.tested = tested;
        this.rules = rules;
        this.picks = picks;
        this.goals = goals;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)   // 파일을 읽다 실패하면 지운 것까지 모두 되돌림
    public void run(ApplicationArguments args) throws IOException {
        // 파일에서만 오는 데이터는 켤 때마다 파일 내용으로 새로 맞춘다.
        // (MySQL처럼 데이터가 남는 DB에서도 새 규칙·고르기·토큰 숫자·판정이 반영되게. 서버 AI가 채운 판정은 남긴다)
        rules.deleteAllInBatch();
        picks.deleteAllInBatch();
        goals.deleteAllInBatch();
        tested.deleteAllInBatch();
        em.flush();
        em.clear();   // 지운 줄이 메모리에 남아 있다가 다시 고쳐지지 않게 비운다
        loadSituationRules();
        loadSituationPicks();
        for (List<String> c : readCsv("seed/situation_goals.csv")) {
            goals.save(new SituationGoal(c.get(0), c.get(1), c.get(2), c.get(3), (int) goals.count()));
        }
        log.info("목적 {}개 넣음", goals.count());
        JsonNode cats = read("categories.json");
        Set<Integer> catIds = new java.util.HashSet<>();
        for (JsonNode c : cats.path("categories")) {
            categories.save(new Category(c.path("id").asInt(), text(c, "name"), text(c, "desc"), text(c, "when")));
            catIds.add(c.path("id").asInt());
        }
        categories.findAll().stream().filter(c -> !catIds.contains(c.getId())).forEach(categories::delete);

        JsonNode desc = read("desc_en.json").path("desc");
        JsonNode cards = read("cards_ko.json").path("cards");
        int order = 0;
        Set<String> toolIds = new java.util.HashSet<>();
        for (JsonNode e : read("entries.json").path("entries")) {
            String id = text(e, "id");
            toolIds.add(id);
            JsonNode auto = e.path("auto");
            String pushed = text(auto, "pushed_at");
            JsonNode card = cards.path(id);
            Tool tool = new Tool(id, text(e, "name"), text(e, "repo"), e.path("category").asInt(),
                    text(desc, id), text(card, "summary_ko"), text(card, "when_ko"),
                    text(e, "version"), text(auto, "license"),
                    auto.hasNonNull("stars") ? auto.path("stars").asLong() : null,
                    pushed != null && pushed.length() >= 10 ? pushed.substring(0, 10) : pushed,
                    e.hasNonNull("always_on_tokens_est") ? e.path("always_on_tokens_est").asInt() : null,
                    e.hasNonNull("scope") ? mapper.writeValueAsString(e.path("scope")) : null,
                    text(e, "token_note"), text(e, "checked_at"), order++);
            tool.setLatest(text(auto, "latest_release"), text(auto, "refreshed_at"));
            tools.save(tool);   // 같은 id가 있으면 새 값으로 덮어씀
        }

        // 파일에서 빠진 도구와, 그 도구가 들어간 판정은 지운다
        tools.findAll().stream().filter(t -> !toolIds.contains(t.getId())).forEach(tools::delete);
        java.util.Map<String, ToolPair> existing = new java.util.HashMap<>();
        for (ToolPair p : pairs.findAll()) {
            if (!toolIds.contains(p.getA()) || !toolIds.contains(p.getB())) {
                pairs.delete(p);
            } else {
                existing.put(p.getPairKey(), p);
            }
        }
        for (JsonNode p : read("compat.json").path("pairs")) {
            if (!toolIds.contains(text(p, "a")) || !toolIds.contains(text(p, "b"))) {
                continue;   // 카탈로그에서 빠진 도구의 판정은 넣지 않는다
            }
            Set<String> sources = new LinkedHashSet<>();
            for (JsonNode ev : p.path("evidence")) {
                String s = text(ev, "source");
                if (s != null && !s.isBlank()) {
                    sources.add(s);
                }
            }
            String review = text(p, "review_state");
            ToolPair fresh = new ToolPair(text(p, "a"), text(p, "b"), text(p, "relation"),
                    review != null ? review : "ai_estimate", text(p, "reason_ko"),
                    mapper.writeValueAsString(new ArrayList<>(sources)), text(p, "judged_at"),
                    p.path("same_role").isBoolean() && p.path("same_role").asBoolean());
            ToolPair old = existing.get(fresh.getPairKey());
            if (old != null) {
                old.updateFrom(fresh);   // 같은 쌍은 내용만 새로(지웠다 다시 넣으면 같은 키가 겹쳐 실패할 수 있음)
            } else {
                pairs.save(fresh);
            }
        }

        int i = 0;
        for (JsonNode t : read("tested.json")) {
            tested.save(new TestedTool(text(t, "tool"), text(t, "effect"), text(t, "caution"),
                    text(t, "caution_work"), text(t, "caution_shell"), text(t, "date"), i++));
        }
        log.info("파일 데이터 맞추기 끝: 분야 {}개, 도구 {}개, 판정 {}쌍, 시험한 도구 {}개",
                categories.count(), tools.count(), pairs.count(), tested.count());
    }

    /** situation_rules.csv → 규칙 표. 첫 줄은 칸 이름. 따옴표로 감싼 칸(쉼표 포함)도 읽는다. */
    private void loadSituationRules() throws IOException {
        String csv;
        try (InputStream in = new ClassPathResource("seed/situation_rules.csv").getInputStream()) {
            csv = new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8).replace("﻿", "");
        }
        List<String> lines = csv.lines().filter(l -> !l.isBlank()).toList();
        for (int i = 1; i < lines.size(); i++) {
            List<String> c = splitCsv(lines.get(i));
            String resultType = c.size() > 11 && !c.get(11).isBlank() ? c.get(11) : "추가";
            String display = c.size() > 13 ? c.get(13) : "";
            if (SituationRule.hidden(c.get(8), display)) {
                continue;   // 근거가 제작자 설명뿐이거나 '화면에 안 올림'
            }
            rules.save(new SituationRule(c.get(0), Integer.parseInt(c.get(1)), c.get(2), c.get(3), c.get(4), c.get(5),
                    c.get(6), c.get(7), c.get(8), c.get(9), c.get(10), i, resultType, display));
        }
        log.info("상황별 추천 규칙 {}개 넣음", rules.count());
    }

    /** situation_priority.csv → 상황 + 중요한 것 → 고를 도구. 첫 줄은 칸 이름. */
    private void loadSituationPicks() throws IOException {
        String csv;
        try (InputStream in = new ClassPathResource("seed/situation_priority.csv").getInputStream()) {
            csv = new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8).replace("﻿", "");
        }
        List<String> lines = csv.lines().filter(l -> !l.isBlank()).toList();
        for (int i = 1; i < lines.size(); i++) {
            List<String> c = splitCsv(lines.get(i));
            picks.save(new SituationPick(c.get(0), c.get(1), c.get(2), c.get(3)));
        }
        log.info("상황별 고르기 규칙 {}개 넣음", picks.count());
    }

    /** CSV 파일을 줄마다 칸 목록으로(첫 줄 칸 이름은 뺌) */
    private List<List<String>> readCsv(String path) throws IOException {
        String csv;
        try (InputStream in = new ClassPathResource(path).getInputStream()) {
            csv = new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8).replace("﻿", "");
        }
        return csv.lines().filter(l -> !l.isBlank()).skip(1).map(SeedLoader::splitCsv).toList();
    }

    static List<String> splitCsv(String line) {
        List<String> out = new ArrayList<>();
        StringBuilder cur = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); i++) {
            char ch = line.charAt(i);
            if (quoted) {
                if (ch == '"' && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    cur.append('"');
                    i++;
                } else if (ch == '"') {
                    quoted = false;
                } else {
                    cur.append(ch);
                }
            } else if (ch == '"') {
                quoted = true;
            } else if (ch == ',') {
                out.add(cur.toString());
                cur.setLength(0);
            } else {
                cur.append(ch);
            }
        }
        out.add(cur.toString());
        return out;
    }

    private JsonNode read(String name) throws IOException {
        try (InputStream in = new ClassPathResource("seed/" + name).getInputStream()) {
            return mapper.readTree(in);
        }
    }

    /** 값이 없거나 null이면 null, 있으면 문자열 */
    static String text(JsonNode node, String field) {
        JsonNode v = node.path(field);
        return v.isMissingNode() || v.isNull() ? null : v.asString();
    }

    static List<String> list(JsonNode arr) {
        List<String> out = new ArrayList<>();
        arr.forEach(n -> out.add(n.asString()));
        return out;
    }
}
