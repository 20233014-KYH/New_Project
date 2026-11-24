package kr.ac.team1.inventory.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

/**
 * 상황 + 중요한 것 → 고를 도구 한 줄 (출처: web/app/src/data/situation_priority.csv).
 * 직접 시험에서 차이가 확인된 조합만 있다. 고를 도구가 base면 "기본 기능으로 충분".
 */
@Entity
public class SituationPick {

    /** 상황ID|중요한 것 */
    @Id
    private String pickKey;

    private String situationId;

    /** accurate / save / simple / safe */
    private String priority;

    /** 고를 도구 아이디들(| 로 이어 붙임) 또는 base */
    private String tools;

    @Lob
    private String reason;

    protected SituationPick() {
    }

    public SituationPick(String situationId, String priority, String tools, String reason) {
        this.pickKey = situationId + "|" + priority;
        this.situationId = situationId;
        this.priority = priority;
        this.tools = tools;
        this.reason = reason;
    }

    public String getPickKey() { return pickKey; }
    public String getSituationId() { return situationId; }
    public String getPriority() { return priority; }
    public String getTools() { return tools; }
    public String getReason() { return reason; }
}
