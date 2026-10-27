package com.inventory.controller;

import com.inventory.service.JudgmentService;
import com.inventory.service.RecommendService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/box")
public class BoxController {

    private final JudgmentService judgmentService;
    private final RecommendService recommendService;

    public BoxController(JudgmentService judgmentService, RecommendService recommendService) {
        this.judgmentService = judgmentService;
        this.recommendService = recommendService;
    }

    record JudgeRequest(List<String> tools, List<String> memo_tools) {}

    record RecommendRequest(
        List<String> tools,
        String work,
        Map<String, String> env
    ) {}

    @PostMapping("/judge")
    public ResponseEntity<?> judge(@RequestBody JudgeRequest req) {
        if (req.tools() == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "tools 필드가 필요해요"));
        }
        JudgmentService.BoxResult result = judgmentService.judgeBox(req.tools());
        return ResponseEntity.ok(result);
    }

    @PostMapping("/recommend")
    public ResponseEntity<?> recommend(@RequestBody RecommendRequest req) {
        if (req.tools() == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "tools 필드가 필요해요"));
        }
        RecommendService.RecommendResult result = recommendService.recommend(
            req.tools(), req.work(), req.env());
        return ResponseEntity.ok(result);
    }
}
