package kr.ac.team1.inventory.web;

import java.util.Map;
import kr.ac.team1.inventory.ai.AiJudgeService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 관리용: 판정이 빈 쌍을 서버 AI로 채운다(새 도구를 넣은 뒤).
 * 로그인 기능이 없어서 지금은 내 컴퓨터에서만 켜는 서버 전제다. 배포하려면 이 주소에 인증을 먼저 붙여야 한다.
 */
@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AiJudgeService ai;

    public AdminController(AiJudgeService ai) {
        this.ai = ai;
    }

    /** 서버 AI가 켜져 있는지, 판정이 빈 쌍이 몇 개인지 */
    @GetMapping("/ai-status")
    public Map<String, Object> status() {
        return Map.of("enabled", ai.enabled(), "missing", ai.missingPairs().size());
    }

    /** 판정이 빈 쌍을 limit개까지 서버 AI로 판정해 저장(키가 없으면 503) */
    @PostMapping("/judge-missing")
    public AiJudgeService.Result judgeMissing(@RequestParam(defaultValue = "20") int limit) {
        return ai.judgeMissing(Math.min(limit, 50));
    }
}
