package kr.ac.team1.inventory.service;

import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import kr.ac.team1.inventory.domain.Tool;
import kr.ac.team1.inventory.domain.ToolPair;
import kr.ac.team1.inventory.dto.Dtos.CategoryDto;
import kr.ac.team1.inventory.dto.Dtos.ToolDetailDto;
import kr.ac.team1.inventory.dto.Dtos.ToolDto;
import kr.ac.team1.inventory.dto.Dtos.ToolPairDto;
import kr.ac.team1.inventory.repo.CategoryRepository;
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

    public ToolService(CategoryRepository categories, ToolRepository tools, ToolPairRepository pairs, ObjectMapper mapper) {
        this.categories = categories;
        this.tools = tools;
        this.pairs = pairs;
        this.mapper = mapper;
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
                        Labels.RELATION.get(p.getRelation()), Labels.REVIEW.get(p.getReviewState())))
                .toList();
        return new ToolDetailDto(toDto(tool), related);
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
                t.getScopeJson() == null ? null : mapper.readTree(t.getScopeJson()), t.getTokenNote(), t.getCheckedAt());
    }

    private static boolean contains(String s, String lq) {
        return s != null && s.toLowerCase(Locale.ROOT).contains(lq);
    }
}
