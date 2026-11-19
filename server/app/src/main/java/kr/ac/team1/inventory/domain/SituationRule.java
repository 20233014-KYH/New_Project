package kr.ac.team1.inventory.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

/**
 * 상황별 추천 규칙 한 줄 (출처: web/app/src/data/situation_rules.csv).
 * "이 상황이면 기본 기능으로도 여기까지 되고, 이럴 땐 이 오픈소스를 깔면 더 좋고, 대신 이만큼 더 든다."
 */
@Entity
public class SituationRule {

    @Id
    private String ruleId;

    /** 분야 번호 1~6 */
    private Integer category;

    /** 화면 질문의 선택지 아이디 (예: e2e-test) */
    private String situationId;

    /** 상황(쉬운 말) — 질문 선택지 문장 */
    private String label;

    @Lob
    private String base;

    /** 추천 도구 아이디들. 여러 개면 | 로 이어 붙임 */
    private String tools;

    @Lob
    private String better;

    private String cost;

    /** tested(직접 시험) / doc(제작자 설명) */
    private String evidenceType;

    @Lob
    private String source;

    private String review;

    /** CSV 순서(질문 선택지를 같은 순서로 보여 주려고) */
    private Integer position;

    protected SituationRule() {
    }

    public SituationRule(String ruleId, Integer category, String situationId, String label, String base, String tools,
                         String better, String cost, String evidenceType, String source, String review, Integer position) {
        this.ruleId = ruleId;
        this.category = category;
        this.situationId = situationId;
        this.label = label;
        this.base = base;
        this.tools = tools;
        this.better = better;
        this.cost = cost;
        this.evidenceType = evidenceType;
        this.source = source;
        this.review = review;
        this.position = position;
    }

    public String getRuleId() { return ruleId; }
    public Integer getCategory() { return category; }
    public String getSituationId() { return situationId; }
    public String getLabel() { return label; }
    public String getBase() { return base; }
    public String getTools() { return tools; }
    public String getBetter() { return better; }
    public String getCost() { return cost; }
    public String getEvidenceType() { return evidenceType; }
    public String getSource() { return source; }
    public String getReview() { return review; }
    public Integer getPosition() { return position; }
}
