package kr.ac.team1.inventory.service;

import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import kr.ac.team1.inventory.domain.Tool;
import kr.ac.team1.inventory.domain.ToolPair;
import kr.ac.team1.inventory.domain.SituationPick;
import kr.ac.team1.inventory.domain.SituationRule;
import kr.ac.team1.inventory.dto.Dtos.CategoryDto;
import kr.ac.team1.inventory.dto.Dtos.PickNote;
import kr.ac.team1.inventory.dto.Dtos.ToolSituation;
import kr.ac.team1.inventory.dto.Dtos.ToolDetailDto;
import kr.ac.team1.inventory.dto.Dtos.ToolDto;
import kr.ac.team1.inventory.dto.Dtos.ToolPairDto;
import kr.ac.team1.inventory.repo.CategoryRepository;
import kr.ac.team1.inventory.repo.SituationPickRepository;
import kr.ac.team1.inventory.repo.SituationRuleRepository;
import kr.ac.team1.inventory.repo.ToolPairRepository;
import kr.ac.team1.inventory.repo.ToolRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import tools.jackson.core.type.TypeReference;
import tools.jackson.databind.ObjectMapper;

/** 분야·도구 목록·도구 상세(카드 한 장 + 그 도구와 관련된 판정) */
@Service
@Transactional(readOnly = true)
public class ToolService {

    private final CategoryRepository categories;
    private final ToolRepository tools;
    private final ToolPairRepository pairs;
    private final ObjectMapper mapper;
    private final SituationRuleRepository rules;
    private final SituationPickRepository picks;

    public ToolService(CategoryRepository categories, ToolRepository tools, ToolPairRepository pairs, ObjectMapper mapper,
                       SituationRuleRepository rules, SituationPickRepository picks) {
        this.categories = categories;
        this.tools = tools;
        this.pairs = pairs;
        this.mapper = mapper;
        this.rules = rules;
        this.picks = picks;
    }

    public List<CategoryDto> categories() {
        return categories.findAll().stream()
                .sorted(Comparator.comparing(c -> c.getId()))
                .map(c -> new CategoryDto(c.getId(), c.getName(), c.getDescription(), c.getWhen()))
                .toList();
    }

    /** 도구 목록: 분야로 거르고, 검색어는 이름·영어 설명·한국어 소개에서 찾는다 */
    public List<ToolDto> list(Integer category, String q) {
        String lq = q == null ? "" : q.trim().toLowerCase(Locale.ROOT);
        return ordered().stream()
                .filter(t -> category == null || category.equals(t.getCategory()))
                .filter(t -> lq.isEmpty() || contains(t.getName(), lq) || contains(t.getDescEn(), lq) || contains(t.getSummaryKo(), lq))
                .map(this::toDto)
                .toList();
    }

    public ToolDetailDto detail(String id) {
        Tool tool = tools.findById(id).orElseThrow(() -> new NotFoundException("없는 도구예요: " + id));
        List<ToolPairDto> related = pairs.findAll().stream()
                .filter(p -> p.getA().equals(id) || p.getB().equals(id))
                .sorted(Comparator.comparing(ToolPair::getId))
                .map(p -> new ToolPairDto(p.getA(), p.getB(), p.getRelation(), p.getReviewState(), p.getReason(),
                        sources(p), p.getJudgedAt(), p.getA().equals(id) ? p.getB() : p.getA(),
                        Labels.RELATION.get(p.getRelation()), Labels.REVIEW.get(p.getReviewState()), p.isSameRole()))
                .toList();
        return new ToolDetailDto(toDto(tool), related, situations(id), traits(id));
    }

    static List<String> splitTools(String s) {
        return java.util.Arrays.stream(s.split(java.util.regex.Pattern.quote("|"))).map(String::trim).filter(t -> !t.isEmpty()).toList();
    }

    /** 이 도구가 추천 도구로 들어간 상황(규칙 파일 순서)과, 그 상황의 중요한 것별 고르기 */
    List<ToolSituation> situations(String id) {
        java.util.Map<String, String> names = new java.util.HashMap<>();
        tools.findAll().forEach(t -> names.put(t.getId(), t.getName()));
        List<SituationPick> allPicks = picks.findAll();
        return rules.findAll().stream().sorted(Comparator.comparing(SituationRule::getPosition))
                .filter(r -> splitTools(r.getTools()).contains(id))
                .map(r -> new ToolSituation(r.getSituationId(), r.getLabel(), r.getBase(), r.getBetter(), r.getCost(),
                        "tested".equals(r.getEvidenceType()) ? "직접 시험" : "제작자 설명",
                        allPicks.stream().filter(p -> p.getSituationId().equals(r.getSituationId()))
                                .sorted(Comparator.comparing(p -> Labels.PRIORITY_ORDER.indexOf(p.getPriority())))
                                .map(p -> new PickNote(p.getPriority(), Labels.PRIORITY.get(p.getPriority()),
                                        "base".equals(p.getTools()) ? "기본 기능"
                                                : String.join(" 또는 ", splitTools(p.getTools()).stream().map(t -> names.getOrDefault(t, t)).toList()),
                                        p.getReason()))
                                .toList(), r.getResultType()))
                .toList();
    }

    private tools.jackson.databind.JsonNode traitsCache;

    /** 직접 써 본 특징(seed/tool_traits.json, api.js와 같은 파일). 없으면 null */
    tools.jackson.databind.JsonNode traits(String id) {
        if (traitsCache == null) {
            try (java.io.InputStream in = new org.springframework.core.io.ClassPathResource("seed/tool_traits.json").getInputStream()) {
                traitsCache = mapper.readTree(in).path("traits");
            } catch (java.io.IOException e) {
                throw new java.io.UncheckedIOException(e);
            }
        }
        tools.jackson.databind.JsonNode t = traitsCache.get(id);
        return t == null || t.isNull() ? null : t;
    }

    List<Tool> ordered() {
        return tools.findAll().stream().sorted(Comparator.comparing(Tool::getPosition)).toList();
    }

    List<String> sources(ToolPair p) {
        if (p.getSourcesJson() == null) {
            return List.of();
        }
        return mapper.readValue(p.getSourcesJson(), new TypeReference<List<String>>() {
        });
    }

    ToolDto toDto(Tool t) {
        return new ToolDto(t.getId(), t.getName(), t.getRepo(), t.getCategory(), t.getDescEn(), t.getSummaryKo(),
                t.getWhenKo(), t.getVersion(), t.getLicense(), t.getStars(), t.getPushedAt(), t.getTokens(),
                t.getScopeJson() == null ? null : mapper.readTree(t.getScopeJson()), t.getTokenNote(), t.getCheckedAt(),
                t.getLatestRelease(), t.getRefreshedAt());
    }

    private static boolean contains(String s, String lq) {
        return s != null && s.toLowerCase(Locale.ROOT).contains(lq);
    }
}
