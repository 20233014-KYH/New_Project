package com.inventory.service;

import com.inventory.domain.*;
import com.inventory.repository.JudgmentRepository;
import com.inventory.repository.ToolRepository;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class JudgmentService {

    private final JudgmentRepository judgmentRepo;
    private final ToolRepository toolRepo;

    public JudgmentService(JudgmentRepository judgmentRepo, ToolRepository toolRepo) {
        this.judgmentRepo = judgmentRepo;
        this.toolRepo = toolRepo;
    }

    public record PairResult(
        String a, String b,
        String state,
        String relation,
        String review_state,
        String reason_ko,
        List<Evidence> evidence,
        String judged_at
    ) {}

    public record BoxResult(
        List<PairResult> pairs,
        List<String> unknown_tools,
        String range_note
    ) {}

    /** 도구 목록을 받아 모든 쌍의 판정을 반환 */
    public BoxResult judgeBox(List<String> toolIds) {
        List<String> unknown = new ArrayList<>();
        List<String> known = new ArrayList<>();

        for (String id : toolIds) {
            if (toolRepo.findById(id).isPresent()) {
                known.add(id);
            } else {
                unknown.add(id);
            }
        }

        List<PairResult> pairs = new ArrayList<>();
        Set<PairKey> seen = new LinkedHashSet<>();

        for (int i = 0; i < known.size(); i++) {
            for (int j = i + 1; j < known.size(); j++) {
                PairKey key = new PairKey(known.get(i), known.get(j));
                if (seen.add(key)) {
                    pairs.add(buildPairResult(key));
                }
            }
        }

        String rangeNote = known.size() >= 3
            ? "확인한 쌍의 범위에서만 판단했어요"
            : null;

        return new BoxResult(pairs, unknown, rangeNote);
    }

    public PairResult buildPairResult(PairKey key) {
        Optional<Judgment> opt = judgmentRepo.findByPair(key);
        if (opt.isEmpty()) {
            return new PairResult(key.first, key.second, "no_info",
                null, null, null, null, null);
        }
        Judgment j = opt.get();
        String state = resolveState(j);
        return new PairResult(
            key.first, key.second,
            state,
            j.relation,
            j.review_state,
            j.reason_ko,
            j.evidence,
            j.judged_at
        );
    }

    private String resolveState(Judgment j) {
        // outdated: entries 의 version 이 판정 당시 version 과 다르면
        Optional<Tool> ta = toolRepo.findById(j.a);
        Optional<Tool> tb = toolRepo.findById(j.b);
        boolean outdated = false;
        if (ta.isPresent() && j.a_version != null && !j.a_version.equals(ta.get().version)) {
            outdated = true;
        }
        if (tb.isPresent() && j.b_version != null && !j.b_version.equals(tb.get().version)) {
            outdated = true;
        }
        if (outdated) return "outdated";
        return "saved";
    }

    public Optional<Judgment> findByPair(String a, String b) {
        return judgmentRepo.findByPair(new PairKey(a, b));
    }
}
