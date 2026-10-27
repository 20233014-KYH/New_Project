package com.inventory.controller;

import com.inventory.domain.Judgment;
import com.inventory.service.JudgmentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;

@RestController
@RequestMapping("/api/judgments")
public class JudgmentController {

    private final JudgmentService judgmentService;

    public JudgmentController(JudgmentService judgmentService) {
        this.judgmentService = judgmentService;
    }

    @GetMapping
    public ResponseEntity<?> get(@RequestParam String a, @RequestParam String b) {
        Optional<Judgment> opt = judgmentService.findByPair(a, b);
        if (opt.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        return ResponseEntity.ok(opt.get());
    }
}
