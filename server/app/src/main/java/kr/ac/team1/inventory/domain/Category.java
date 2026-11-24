package kr.ac.team1.inventory.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;

/** 분야 6개(기획·작업 방식 … QA·테스트). 화면의 분야 카드 한 장. */
@Entity
public class Category {

    @Id
    private Integer id;

    @Column(nullable = false)
    private String name;

    /** 한 줄 설명 */
    private String description;

    /** "이럴 때 찾으세요" 예시 */
    @Column(name = "when_text")
    private String when;

    protected Category() {
    }

    public Category(Integer id, String name, String description, String when) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.when = when;
    }

    public Integer getId() { return id; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public String getWhen() { return when; }
}
