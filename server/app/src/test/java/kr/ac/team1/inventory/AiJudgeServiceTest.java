package kr.ac.team1.inventory;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import kr.ac.team1.inventory.ai.AiDisabledException;
import kr.ac.team1.inventory.ai.AiJudgeService;
import kr.ac.team1.inventory.domain.PairKeys;
import kr.ac.team1.inventory.repo.ToolPairRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

/** 서버 AI 판정: 키가 없으면 절대 부르지 않는다(시험에서 실제 API 호출·요금이 생기지 않게 키를 비워 둠). */
@SpringBootTest(properties = "ANTHROPIC_API_KEY=")
@Transactional
class AiJudgeServiceTest {

    @Autowired
    AiJudgeService ai;

    @Autowired
    ToolPairRepository pairs;

    @Test
    void 카탈로그_36개끼리는_빈_쌍이_없어서_부르지_않는다() {
        assertThat(ai.enabled()).isFalse();
        assertThat(ai.missingPairs()).isEmpty();
        assertThat(ai.judgeMissing(20).judged()).isZero();
    }

    @Test
    void 빈_쌍이_생겼는데_키가_없으면_꺼져_있다고_알린다() {
        pairs.findAll().stream().filter(p -> p.getPairKey().equals(PairKeys.of("caveman", "graphify")))
                .forEach(pairs::delete);
        assertThat(ai.missingPairs()).hasSize(1);
        assertThatThrownBy(() -> ai.judgeMissing(20)).isInstanceOf(AiDisabledException.class)
                .hasMessageContaining("빈 쌍 1개");
    }
}
