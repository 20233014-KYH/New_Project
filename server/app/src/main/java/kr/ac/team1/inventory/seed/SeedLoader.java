package kr.ac.team1.inventory.seed;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import kr.ac.team1.inventory.domain.Category;
import kr.ac.team1.inventory.domain.TestedTool;
import kr.ac.team1.inventory.domain.Tool;
import kr.ac.team1.inventory.domain.ToolPair;
import kr.ac.team1.inventory.repo.CategoryRepository;
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
    private final CategoryRepository categories;
    private final ToolRepository tools;
    private final ToolPairRepository pairs;
    private final TestedToolRepository tested;

    public SeedLoader(ObjectMapper mapper, CategoryRepository categories, ToolRepository tools,
                      ToolPairRepository pairs, TestedToolRepository tested) {
        this.mapper = mapper;
        this.categories = categories;
        this.tools = tools;
        this.pairs = pairs;
        this.tested = tested;
    }

    @Override
    @Transactional
    public void run(ApplicationArguments args) throws IOException {
        if (tools.count() > 0) {
            log.info("DB에 데이터가 이미 있어 처음 데이터 넣기를 건너뜀 (도구 {}개)", tools.count());
            return;
        }
        JsonNode cats = read("categories.json");
        for (JsonNode c : cats.path("categories")) {
            categories.save(new Category(c.path("id").asInt(), text(c, "name"), text(c, "desc"), text(c, "when")));
        }

        JsonNode desc = read("desc_en.json").path("desc");
        JsonNode cards = read("cards_ko.json").path("cards");
        int order = 0;
        for (JsonNode e : read("entries.json").path("entries")) {
            String id = text(e, "id");
            JsonNode auto = e.path("auto");
            String pushed = text(auto, "pushed_at");
            JsonNode card = cards.path(id);
            tools.save(new Tool(id, text(e, "name"), text(e, "repo"), e.path("category").asInt(),
                    text(desc, id), text(card, "summary_ko"), text(card, "when_ko"),
                    text(e, "version"), text(auto, "license"),
                    auto.hasNonNull("stars") ? auto.path("stars").asLong() : null,
                    pushed != null && pushed.length() >= 10 ? pushed.substring(0, 10) : pushed,
                    e.hasNonNull("always_on_tokens_est") ? e.path("always_on_tokens_est").asInt() : null,
                    e.hasNonNull("scope") ? mapper.writeValueAsString(e.path("scope")) : null,
                    text(e, "token_note"), text(e, "checked_at"), order++));
        }

        for (JsonNode p : read("compat.json").path("pairs")) {
            Set<String> sources = new LinkedHashSet<>();
            for (JsonNode ev : p.path("evidence")) {
                String s = text(ev, "source");
                if (s != null && !s.isBlank()) {
                    sources.add(s);
                }
            }
            String review = text(p, "review_state");
            pairs.save(new ToolPair(text(p, "a"), text(p, "b"), text(p, "relation"),
                    review != null ? review : "ai_estimate", text(p, "reason_ko"),
                    mapper.writeValueAsString(new ArrayList<>(sources)), text(p, "judged_at")));
        }

        int i = 0;
        for (JsonNode t : read("tested.json")) {
            tested.save(new TestedTool(text(t, "tool"), text(t, "effect"), text(t, "caution"),
                    text(t, "caution_work"), text(t, "caution_shell"), text(t, "date"), i++));
        }
        log.info("처음 데이터 넣기 끝: 분야 {}개, 도구 {}개, 판정 {}쌍, 시험한 도구 {}개",
                categories.count(), tools.count(), pairs.count(), tested.count());
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
