package kr.ac.team1.inventory.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonUnwrapped;
import java.util.List;
import tools.jackson.databind.JsonNode;

/**
 * 화면(web/app/src/api.js)과 주고받는 모양. 로컬 모드 결과와 같은 이름을 쓴다
 * (예: desc_en, review_state, otherId, unknownCount — 화면이 이미 이 이름으로 읽음).
 */
public final class Dtos {

    private Dtos() {
    }

    public record CategoryDto(Integer id, String name, String desc, String when) {
    }

    public record ToolDto(
            String id, String name, String repo, Integer category,
            @JsonProperty("desc_en") String descEn,
            @JsonProperty("summary_ko") String summaryKo,
            @JsonProperty("when_ko") String whenKo,
            String version, String license, Long stars,
            @JsonProperty("pushed_at") String pushedAt,
            Integer tokens, JsonNode scope,
            @JsonProperty("token_note") String tokenNote,
            @JsonProperty("checked_at") String checkedAt) {
    }

    /** 도구 상세에 붙는 판정 한 건 */
    public record ToolPairDto(
            String a, String b, String relation,
            @JsonProperty("review_state") String reviewState,
            String reason, List<String> sources,
            @JsonProperty("judged_at") String judgedAt,
            String otherId, String label, String review) {
    }

    /** 도구 카드(펼쳐서) + pairs + 이 도구를 직접 시험한 상황(기본 기능과 비교) */
    public record ToolDetailDto(@JsonUnwrapped ToolDto tool, List<ToolPairDto> pairs, List<ToolSituation> situations) {
    }

    /** 이 도구가 추천 도구로 들어간 상황 규칙 한 줄 + 그 상황의 중요한 것별 고르기 */
    public record ToolSituation(String id, String label, String base, String better, String cost, String evidence,
                                List<PickNote> picks) {
    }

    /** 중요한 것별 고르기 한 줄. chosen = 고른 도구 이름들(" 또는 ") 또는 "기본 기능" */
    public record PickNote(String priority, String label, String chosen, String reason) {
    }

    /** 도구함 판정 한 쌍. state = saved(저장된 판정) / no_info(확인된 정보 없음) */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record JudgeItem(
            String a, String b, String state, String relation, String label, String review,
            String reason, List<String> sources,
            @JsonProperty("judged_at") String judgedAt) {
    }

    public record RemoveItem(String tool, String keep, Integer save, String review, String reason,
                             List<String> sources, @JsonProperty("judged_at") String judgedAt) {
    }

    public record AddItem(String tool, String effect, String caution, List<String> warnings, List<String> unknown,
                          String blocked, String verdict, String date) {
    }

    public record RecommendResult(List<JudgeItem> pairs, List<RemoveItem> remove, List<AddItem> add, int unknownCount,
                                  SituationCard situation) {
    }

    /** 상황 질문의 선택지 하나 */
    public record SituationDto(String id, Integer category, String label) {
    }

    /** 추천 도구 하나. inBox = 이미 도구함에 담겨 있는지, overlapWith/similarTo = 도구함에서 겹침/상황따라 판정인 도구 */
    public record ToolRef(String id, String name, boolean inBox, List<String> overlapWith, List<String> similarTo) {
    }

    /** 고른 상황의 3칸 카드: 기본 기능으로도 / 이럴 땐 깔면 더 좋아요 / 대신 */
    public record SituationCard(String id, Integer category, String label, String base, List<ToolRef> tools,
                                String better, String cost, String evidence, String source, String review, Pick pick) {
    }

    /** 중요한 것에 따라 고른 도구. base = 기본 기능으로 충분(tools는 빈 목록) */
    public record Pick(String priority, String label, boolean base, List<ToolRef> tools, String reason) {
    }

    public record JudgeRequest(List<String> ids) {
    }

    /** 질문에 대한 답. work = bugfix/feature/빈칸, shell = bash/powershell/빈칸, logs = big_logs/small/빈칸,
     *  priority = accurate/save/simple/safe/빈칸 */
    public record Answers(String work, String shell, String logs, String situation, String priority) {
    }

    public record RecommendRequest(List<String> ids, Answers answers) {
    }
}
