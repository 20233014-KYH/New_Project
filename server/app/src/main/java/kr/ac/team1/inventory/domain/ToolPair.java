package kr.ac.team1.inventory.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

/** 저장된 판정 한 건(두 도구의 관계). 출처: sample-data/compat.json */
@Entity
@Table(uniqueConstraints = @UniqueConstraint(columnNames = "pairKey"))
public class ToolPair {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 두 아이디를 정렬해 붙인 키(a|b). (a,b)와 (b,a)를 같은 쌍으로 찾기 위해 */
    @Column(nullable = false)
    private String pairKey;

    @Column(name = "tool_a", nullable = false)
    private String a;

    @Column(name = "tool_b", nullable = false)
    private String b;

    /** overlap / situational / complement / none */
    @Column(nullable = false)
    private String relation;

    /** tested(직접 시험) / human_review(사람 검토) / ai_estimate(AI 추정) */
    private String reviewState;

    @Lob
    private String reason;

    /** 근거 출처 목록(JSON 배열 문자열) */
    @Lob
    private String sourcesJson;

    private String judgedAt;

    protected ToolPair() {
    }

    public ToolPair(String a, String b, String relation, String reviewState, String reason, String sourcesJson, String judgedAt) {
        this.pairKey = PairKeys.of(a, b);
        this.a = a;
        this.b = b;
        this.relation = relation;
        this.reviewState = reviewState;
        this.reason = reason;
        this.sourcesJson = sourcesJson;
        this.judgedAt = judgedAt;
    }

    public Long getId() { return id; }
    public String getPairKey() { return pairKey; }
    public String getA() { return a; }
    public String getB() { return b; }
    public String getRelation() { return relation; }
    public String getReviewState() { return reviewState; }
    public String getReason() { return reason; }
    public String getSourcesJson() { return sourcesJson; }
    public String getJudgedAt() { return judgedAt; }
}
