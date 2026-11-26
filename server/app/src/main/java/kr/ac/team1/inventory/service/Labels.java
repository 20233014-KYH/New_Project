package kr.ac.team1.inventory.service;

import java.util.Map;

/** 화면에 보이는 한국어 이름(로컬 모드 api.js의 KO·RS와 같음) */
final class Labels {

    static final Map<String, String> RELATION = Map.of(
            "overlap", "겹침", "situational", "상황따라", "complement", "보완", "none", "관계 없음");
    static final Map<String, String> REVIEW = Map.of(
            "tested", "직접 시험", "human_review", "사람 검토", "ai_estimate", "AI 추정");
    static final Map<String, String> PRIORITY = Map.of(
            "accurate", "틀리지 않는 것", "quality", "결과 품질", "save", "토큰·한도 아끼기", "simple", "설치·관리가 간단한 것", "safe", "실수로 망가뜨리지 않는 것", "fast", "빨리 끝내기");
    /** 중요한 것 보여 주는 순서 */
    static final java.util.List<String> PRIORITY_ORDER = java.util.List.of("accurate", "quality", "save", "fast", "simple", "safe");
    static final String NO_INFO = "확인된 정보 없음";

    private Labels() {
    }
}
