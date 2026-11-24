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
import kr.ac.team1.inventory.dto.Dtos.Answers;
import kr.ac.team1.inventory.dto.Dtos.JudgeItem;
import kr.ac.team1.inventory.dto.Dtos.RecommendResult;
import kr.ac.team1.inventory.dto.Dtos.RemoveItem;
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
    private final ToolService toolService;

    public JudgeService(ToolRepository tools, ToolPairRepository pairs, TestedToolRepository tested, ToolService toolService) {
        this.tools = tools;
        this.pairs = pairs;
        this.tested = tested;
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
        Answers ans = answers == null ? new Answers("", "", "") : answers;
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
                remove.add(new RemoveItem(big.getId(), keep.getId(), tokens(big), p.review(), p.reason(), p.sources(), p.judgedAt()));
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
        return new RecommendResult(js, remove, add, unknownCount);
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
        return t.getTokens() == null ? 0 : t.getTokens();
    }
}
