package kr.ac.team1.inventory.service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;
import kr.ac.team1.inventory.domain.PairKeys;
import kr.ac.team1.inventory.domain.TestedTool;
import kr.ac.team1.inventory.domain.Tool;
import kr.ac.team1.inventory.domain.ToolPair;
import kr.ac.team1.inventory.dto.Dtos.AddItem;
import kr.ac.team1.inventory.dto.Dtos.Caution;
import kr.ac.team1.inventory.dto.Dtos.Answers;
import kr.ac.team1.inventory.dto.Dtos.GoalDto;
import kr.ac.team1.inventory.dto.Dtos.GoalPlan;
import kr.ac.team1.inventory.dto.Dtos.JudgeItem;
import kr.ac.team1.inventory.dto.Dtos.PlanItem;
import kr.ac.team1.inventory.dto.Dtos.Pick;
import kr.ac.team1.inventory.dto.Dtos.RecommendResult;
import kr.ac.team1.inventory.dto.Dtos.RemoveItem;
import kr.ac.team1.inventory.dto.Dtos.SituationCard;
import kr.ac.team1.inventory.dto.Dtos.SituationDto;
import kr.ac.team1.inventory.dto.Dtos.ToolRef;
import kr.ac.team1.inventory.domain.SituationGoal;
import kr.ac.team1.inventory.domain.SituationRule;
import kr.ac.team1.inventory.repo.SituationGoalRepository;
import kr.ac.team1.inventory.repo.SituationPickRepository;
import kr.ac.team1.inventory.repo.SituationRuleRepository;
import kr.ac.team1.inventory.repo.TestedToolRepository;
import kr.ac.team1.inventory.repo.ToolPairRepository;
import kr.ac.team1.inventory.repo.ToolRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 도구함 판정과 추천. 화면 로컬 모드(api.js의 judgeLocal·recommendLocal)와 같은 규칙을 서버로 옮겼다.
 * 1) 담은 도구를 둘씩 짝짓는다(겹침은 두 도구 사이의 문제라서).
 * 2) 짝마다 저장된 판정을 찾는다. 없으면 "확인된 정보 없음"(안전하다는 뜻 아님).
 * 3) 겹치는 짝이면 처음 읽는 양이 큰 쪽을 뺄 후보로(임시 규칙), 시험한 도구는 조건을 보고 더하기 후보로.
 */
@Service
@Transactional(readOnly = true)
public class JudgeService {

    /** 한 번에 받을 도구 수 상한(기획안 6-3: 요청당 도구 수 제한) */
    public static final int MAX_TOOLS = 40;

    private final ToolRepository tools;
    private final ToolPairRepository pairs;
    private final TestedToolRepository tested;
    private final SituationRuleRepository rules;
    private final SituationPickRepository picks;
    private final SituationGoalRepository goals;
    private final ToolService toolService;
    private final OverlapCriteria criteria;

    public JudgeService(ToolRepository tools, ToolPairRepository pairs, TestedToolRepository tested, ToolService toolService,
                        SituationRuleRepository rules, SituationPickRepository picks,
                        SituationGoalRepository goals, OverlapCriteria criteria) {
        this.criteria = criteria;
        this.tools = tools;
        this.pairs = pairs;
        this.tested = tested;
        this.rules = rules;
        this.picks = picks;
        this.goals = goals;
        this.toolService = toolService;
    }

    public List<JudgeItem> judge(List<String> rawIds) {
        List<String> ids = clean(rawIds);
        Map<String, Tool> byId = tools.findAllById(ids).stream().collect(Collectors.toMap(Tool::getId, Function.identity()));
        Map<String, ToolPair> pairMap = pairMap();
        List<JudgeItem> out = new ArrayList<>();
        for (int i = 0; i < ids.size(); i++) {
            for (int j = i + 1; j < ids.size(); j++) {
                ToolPair p = pairMap.get(PairKeys.of(ids.get(i), ids.get(j)));
                if (p != null) {
                    out.add(saved(p));
                } else {
                    boolean sameCategory = Objects.equals(byId.get(ids.get(i)).getCategory(), byId.get(ids.get(j)).getCategory());
                    out.add(new JudgeItem(ids.get(i), ids.get(j), "no_info", null, Labels.NO_INFO,
                            sameCategory ? "판정 없음" : "다른 분야", null, null, null));
                }
            }
        }
        return out;
    }

