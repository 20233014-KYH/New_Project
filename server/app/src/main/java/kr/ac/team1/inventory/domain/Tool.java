package kr.ac.team1.inventory.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

/** 도구 하나(36개 중 하나). 출처: sample-data/entries.json + desc_en.json + cards_ko.json */
@Entity
public class Tool {

    /** 도구 아이디(예: superpowers). 판정의 a·b와 같은 값 */
    @Id
    private String id;

    @Column(nullable = false)
    private String name;

    private String repo;

    /** 분야 번호 1~6 */
    private Integer category;

    /** GitHub 저장소 설명(영어 원문) */
    @Lob
    private String descEn;

    /** 한국어 한 줄 소개(GitHub 설명 번역, 팀원 확인 전) */
    @Lob
    private String summaryKo;

    /** 한국어 "이럴 때 쓰세요"(허준서 비교 표) */
    @Lob
    private String whenKo;

    private String version;
    private String license;
    private Long stars;

    /** 마지막 업데이트 날짜(YYYY-MM-DD) */
    private String pushedAt;

    /** 처음 읽는 양(토큰, 실측) */
    private Integer tokens;

    /** 역할 범위(스킬·에이전트·명령·MCP·훅 개수) — JSON 그대로 저장 */
    @Lob
    private String scopeJson;

    @Lob
    private String tokenNote;

    private String checkedAt;

    /** entries.json의 순서(목록을 화면과 같은 순서로 보여 주려고) */
    private Integer position;

    protected Tool() {
    }

    public Tool(String id, String name, String repo, Integer category, String descEn, String summaryKo, String whenKo,
                String version, String license, Long stars, String pushedAt, Integer tokens, String scopeJson,
                String tokenNote, String checkedAt, Integer position) {
        this.id = id;
        this.name = name;
        this.repo = repo;
        this.category = category;
        this.descEn = descEn;
        this.summaryKo = summaryKo;
        this.whenKo = whenKo;
        this.version = version;
        this.license = license;
        this.stars = stars;
        this.pushedAt = pushedAt;
        this.tokens = tokens;
        this.scopeJson = scopeJson;
        this.tokenNote = tokenNote;
        this.checkedAt = checkedAt;
        this.position = position;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getRepo() { return repo; }
    public Integer getCategory() { return category; }
    public String getDescEn() { return descEn; }
    public String getSummaryKo() { return summaryKo; }
    public String getWhenKo() { return whenKo; }
    public String getVersion() { return version; }
    public String getLicense() { return license; }
    public Long getStars() { return stars; }
    public String getPushedAt() { return pushedAt; }
    public Integer getTokens() { return tokens; }
    public String getScopeJson() { return scopeJson; }
    public String getTokenNote() { return tokenNote; }
    public String getCheckedAt() { return checkedAt; }
    public Integer getPosition() { return position; }
}
