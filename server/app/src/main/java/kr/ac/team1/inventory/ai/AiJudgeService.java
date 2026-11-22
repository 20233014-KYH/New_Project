package kr.ac.team1.inventory.ai;

import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.core.JsonValue;
import com.anthropic.models.messages.MessageCreateParams;
import com.anthropic.models.messages.StructuredMessageCreateParams;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import kr.ac.team1.inventory.domain.PairKeys;
import kr.ac.team1.inventory.domain.Tool;
import kr.ac.team1.inventory.domain.ToolPair;
import kr.ac.team1.inventory.repo.ToolPairRepository;
import kr.ac.team1.inventory.repo.ToolRepository;
import kr.ac.team1.inventory.service.OverlapCriteria;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 판정이 빈 도구 쌍을 서버 AI(Claude)가 채운다. 새 도구를 카탈로그에 넣었을 때 쓰려고 만든 자리.
 * - 지시문은 미리 판정할 때 쓴 judgment/2026-11-21-cross-ai/판정지시문.md를 그대로 쓴다(기준을 같게).
 * - 꺼짐이 기본: 환경 변수 ANTHROPIC_API_KEY가 없으면 호출하지 않는다(키를 파일에 쓰지 않음).
 * - 한 번에 limit쌍까지만(요금 안전장치). 서버 AI는 한 번만 판정하므로 '교차 검수 전'으로 표시한다.
 */
@Service
public class AiJudgeService {

    static final String MODEL = "claude-opus-5-5";
    static final Set<String> RELATIONS = Set.of("overlap", "situational", "complement", "none");

    /** 구조화 출력 모양(판정지시문의 출력 형식과 같음) */
    public record Judgment(String a, String b, String relation, String confidence, String reason_ko) {
    }

    public record Judgments(List<Judgment> pairs) {
    }

    /** 실행 결과: 판정이 빈 쌍 수, 이번에 판정해 저장한 쌍 */
    public record Result(int missing, int judged, List<Judgment> pairs) {
    }

    private final ToolRepository tools;
    private final ToolPairRepository pairs;
    private final String apiKey;
    private final OverlapCriteria criteria;

    public AiJudgeService(ToolRepository tools, ToolPairRepository pairs, @Value("${ANTHROPIC_API_KEY:}") String apiKey,
                          OverlapCriteria criteria) {
        this.criteria = criteria;
        this.tools = tools;
        this.pairs = pairs;
        this.apiKey = apiKey;
    }

    public boolean enabled() {
        return apiKey != null && !apiKey.isBlank();
    }

    /** 카탈로그 도구끼리 판정이 없는 쌍 */
    public List<String[]> missingPairs() {
        List<Tool> all = tools.findAll().stream().sorted(Comparator.comparing(Tool::getPosition)).toList();
        Set<String> have = pairs.findAll().stream().map(ToolPair::getPairKey).collect(Collectors.toSet());
        List<String[]> out = new ArrayList<>();
        for (int i = 0; i < all.size(); i++) {
            for (int j = i + 1; j < all.size(); j++) {
                if (!have.contains(PairKeys.of(all.get(i).getId(), all.get(j).getId()))) {
                    out.add(new String[] {all.get(i).getId(), all.get(j).getId()});
                }
            }
        }
        return out;
    }

