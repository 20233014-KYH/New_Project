package kr.ac.team1.inventory.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/**
 * 목적 하나 → 상황 여러 개 (출처: web/app/src/data/situation_goals.csv).
 * 예: 해커톤 = 아이디어 다듬기 + 계획 + 새 라이브러리 + 화면 테스트 + 큰 도구 결과 + 사용량 보기.
 */
@Entity
public class SituationGoal {

    @Id
    private String goalId;

    private String label;

    private String description;

    /** 상황ID들(| 로 이어 붙임) */
    private String situations;

    private Integer position;

    protected SituationGoal() {
    }

    public SituationGoal(String goalId, String label, String description, String situations, Integer position) {
        this.goalId = goalId;
        this.label = label;
        this.description = description;
        this.situations = situations;
        this.position = position;
    }

    public String getGoalId() { return goalId; }
    public String getLabel() { return label; }
    public String getDescription() { return description; }
    public String getSituations() { return situations; }
    public Integer getPosition() { return position; }
}
