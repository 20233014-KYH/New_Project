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

    private static final Answers NONE = new Answers("", "", "", null, null, null);

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
        assertThat(rec.remove().get(0).save()).isEqualTo(17491);   // 2026-11-21 Claude Code 2.1.318로 다시 잰 값
        assertThat(rec.remove().get(0).group()).isNull();
    }

    @Test
    void 같은_일_묶음_3개는_둘씩은_상황따라여도_합쳐서_기준을_넘으면_하나만_남긴다() {
        // graphify 795 · codegraph 1,109 · understand-anything 1,355: 둘씩은 작은 쪽이 기준(1,642) 미만이라 상황따라
        List<String> box = List.of("graphify", "codegraph", "understand-anything");
        assertThat(judge.judge(box)).noneMatch(p -> "overlap".equals(p.relation()));
        RecommendResult rec = judge.recommend(box, NONE);
        // 가장 큰 것을 남겨도 795 + 1,109 = 1,904 ≥ 1,642 → 가장 작은 graphify만 남김
        assertThat(rec.remove()).extracting(r -> r.tool()).containsExactly("codegraph", "understand-anything");
        assertThat(rec.remove()).allMatch(r -> r.keep().equals("graphify") && r.group().equals(box));
        assertThat(rec.remove().get(0).reason()).contains("1,904").contains("1,642");
    }

    @Test
    void 같은_일_둘만_있으면_묶음_빼기는_없다() {
        assertThat(judge.recommend(List.of("graphify", "codegraph"), NONE).remove()).isEmpty();
    }

    @Test
    void 파워셸이면_rtk_카드에_주의와_효과없음() {
        RecommendResult rec = judge.recommend(List.of("caveman"), new Answers("", "powershell", "", null, null, null));
        AddItem rtk = rec.add().stream().filter(a -> a.tool().equals("rtk")).findFirst().orElseThrow();
        assertThat(rtk.verdict()).isEqualTo("지금 환경에서는 효과가 없어요");
        assertThat(rtk.warnings()).isNotEmpty();
    }

    @Test
    void 다른_분야_쌍도_AI_추정_판정이_있다() {
        // 2026-11-21 다른 분야 540쌍을 Claude·Codex 교차 판정으로 채움 → 카탈로그 36개끼리는 판정 없는 쌍이 없음
        List<JudgeItem> pairs = judge.judge(List.of("caveman", "graphify"));
        assertThat(pairs).singleElement().satisfies(p -> {
            assertThat(p.state()).isEqualTo("saved");
            assertThat(p.review()).isEqualTo("AI 추정");
        });
        assertThat(judge.judge(tools.list(null, null).stream().map(t -> t.id()).toList()))
                .noneMatch(p -> "no_info".equals(p.state()));
        // 직접 시험 기록이 있는 다른 분야 쌍은 시험 결과로
        assertThat(judge.judge(List.of("superpowers", "caveman"))).singleElement()
                .satisfies(p -> assertThat(p.review()).isEqualTo("직접 시험"));
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
    void 검수_상태가_그대로_사람검토_87_직접시험_4_AI추정_539() {
        Map<String, String> seen = new HashMap<>();
        for (ToolDto t : tools.list(null, null)) {
            for (ToolPairDto p : tools.detail(t.id()).pairs()) {
                seen.put(p.a().compareTo(p.b()) < 0 ? p.a() + "|" + p.b() : p.b() + "|" + p.a(), p.review());
            }
        }
        assertThat(seen.values().stream().filter("사람 검토"::equals).count()).isEqualTo(87);
        assertThat(seen.values().stream().filter("직접 시험"::equals).count()).isEqualTo(4);
        assertThat(seen.values().stream().filter("AI 추정"::equals).count()).isEqualTo(539);
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
        var card = judge.recommend(List.of("superpowers"), new Answers("", "", "", "e2e-test", null, null)).situation();
        assertThat(card.base()).contains("11/12");
        assertThat(card.tools()).extracting(t -> t.id()).containsExactly("playwright-mcp");
        assertThat(card.tools().get(0).inBox()).isFalse();
        assertThat(card.cost()).isEqualTo("추가 비용 없음");
        assertThat(card.evidence()).isEqualTo("직접 시험");
    }

    @Test
    void 도구_상세에_기본_기능과_비교한_시험_상황이_붙는다() {
        var sits = tools.detail("headroom").situations();
        assertThat(sits).extracting(x -> x.id()).containsExactly("big-tool-output");
        assertThat(sits.get(0).picks()).extracting(x -> x.priority()).containsExactly("accurate", "save", "simple");
        assertThat(sits.get(0).picks().get(2).chosen()).isEqualTo("기본 기능");
        assertThat(tools.detail("codegraph").situations()).extracting(x -> x.id()).containsExactly("code-find", "code-flow");
        assertThat(tools.detail("tdd-guard").situations()).isEmpty();
    }

    @Test
    void 목적을_고르면_더하기_꺼도_되는_것_그대로를_정한다() {
        var hack = judge.recommend(List.of("caveman"), new Answers("", "", "", null, "accurate", "hackathon")).goal();
        assertThat(hack.situations()).hasSize(6);
        assertThat(hack.add()).extracting(x -> x.tool()).containsExactly("gstack", "playwright-mcp", "headroom");
        assertThat(hack.add().get(2).warnings()).anyMatch(w -> w.contains("caveman"));
        assertThat(hack.keep()).isEmpty();

        // 토큰이 중요하고, 시험에서 '기본 기능으로 충분'이던 상황의 도구가 도구함에 있으면 꺼도 되는 것
        var lp = judge.recommend(List.of("graphify"), new Answers("", "", "", null, "save", "long-project")).goal();
        assertThat(lp.turnOff()).extracting(x -> x.tool()).containsExactly("graphify");
        assertThat(lp.turnOff().get(0).situations()).containsExactly("큰 코드에서 함수나 기능이 어디 있는지 찾고 싶어요");

        // 이미 있는 도구는 그대로, 시험 주의(PowerShell에선 rtk가 안 됨)는 경고로
        var save = judge.recommend(List.of("caveman"), new Answers("", "powershell", "", null, "save", "save-limit")).goal();
        assertThat(save.keep()).extracting(x -> x.tool()).containsExactly("caveman");
        var rtk = save.add().stream().filter(x -> x.tool().equals("rtk")).findFirst().orElseThrow();
        assertThat(rtk.warnings()).anyMatch(w -> w.contains("PowerShell"));

        // 중요한 것을 안 고르면 상황 카드만
        var none = judge.recommend(List.of("caveman"), new Answers("", "", "", null, null, "hackathon")).goal();
        assertThat(none.add()).isEmpty();
        assertThat(none.situations()).hasSize(6);
        assertThat(judge.goals()).hasSize(6);
    }

    @Test
    void 중요한_것을_고르면_시험_결과로_도구를_하나_고른다() {
        var acc = judge.recommend(List.of(), new Answers("", "", "", "big-tool-output", "accurate", null)).situation().pick();
        assertThat(acc.base()).isFalse();
        assertThat(acc.tools()).extracting(t -> t.id()).containsExactly("headroom");
        assertThat(acc.label()).isEqualTo("틀리지 않는 것");
        var save = judge.recommend(List.of(), new Answers("", "", "", "big-tool-output", "save", null)).situation().pick();
        assertThat(save.tools()).extracting(t -> t.id()).containsExactly("caveman");
        var safe = judge.recommend(List.of(), new Answers("", "", "", "db-ask", "safe", null)).situation().pick();
        assertThat(safe.tools()).extracting(t -> t.id()).containsExactly("dbhub");
        var base = judge.recommend(List.of(), new Answers("", "", "", "code-find", "save", null)).situation().pick();
        assertThat(base.base()).isTrue();
        assertThat(base.tools()).isEmpty();
        // 시험에서 차이를 확인 못 한 조합·중요한 것을 안 고름 → null
        assertThat(judge.recommend(List.of(), new Answers("", "", "", "usage-view", "accurate", null)).situation().pick()).isNull();
        assertThat(judge.recommend(List.of(), new Answers("", "", "", "db-ask", null, null)).situation().pick()).isNull();
    }

    @Test
    void 추천_도구가_도구함_도구와_겹치거나_비슷하면_카드에_알린다() {
        // gsd-core(도구함) ↔ superpowers(추천) = 겹침, serena(도구함) ↔ codegraph(추천) = 상황따라
        var multi = judge.recommend(List.of("gsd-core"), new Answers("", "", "", "multi-day", null, null)).situation();
        assertThat(multi.tools().get(0).overlapWith()).containsExactly("gsd-core");
        var find = judge.recommend(List.of("serena"), new Answers("", "", "", "code-find", null, null)).situation();
        var codegraph = find.tools().stream().filter(t -> t.id().equals("codegraph")).findFirst().orElseThrow();
        assertThat(codegraph.similarTo()).containsExactly("serena");
        assertThat(codegraph.overlapWith()).isEmpty();
        var serena = find.tools().stream().filter(t -> t.id().equals("serena")).findFirst().orElseThrow();
        assertThat(serena.inBox()).isTrue();
        assertThat(serena.similarTo()).isEmpty();
    }

    @Test
    void 이미_담은_도구는_inBox로_표시하고_시험_전_근거는_제작자_설명() {
        var debug = judge.recommend(List.of("playwright-mcp"), new Answers("", "", "", "site-debug", null, null)).situation();
        assertThat(debug.tools()).hasSize(2);
        assertThat(debug.tools().get(0).inBox()).isTrue();
        var sec = judge.recommend(List.of("superpowers"), new Answers("", "", "", "security", null, null)).situation();
        assertThat(sec.evidence()).isEqualTo("제작자 설명");
    }

    @Test
    void 상황을_안_고르거나_없는_상황이면_카드_없음() {
        assertThat(judge.recommend(List.of("superpowers"), NONE).situation()).isNull();
        assertThat(judge.recommend(List.of("superpowers"), new Answers("", "", "", "없는상황", null, null)).situation()).isNull();
    }
}
