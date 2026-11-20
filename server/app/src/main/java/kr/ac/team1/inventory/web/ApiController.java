package kr.ac.team1.inventory.web;

import java.util.List;
import kr.ac.team1.inventory.dto.Dtos.CategoryDto;
import kr.ac.team1.inventory.dto.Dtos.JudgeItem;
import kr.ac.team1.inventory.dto.Dtos.JudgeRequest;
import kr.ac.team1.inventory.dto.Dtos.RecommendRequest;
import kr.ac.team1.inventory.dto.Dtos.RecommendResult;
import kr.ac.team1.inventory.dto.Dtos.SituationDto;
import kr.ac.team1.inventory.dto.Dtos.ToolDetailDto;
import kr.ac.team1.inventory.dto.Dtos.ToolDto;
import kr.ac.team1.inventory.service.JudgeService;
import kr.ac.team1.inventory.service.ToolService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 화면이 부르는 주소(server/api-draft.md 2장). 화면은 VITE_API_BASE=http://localhost:8080/api 로 연결 */
@RestController
@RequestMapping("/api")
public class ApiController {

    private final ToolService toolService;
    private final JudgeService judgeService;

    public ApiController(ToolService toolService, JudgeService judgeService) {
        this.toolService = toolService;
        this.judgeService = judgeService;
    }

    /** 분야 6개 */
    @GetMapping("/categories")
    public List<CategoryDto> categories() {
        return toolService.categories();
    }

    /** 도구 목록(분야·검색어로 거르기) */
    @GetMapping("/tools")
    public List<ToolDto> tools(@RequestParam(required = false) Integer category, @RequestParam(required = false) String q) {
        return toolService.list(category, q);
    }

    /** 도구 카드 하나 + 이 도구와 관련된 판정 */
    @GetMapping("/tools/{id}")
    public ToolDetailDto tool(@PathVariable String id) {
        return toolService.detail(id);
    }

    /** 두 도구의 판정. 없으면 404 → 화면에 "확인된 정보 없음" */
    @GetMapping("/judgments")
    public JudgeItem judgment(@RequestParam String a, @RequestParam String b) {
        return judgeService.judgment(a, b);
    }

    /** 도구함 전체 판정(모든 짝) */
    @PostMapping({"/judge", "/box/judge"})
    public List<JudgeItem> judge(@RequestBody JudgeRequest req) {
        return judgeService.judge(req.ids());
    }

    /** 상황 질문의 선택지 (상황별 추천 규칙에서) */
    @GetMapping("/situations")
    public List<SituationDto> situations() {
        return judgeService.situations();
    }

    /** 추천(빼기·더하기). answers = 질문에 대한 답 */
    @GetMapping("/goals")
    public List<kr.ac.team1.inventory.dto.Dtos.GoalDto> goals() {
        return judgeService.goals();
    }

    @PostMapping("/recommend")
    public RecommendResult recommend(@RequestBody RecommendRequest req) {
        return judgeService.recommend(req.ids(), req.answers());
    }
}
