package kr.ac.team1.inventory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import kr.ac.team1.inventory.dto.Dtos.AddItem;
import kr.ac.team1.inventory.dto.Dtos.Answers;
import kr.ac.team1.inventory.dto.Dtos.JudgeItem;
import kr.ac.team1.inventory.dto.Dtos.RecommendResult;
import kr.ac.team1.inventory.dto.Dtos.ToolDto;
import kr.ac.team1.inventory.dto.Dtos.ToolPairDto;
import kr.ac.team1.inventory.service.BadRequestException;
import kr.ac.team1.inventory.service.JudgeService;
import kr.ac.team1.inventory.service.NotFoundException;
import kr.ac.team1.inventory.service.ToolService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** 화면 로컬 모드 시험(web/app/src/api.test.js)과 같은 경우를 서버에서 확인한다. DB는 내장 H2. */
@SpringBootTest
class JudgeServiceTest {

    @Autowired
    JudgeService judge;

    @Autowired
    ToolService tools;

    private static final Answers NONE = new Answers("", "", "", null);

    @Test
    void 처음_데이터가_DB에_다_들어감() {
        assertThat(tools.categories()).hasSize(6);
        assertThat(tools.list(null, null)).hasSize(36);
    }

    @Test
    void 겹침_1쌍과_빼기_후보_ecc() {
        List<JudgeItem> pairs = judge.judge(List.of("superpowers", "ecc", "caveman"));
        List<JudgeItem> overlaps = pairs.stream().filter(p -> "overlap".equals(p.relation())).toList();
        assertThat(overlaps).hasSize(1);
        assertThat(overlaps.get(0).a()).isEqualTo("superpowers");
        assertThat(overlaps.get(0).b()).isEqualTo("ecc");

        RecommendResult rec = judge.recommend(List.of("superpowers", "ecc", "caveman"), NONE);
        assertThat(rec.remove()).hasSize(1);
        assertThat(rec.remove().get(0).tool()).isEqualTo("ecc");
        assertThat(rec.remove().get(0).save()).isEqualTo(9169);
    }

    @Test
    void 파워셸이면_rtk_카드에_주의와_효과없음() {
        RecommendResult rec = judge.recommend(List.of("caveman"), new Answers("", "powershell", "", null));
        AddItem rtk = rec.add().stream().filter(a -> a.tool().equals("rtk")).findFirst().orElseThrow();
        assertThat(rtk.verdict()).isEqualTo("지금 환경에서는 효과가 없어요");
        assertThat(rtk.warnings()).isNotEmpty();
    }

    @Test
    void 판정_없는_쌍은_확인된_정보_없음() {
        List<JudgeItem> pairs = judge.judge(List.of("caveman", "graphify"));
        assertThat(pairs).singleElement().satisfies(p -> {
            assertThat(p.state()).isEqualTo("no_info");
            assertThat(p.label()).isEqualTo("확인된 정보 없음");
            assertThat(p.review()).isEqualTo("다른 분야");
        });
        assertThatThrownBy(() -> judge.judgment("caveman", "graphify")).isInstanceOf(NotFoundException.class);
    }

    @Test
    void 분야_필터와_한국어_검색() {
        assertThat(tools.list(1, null)).allMatch(t -> t.category() == 1).isNotEmpty();
        List<ToolDto> found = tools.list(null, "원시인");
        assertThat(found).extracting(ToolDto::id).containsExactly("caveman");
        assertThat(found.get(0).summaryKo()).isNotBlank();
        assertThat(found.get(0).whenKo()).isNotBlank();
    }

    @Test
    void 검수_상태가_그대로_사람검토_87_직접시험_3() {
        Map<String, String> seen = new HashMap<>();
        for (ToolDto t : tools.list(null, null)) {
            for (ToolPairDto p : tools.detail(t.id()).pairs()) {
                seen.put(p.a().compareTo(p.b()) < 0 ? p.a() + "|" + p.b() : p.b() + "|" + p.a(), p.review());
            }
        }
        assertThat(seen.values().stream().filter("사람 검토"::equals).count()).isEqualTo(87);
        assertThat(seen.values().stream().filter("직접 시험"::equals).count()).isEqualTo(3);
    }

    @Test
    void 저장된_판정에는_이유_출처_확인일() {
        JudgeItem p = judge.judge(List.of("superpowers", "ecc")).get(0);
        assertThat(p.reason()).isNotBlank();
        assertThat(p.sources()).isNotEmpty();
        assertThat(p.judgedAt()).isEqualTo("2026-10-19");
        assertThat(judge.recommend(List.of("superpowers", "ecc"), NONE).remove().get(0).reason()).isNotBlank();
    }

    @Test
    void 없는_도구나_너무_많은_도구는_거절() {
        assertThatThrownBy(() -> judge.judge(List.of("superpowers", "없는도구"))).isInstanceOf(BadRequestException.class);
        List<String> many = java.util.stream.IntStream.range(0, JudgeService.MAX_TOOLS + 1).mapToObj(i -> "t" + i).toList();
        assertThatThrownBy(() -> judge.judge(many)).isInstanceOf(BadRequestException.class);
    }

    @Test
    void 같은_도구를_두_번_담아도_한_번만() {
        assertThat(judge.judge(List.of("superpowers", "superpowers", "ecc"))).hasSize(1);
    }

    @Test
    void 상황_질문_선택지는_규칙_18개() {
        assertThat(judge.situations()).hasSize(18);
        assertThat(judge.situations().get(0).id()).isEqualTo("plan-new");
    }

    @Test
    void 상황을_고르면_기본으로_되는_것_깔면_좋은_도구_비용_카드() {
        var card = judge.recommend(List.of("superpowers"), new Answers("", "", "", "e2e-test")).situation();
        assertThat(card.base()).contains("11/12");
        assertThat(card.tools()).extracting(t -> t.id()).containsExactly("playwright-mcp");
        assertThat(card.tools().get(0).inBox()).isFalse();
        assertThat(card.cost()).isEqualTo("추가 비용 없음");
        assertThat(card.evidence()).isEqualTo("직접 시험");
    }

    @Test
    void 이미_담은_도구는_inBox로_표시하고_시험_전_근거는_제작자_설명() {
        var debug = judge.recommend(List.of("playwright-mcp"), new Answers("", "", "", "site-debug")).situation();
        assertThat(debug.tools()).hasSize(2);
        assertThat(debug.tools().get(0).inBox()).isTrue();
        var sec = judge.recommend(List.of("superpowers"), new Answers("", "", "", "security")).situation();
        assertThat(sec.evidence()).isEqualTo("제작자 설명");
    }

    @Test
    void 상황을_안_고르거나_없는_상황이면_카드_없음() {
        assertThat(judge.recommend(List.of("superpowers"), NONE).situation()).isNull();
        assertThat(judge.recommend(List.of("superpowers"), new Answers("", "", "", "없는상황")).situation()).isNull();
    }
}
