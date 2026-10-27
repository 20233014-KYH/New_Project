package com.inventory.controller;

import com.inventory.domain.Judgment;
import com.inventory.domain.Tool;
import com.inventory.repository.ToolRepository;
import com.inventory.service.JudgmentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/tools")
public class ToolController {

    private final ToolRepository toolRepo;
    private final JudgmentService judgmentService;

    public ToolController(ToolRepository toolRepo, JudgmentService judgmentService) {
        this.toolRepo = toolRepo;
        this.judgmentService = judgmentService;
    }

    @GetMapping
    public List<Tool> list(
        @RequestParam(required = false) Integer category,
        @RequestParam(required = false) String q,
        @RequestParam(required = false, defaultValue = "stars") String sort
    ) {
        List<Tool> tools = category != null
            ? toolRepo.findByCategory(category)
            : toolRepo.findAll();

        if (q != null && !q.isBlank()) {
            String lq = q.toLowerCase();
            tools = tools.stream()
                .filter(t -> t.name.toLowerCase().contains(lq)
                    || (t.summary_ko != null && t.summary_ko.toLowerCase().contains(lq)))
                .collect(Collectors.toList());
        }

        tools = new ArrayList<>(tools);
        if ("pushed_at".equals(sort)) {
            tools.sort(Comparator.comparing((Tool t) ->
                t.auto != null && t.auto.pushed_at != null ? t.auto.pushed_at : "")
                .reversed());
        } else {
            tools.sort(Comparator.comparingLong((Tool t) ->
                t.auto != null ? t.auto.stars : 0L).reversed());
        }
        return tools;
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> get(@PathVariable String id) {
        Optional<Tool> opt = toolRepo.findById(id);
        if (opt.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        Tool tool = opt.get();
        List<Judgment> similar = judgmentService.findByPair(id, id).stream().toList();
        // 같은 분야 판정 목록
        List<Judgment> judgments = tool.category > 0
            ? toolRepo.findByCategory(tool.category).stream()
                .flatMap(other -> judgmentService.findByPair(id, other.id).stream())
                .distinct()
                .toList()
            : Collections.emptyList();

        Map<String, Object> resp = new LinkedHashMap<>();
        resp.put("tool", tool);
        resp.put("judgments", judgments);
        return ResponseEntity.ok(resp);
    }
}