    @Transactional
    public Result judgeMissing(int limit) {
        List<String[]> missing = missingPairs();
        if (missing.isEmpty()) {
            return new Result(0, 0, List.of());
        }
        if (!enabled()) {
            throw new AiDisabledException("서버 AI 판정이 꺼져 있어요(ANTHROPIC_API_KEY 없음). 판정이 빈 쌍 " + missing.size() + "개");
        }
        List<String[]> batch = missing.subList(0, Math.min(Math.max(limit, 1), missing.size()));
        Map<String, Tool> byId = tools.findAll().stream().collect(Collectors.toMap(Tool::getId, Function.identity()));
        List<Judgment> got = ask(prompt(batch, byId));
        String today = LocalDate.now().toString();
        List<Judgment> saved = new ArrayList<>();
        for (String[] p : batch) {
            Judgment j = got.stream().filter(x -> x.a() != null && x.b() != null
                    && PairKeys.of(x.a(), x.b()).equals(PairKeys.of(p[0], p[1]))).findFirst().orElse(null);
            if (j == null || !RELATIONS.contains(j.relation())) {
                continue;   // 빠지거나 이상한 답은 저장하지 않고 다음 실행에 다시 판정
            }
            String rel = j.relation();
            String reason = "[AI 추정·서버 AI 한 번 판정(교차 검수 전) " + today + "] " + j.reason_ko();
            boolean sameRole = "overlap".equals(rel);
            int min = criteria.minTokens();
            if (sameRole && !(tokens(byId.get(p[0])) >= min && tokens(byId.get(p[1])) >= min)) {
                rel = "situational";   // 미리 한 판정과 같은 겹침 기준(compat.json criteria)
                reason += " [겹침 기준 적용: 한쪽이 처음 읽는 양 " + String.format(java.util.Locale.US, "%,d", min)
                        + "토큰 미만이거나 아직 안 재서 상황따라로 낮춤(같은 일을 하는 도구라는 사실은 카드에 표시)]";
            }
            pairs.save(new ToolPair(p[0], p[1], rel, "ai_estimate", reason,
                    "[\"judgment/2026-11-21-cross-ai/판정지시문.md (서버 AI " + MODEL + ")\"]", today, sameRole));
            saved.add(new Judgment(p[0], p[1], rel, j.confidence(), reason));
        }
        return new Result(missing.size(), saved.size(), saved);
    }

    private static int tokens(Tool t) {
        return t == null || t.getTokens() == null ? 0 : t.getTokens();
    }

    String prompt(List<String[]> batch, Map<String, Tool> byId) {
        StringBuilder sb = new StringBuilder(guide()).append("\n\n## 도구 정보\n");
        batch.stream().flatMap(p -> Stream.of(p[0], p[1])).distinct().map(byId::get).forEach(t -> sb
                .append("- ").append(t.getId()).append(" (분야 ").append(t.getCategory()).append(")")
                .append(" 설명: ").append(t.getDescEn())
                .append(t.getSummaryKo() == null ? "" : " / 한국어 소개: " + t.getSummaryKo())
                .append(t.getWhenKo() == null ? "" : " / 이럴 때: " + t.getWhenKo())
                .append(t.getScopeJson() == null ? "" : " / 역할 범위: " + t.getScopeJson())
                .append(" / 처음 읽는 양: ").append(t.getTokens() == null ? "모름" : t.getTokens() + "토큰").append("\n"));
        sb.append("\n## 판정할 쌍 (").append(batch.size()).append("개, 전부)\n");
        batch.forEach(p -> sb.append("- ").append(p[0]).append(" / ").append(p[1]).append("\n"));
        return sb.toString();
    }

    private static String guide() {
        try (InputStream in = new ClassPathResource("seed/판정지시문.md").getInputStream()) {
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("판정 지시문을 못 읽었어요", e);
        }
    }

    /** Claude에 묻고 구조화 출력(Judgments)으로 받는다 */
    List<Judgment> ask(String prompt) {
        AnthropicClient client = AnthropicOkHttpClient.builder().apiKey(apiKey).build();
        StructuredMessageCreateParams<Judgments> params = MessageCreateParams.builder()
                .model(MODEL)
                .maxTokens(16000L)
                // 거절(refusal)되면 서버가 다른 모델로 이어서 답하게 하는 옵션(server-side fallback)
                .putAdditionalHeader("anthropic-beta", "server-side-fallback-2026-07-01")
                .putAdditionalBodyProperty("fallbacks", JsonValue.from("default"))
                .outputConfig(Judgments.class)
                .addUserMessage(prompt)
                .build();
        return client.messages().create(params).content().stream()
                .flatMap(cb -> cb.text().stream())
                .flatMap(t -> t.text().pairs().stream())
                .toList();
    }
}