    /** 두 도구의 저장된 판정 하나. 없으면 NotFound → 화면에 "확인된 정보 없음" */
    public JudgeItem judgment(String a, String b) {
        clean(List.of(a, b));
        return saved(pairs.findByPairKey(PairKeys.of(a, b)).orElseThrow(() -> new NotFoundException(Labels.NO_INFO)));
    }

    public RecommendResult recommend(List<String> rawIds, Answers answers) {
        List<String> ids = clean(rawIds);
        Answers ans = answers == null ? new Answers("", "", "", null, null, null) : answers;
        List<JudgeItem> js = judge(ids);
        Map<String, Tool> byId = tools.findAll().stream().collect(Collectors.toMap(Tool::getId, Function.identity()));
        Map<String, ToolPair> pairMap = pairMap();

        // 빼기: 겹치는 짝에서 처음 읽는 양이 큰 쪽(같으면 앞쪽)을 뺄 후보로. 도구 하나는 한 번만.
        List<RemoveItem> remove = new ArrayList<>();
        for (JudgeItem p : js) {
            if (!"overlap".equals(p.relation())) {
                continue;
            }
            Tool a = byId.get(p.a());
            Tool b = byId.get(p.b());
            if (a == null || b == null) {
                continue;
            }
            Tool big = tokens(a) >= tokens(b) ? a : b;
            Tool keep = big == a ? b : a;
            if (remove.stream().noneMatch(r -> r.tool().equals(big.getId()))) {
                remove.add(new RemoveItem(big.getId(), keep.getId(), tokens(big), p.review(), p.reason(), p.sources(), p.judgedAt(), null));
            }
        }

        // 같은 일 묶음(3개 이상): 가장 큰 것을 남겨도 아끼는 양(합 - 최댓값)이 기준 이상이면 하나만 남긴다.
        // 남길 도구 = 아직 안 뺀 것 중 처음 읽는 양이 가장 작은 것(같으면 도구함 앞쪽) — 빼기 규칙과 같은 임시 규칙
        for (List<String> g : roleGroups(ids, pairMap)) {
            int sum = g.stream().mapToInt(id -> tokens(byId.get(id))).sum();
            int max = g.stream().mapToInt(id -> tokens(byId.get(id))).max().orElse(0);
            int saving = sum - max;
            if (saving < criteria.minTokens()) {
                continue;
            }
            List<String> free = g.stream().filter(id -> remove.stream().noneMatch(r -> r.tool().equals(id))).toList();
            if (free.size() < 2) {
                continue;
            }
            String keep = free.get(0);
            for (String id : free) {
                if (tokens(byId.get(id)) < tokens(byId.get(keep))) {
                    keep = id;
                }
            }
            String names = g.stream().map(id -> byId.get(id).getName()).collect(Collectors.joining(", "));
            for (String id : free) {
                if (id.equals(keep)) {
                    continue;
                }
                ToolPair p = pairMap.get(PairKeys.of(id, keep));
                remove.add(new RemoveItem(id, keep, tokens(byId.get(id)), Labels.REVIEW.get(p.getReviewState()),
                        "같은 일을 하는 도구 " + g.size() + "개(" + names + ")를 함께 켰어요. 가장 큰 것을 남겨도 "
                                + comma(saving) + "토큰을 아껴서(기준 " + comma(criteria.minTokens()) + "토큰) 하나만 남기기를 권해요.",
                        toolService.sources(p), p.getJudgedAt(), g));
            }
        }

        // 더하기: 우리가 직접 시험한 도구만. 담은 도구와 겹치면 막고, 판정 없는 짝은 숨기지 않고 unknown에 적는다.
        List<AddItem> add = new ArrayList<>();
        for (TestedTool t : tested.findAll().stream().sorted(Comparator.comparing(TestedTool::getPosition)).toList()) {
            if (ids.contains(t.getTool())) {
                continue;
            }
            List<String> unknown = new ArrayList<>();
            String blocked = null;
            for (String id : ids) {
                ToolPair p = pairMap.get(PairKeys.of(id, t.getTool()));
                if (p == null) {
                    unknown.add(id);
                } else if (blocked == null && "overlap".equals(p.getRelation())) {
                    blocked = id;
                }
            }
            List<String> warnings = new ArrayList<>();
            if (t.getCautionWork() != null && t.getCautionWork().equals(ans.work())) {
                warnings.add(t.getCaution());
            }
            boolean notFit = t.getCautionShell() != null && t.getCautionShell().equals(ans.shell());
            if (notFit) {
                warnings.add(t.getCaution());
            }
            String verdict = blocked != null ? "겹침이 있어 추천하지 않아요"
                    : notFit ? "지금 환경에서는 효과가 없어요" : "조건을 확인하고 더해 보세요";
            add.add(new AddItem(t.getTool(), t.getEffect(), t.getCaution(), warnings, unknown, blocked, verdict, t.getTestedOn()));
        }
        int unknownCount = (int) js.stream().filter(p -> "no_info".equals(p.state())).count();
        return new RecommendResult(js, remove, add, unknownCount, situationCard(ans.situation(), ans.priority(), ids, byId, pairMap),
                goalPlan(ans, ids, byId, pairMap));
    }

