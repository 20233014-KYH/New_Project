package kr.ac.team1.inventory.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Lob;

/** 우리가 직접 시험해서 효과를 확인한 도구(더하기 추천 후보). 출처: web/app/src/data/tested.json */
@Entity
public class TestedTool {

    @Id
    private String tool;

    /** 시험으로 확인한 효과 */
    @Lob
    private String effect;

    /** 주의할 점 */
    @Lob
    private String caution;

    /** 이 작업이면 주의(예: bugfix) */
    private String cautionWork;

    /** 이 셸이면 효과 없음(예: powershell) */
    private String cautionShell;

    /** 시험한 날짜 */
    private String testedOn;

    /** tested.json의 순서(추천 카드 순서를 화면과 같게) */
    private Integer position;

    protected TestedTool() {
    }

    public TestedTool(String tool, String effect, String caution, String cautionWork, String cautionShell, String testedOn, Integer position) {
        this.tool = tool;
        this.effect = effect;
        this.caution = caution;
        this.cautionWork = cautionWork;
        this.cautionShell = cautionShell;
        this.testedOn = testedOn;
        this.position = position;
    }

    public String getTool() { return tool; }
    public String getEffect() { return effect; }
    public String getCaution() { return caution; }
    public String getCautionWork() { return cautionWork; }
    public String getCautionShell() { return cautionShell; }
    public String getTestedOn() { return testedOn; }
    public Integer getPosition() { return position; }
}
