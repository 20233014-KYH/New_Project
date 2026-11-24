package kr.ac.team1.inventory.service;

import java.io.IOException;
import java.io.InputStream;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

/**
 * 겹침 기준(compat.json의 criteria). 빈 세션이 처음 읽는 양의 5%(2026-11-21 Claude Code 2.1.318 기준 1,642토큰).
 * 화면 로컬 모드(api.js의 OVERLAP_MIN)와 같은 파일에서 읽는다. DB에 데이터가 이미 있어도 항상 파일에서 읽는다.
 */
@Component
public class OverlapCriteria {

    private final int minTokens;

    public OverlapCriteria(ObjectMapper mapper) throws IOException {
        try (InputStream in = new ClassPathResource("seed/compat.json").getInputStream()) {
            JsonNode c = mapper.readTree(in).path("criteria").path("overlap_min_tokens");
            this.minTokens = c.isNumber() ? c.asInt() : 0;
        }
    }

    /** 같은 일을 하는 도구를 하나 꺼서 아끼는 양이 이만큼 이상이어야 겹침(빼기 추천) */
    public int minTokens() {
        return minTokens;
    }
}