    /** 목적 선택지 (CSV 순서) */
    public List<GoalDto> goals() {
        return goals.findAll().stream().sorted(Comparator.comparing(SituationGoal::getPosition))
                .map(g -> new GoalDto(g.getGoalId(), g.getLabel(), g.getDescription())).toList();
    }

    /**
     * 목적 → 상황 여러 개의 카드를 모아 도구함을 바꿀 것을 정한다.
     * 더하기: 중요한 것으로 고른 도구 중 도구함에 없는 것 / 그대로: 고른 도구가 이미 도구함에 있음 /
     * 꺼도 되는 것: 토큰·속도·간단함이 중요한데 시험에서 '기본 기능으로 충분'이었던 상황의 추천 도구가 도구함에 있음.
     * 중요한 것을 안 골랐으면 상황 카드만 준다(고를 근거가 없어서).
     */
    private GoalPlan goalPlan(Answers ans, List<String> ids, Map<String, Tool> byId, Map<String, ToolPair> pairMap) {
        if (ans.goal() == null || ans.goal().isBlank()) {
            return null;
        }
        Map<String, TestedTool> testedMap = tested.findAll().stream().collect(Collectors.toMap(TestedTool::getTool, Function.identity()));
        return goals.findById(ans.goal()).map(g -> {
            List<SituationCard> cards = ToolService.splitTools(g.getSituations()).stream()
                    .map(s -> situationCard(s, ans.priority(), ids, byId, pairMap)).filter(Objects::nonNull).toList();
            Map<String, PlanItem> add = new java.util.LinkedHashMap<>();
            Map<String, PlanItem> off = new java.util.LinkedHashMap<>();
            Map<String, PlanItem> keep = new java.util.LinkedHashMap<>();
            boolean costMatters = ans.priority() != null && List.of("save", "fast", "simple").contains(ans.priority());
            for (SituationCard c : cards) {
                Pick p = c.pick();
                if (p == null) {
                    continue;
                }
                if (p.base()) {
                    if (costMatters) {
                        c.tools().stream().filter(ToolRef::inBox).forEach(t -> merge(off, t, c.label(), p.reason(), List.of()));
                    }
                    continue;
                }
                // '또는'으로 묶인 도구는 하나만: 도구함에 이미 있는 쪽을 그대로, 없으면 첫 번째만 더하기 (api.js goalPlan과 같음)
                List<ToolRef> inBoxPick = p.tools().stream().filter(ToolRef::inBox).toList();
                for (ToolRef t : inBoxPick.isEmpty() ? p.tools().stream().limit(1).toList() : inBoxPick) {
                    if (t.inBox()) {
                        merge(keep, t, c.label(), p.reason(), List.of());
                        continue;
                    }
                    List<String> warnings = new ArrayList<>();
                    t.overlapWith().forEach(o -> warnings.add("도구함의 " + o + "와 겹쳐요"));
                    t.similarTo().forEach(o -> warnings.add("도구함의 " + o + "와 비슷한 역할이에요(상황따라)"));
                    TestedTool tt = testedMap.get(t.id());
                    if (tt != null && ((tt.getCautionWork() != null && tt.getCautionWork().equals(ans.work()))
                            || (tt.getCautionShell() != null && tt.getCautionShell().equals(ans.shell())))) {
                        warnings.add(tt.getCaution());
                    }
                    merge(add, t, c.label(), p.reason(), warnings);
                }
            }
            return new GoalPlan(g.getGoalId(), g.getLabel(), g.getDescription(), List.copyOf(add.values()),
                    List.copyOf(off.values()), List.copyOf(keep.values()), cards);
        }).orElse(null);
    }

