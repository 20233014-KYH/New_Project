package com.inventory.service;

import com.inventory.domain.*;
import com.inventory.repository.TestedRepository;
import com.inventory.repository.ToolRepository;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class RecommendService {

    private final JudgmentService judgmentService;
    private final ToolRepository toolRepo;
    private final TestedRepository testedRepo;

    public RecommendService(JudgmentService judgmentService,
                            ToolRepository toolRepo,
                            TestedRepository testedRepo) {
        this.judgmentService = judgmentService;
        this.toolRepo = toolRepo;
        this.testedRepo = testedRepo;
    }

    public record RemoveItem(
        String tool, String because, String with,
        long save_tokens_max, String evidence_type, String note
    ) {}

    public record AddItem(
        String tool, String condition_ko,
        String evidence_type,
        List<String> pairs_checked,
        List<String> pairs_unknown
    ) {}

    public record RecommendResult(
        List<RemoveItem> remove,
        List<AddItem> add,
        List<Object> replace,
        String none_reason
    ) {}

    public RecommendResult recommend(List<String> toolIds, String work, Map<String, String> env) {
        List<String> known = toolIds.stream()
            .filter(id -> toolRepo.findById(id).isPresent())
            .toList();

        List<RemoveItem> remove = buildRemove(known);
        List<AddItem> add = buildAdd(known, work, env);

        String noneReason = (remove.isEmpty() && add.isEmpty())
            ? "현재 데이터로 추천할 수 있는 항목이 없어요"
            : null;

        return new RecommendResult(remove, add, Collections.emptyList(), noneReason);
    }

    private List<RemoveItem> buildRemove(List<String> known) {
        List<RemoveItem> result = new ArrayList<>();
        Set<PairKey> seen = new HashSet<>();

        for (int i = 0; i < known.size(); i++) {
            for (int j = i + 1; j < known.size(); j++) {
                PairKey key = new PairKey(known.get(i), known.get(j));
                if (!seen.add(key)) continue;

                JudgmentService.PairResult pr = judgmentService.buildPairResult(key);
                if (!"saved".equals(pr.state()) && !"outdated".equals(pr.state())) continue;
                if (!"overlap".equals(pr.relation())) continue;

                // 처음 읽는 양이 큰 쪽을 제거 후보로
                String candidate = pickLargerToken(key.first, key.second);
                String keep = candidate.equals(key.first) ? key.second : key.first;

                long saveTokens = calcSaveTokens(candidate, keep);
                String evidenceType = pr.review_state() != null ? pr.review_state() : "doc";

                String note = buildOverlapNote(pr);

                result.add(new RemoveItem(candidate, "overlap", keep,
                    saveTokens, evidenceType, note));
            }
        }
        return result;
    }

    private String pickLargerToken(String a, String b) {
        long ta = toolRepo.findById(a).map(t -> t.always_on_tokens_est).orElse(0L);
        long tb = toolRepo.findById(b).map(t -> t.always_on_tokens_est).orElse(0L);
        return ta >= tb ? a : b;
    }

    private long calcSaveTokens(String candidate, String keep) {
        return toolRepo.findById(candidate).map(t -> t.always_on_tokens_est).orElse(0L);
    }

    private String buildOverlapNote(JudgmentService.PairResult pr) {
        if (pr.evidence() == null) return null;
        return pr.evidence().stream()
            .filter(e -> "tested".equals(e.type))
            .map(e -> e.claim)
            .findFirst()
            .orElse(null);
    }

    private List<AddItem> buildAdd(List<String> known, String work, Map<String, String> env) {
        List<AddItem> result = new ArrayList<>();
        String shell = env != null ? env.get("shell") : null;

        for (TestedInfo ti : testedRepo.findAll()) {
            if (known.contains(ti.tool)) continue;

            Tool candidate = toolRepo.findById(ti.tool).orElse(null);
            if (candidate == null) continue;

            // 도구함 내 모든 도구와의 판정 확인
            List<String> pairsChecked = new ArrayList<>();
            List<String> pairsUnknown = new ArrayList<>();
            boolean hasConflict = false;

            for (String knownId : known) {
                JudgmentService.PairResult pr = judgmentService.buildPairResult(
                    new PairKey(ti.tool, knownId));
                if ("no_info".equals(pr.state())) {
                    pairsUnknown.add(knownId);
                } else {
                    if ("overlap".equals(pr.relation()) || "verified_issue".equals(pr.relation())) {
                        hasConflict = true;
                        break;
                    }
                    pairsChecked.add(knownId);
                }
            }

            if (hasConflict) continue;

            // 조건 문구 조합
            String conditionKo = buildCondition(ti, work, shell);

            result.add(new AddItem(
                ti.tool,
                conditionKo,
                "tested",
                pairsChecked,
                pairsUnknown
            ));
        }
        return result;
    }

    private String buildCondition(TestedInfo ti, String work, String shell) {
        StringBuilder sb = new StringBuilder();
        if (ti.caution_work != null && ti.caution_work.equals(work) && ti.caution != null) {
            sb.append(ti.caution).append(" ");
        }
        if (ti.caution_shell != null && ti.caution_shell.equals(shell) && ti.caution != null) {
            sb.append(ti.caution);
        }
        if (sb.isEmpty() && ti.effect != null) {
            sb.append(ti.effect);
        }
        return sb.toString().trim();
    }
}