    /** 같은 도구가 여러 상황에서 나오면 한 줄로 합치고 상황 이름·이유·주의를 이어 붙인다 */
    private static void merge(Map<String, PlanItem> m, ToolRef t, String situation, String reason, List<String> warnings) {
        PlanItem old = m.get(t.id());
        if (old == null) {
            m.put(t.id(), new PlanItem(t.id(), t.name(), List.of(situation), List.of(reason), List.copyOf(warnings)));
            return;
        }
        List<String> s = new ArrayList<>(old.situations());
        List<String> r = new ArrayList<>(old.reasons());
        s.add(situation);
        r.add(reason);
        List<String> w = new ArrayList<>(old.warnings());
        warnings.stream().filter(x -> !w.contains(x)).forEach(w::add);
        m.put(t.id(), new PlanItem(t.id(), t.name(), s, r, w));
    }

    /** 상황 질문의 선택지 (CSV 순서) */
    public List<SituationDto> situations() {
        return rules.findAll().stream().sorted(Comparator.comparing(SituationRule::getPosition)).filter(r -> !r.isCaution())
                .map(r -> new SituationDto(r.getSituationId(), r.getCategory(), r.getLabel())).toList();
    }

    /** 고른 상황의 3칸 카드. 상황을 안 골랐거나 없는 상황이면 null */
    /** 추천 도구 t와 도구함의 도구 사이 판정이 relation이면 그 도구 id를 모은다. 이미 담은 도구는 빈 목록 */
    private static List<String> clashWith(String t, List<String> ids, Map<String, ToolPair> pairMap, String relation) {
        if (ids.contains(t)) {
            return List.of();
        }
        return ids.stream().filter(id -> {
            ToolPair p = pairMap.get(PairKeys.of(id, t));
            return p != null && relation.equals(p.getRelation());
        }).toList();
    }

    private SituationCard situationCard(String situationId, String priority, List<String> ids, Map<String, Tool> byId, Map<String, ToolPair> pairMap) {
        if (situationId == null || situationId.isBlank()) {
            return null;
        }
        List<SituationRule> same = rules.findAll().stream().filter(r -> situationId.equals(r.getSituationId()))
                .sorted(Comparator.comparing(SituationRule::getPosition)).toList();
        java.util.function.Function<String, List<ToolRef>> refs = s -> java.util.Arrays.stream(s.split(java.util.regex.Pattern.quote("|")))
                .map(String::trim).filter(t -> !t.isEmpty())
                .map(t -> new ToolRef(t, byId.containsKey(t) ? byId.get(t).getName() : t, ids.contains(t),
                        clashWith(t, ids, pairMap, "overlap"), clashWith(t, ids, pairMap, "situational"))).toList();
        return same.stream().filter(r -> !r.isCaution()).findFirst()
                .map(r -> new SituationCard(r.getSituationId(), r.getCategory(), r.getLabel(), r.getBase(), refs.apply(r.getTools()),
                        r.getBetter(), r.getCost(), "tested".equals(r.getEvidenceType()) ? "직접 시험" : "제작자 설명",
                        r.getSource(), r.getReview(), pick(situationId, priority, ids, byId, pairMap),
                        r.getResultType(), r.getDisplay(),
                        same.stream().filter(SituationRule::isCaution)
                                .map(x -> new Caution(refs.apply(x.getTools()), x.getBetter(), x.getCost())).toList()))
                .orElse(null);
    }

    /** 상황 + 중요한 것으로 고른 도구. 안 골랐거나 시험에서 차이를 확인 못 한 조합이면 null */
    private Pick pick(String situationId, String priority, List<String> ids, Map<String, Tool> byId,
                           Map<String, ToolPair> pairMap) {
        if (priority == null || priority.isBlank()) {
            return null;
        }
        return picks.findById(situationId + "|" + priority).map(p -> {
            boolean base = "base".equals(p.getTools());
            List<ToolRef> refs = base ? List.of() : java.util.Arrays.stream(p.getTools().split(java.util.regex.Pattern.quote("|")))
                    .map(String::trim).filter(t -> !t.isEmpty())
                    .map(t -> new ToolRef(t, byId.containsKey(t) ? byId.get(t).getName() : t, ids.contains(t),
                            clashWith(t, ids, pairMap, "overlap"), clashWith(t, ids, pairMap, "situational"))).toList();
            return new Pick(priority, Labels.PRIORITY.get(priority), base, refs, p.getReason());
        }).orElse(null);
    }

    /** 빈 값·중복을 빼고 순서는 지킨다. 없는 도구나 너무 많은 도구는 거절한다. */
    List<String> clean(List<String> rawIds) {
        if (rawIds == null) {
            throw new BadRequestException("도구 목록(ids)이 필요해요");
        }
        List<String> ids = new ArrayList<>(new LinkedHashSet<>(rawIds.stream().filter(Objects::nonNull).map(String::trim)
                .filter(s -> !s.isEmpty()).toList()));
        if (ids.size() > MAX_TOOLS) {
            throw new BadRequestException("한 번에 " + MAX_TOOLS + "개까지 판정할 수 있어요");
        }
        List<String> missing = ids.stream().filter(id -> !tools.existsById(id)).toList();
        if (!missing.isEmpty()) {
            throw new BadRequestException("카탈로그에 없는 도구예요: " + String.join(", ", missing));
        }
        return ids;
    }

    private JudgeItem saved(ToolPair p) {
        return new JudgeItem(p.getA(), p.getB(), "saved", p.getRelation(), Labels.RELATION.get(p.getRelation()),
                Labels.REVIEW.get(p.getReviewState()), p.getReason(), toolService.sources(p), p.getJudgedAt());
    }

    private Map<String, ToolPair> pairMap() {
        return pairs.findAll().stream().collect(Collectors.toMap(ToolPair::getPairKey, Function.identity()));
    }

    private static int tokens(Tool t) {
        return t == null || t.getTokens() == null ? 0 : t.getTokens();
    }

    static String comma(int n) {
        return String.format(java.util.Locale.US, "%,d", n);
    }

    /** 도구함 안에서 서로 모두 같은 일(sameRole)인 3개 이상 묶음(최대 클리크). 큰 묶음 먼저, 같으면 도구함 순서. api.js roleGroups와 같음 */
    static List<List<String>> roleGroups(List<String> ids, Map<String, ToolPair> pairMap) {
        List<List<String>> out = new ArrayList<>();
        bronKerbosch(new ArrayList<>(), new ArrayList<>(ids), new ArrayList<>(), ids, pairMap, out);
        Comparator<List<String>> bySize = Comparator.comparingInt(g -> -g.size());
        out.sort(bySize.thenComparing((x, y) -> {
            for (int i = 0; i < Math.min(x.size(), y.size()); i++) {
                int d = ids.indexOf(x.get(i)) - ids.indexOf(y.get(i));
                if (d != 0) {
                    return d;
                }
            }
            return x.size() - y.size();
        }));
        return out;
    }

    private static void bronKerbosch(List<String> r, List<String> p, List<String> x, List<String> ids,
                                     Map<String, ToolPair> pairMap, List<List<String>> out) {
        if (p.isEmpty() && x.isEmpty()) {
            if (r.size() >= 3) {
                out.add(ids.stream().filter(r::contains).toList());
            }
            return;
        }
        for (String v : new ArrayList<>(p)) {
            List<String> n = ids.stream().filter(o -> !o.equals(v)).filter(o -> {
                ToolPair tp = pairMap.get(PairKeys.of(v, o));
                return tp != null && tp.isSameRole();
            }).toList();
            List<String> r2 = new ArrayList<>(r);
            r2.add(v);
            bronKerbosch(r2, p.stream().filter(n::contains).collect(Collectors.toCollection(ArrayList::new)),
                    x.stream().filter(n::contains).collect(Collectors.toCollection(ArrayList::new)), ids, pairMap, out);
            p.remove(v);
            x.add(v);
        }
    }
}
