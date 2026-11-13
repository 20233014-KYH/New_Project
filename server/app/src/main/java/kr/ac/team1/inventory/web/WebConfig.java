package kr.ac.team1.inventory.web;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/** 화면 개발 서버(Vite, 5173)에서 이 서버를 부를 수 있게 허용 */
@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final String[] origins;

    public WebConfig(@Value("${app.cors.origins}") String[] origins) {
        this.origins = origins;
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        // 패턴으로 받는다(예: http://localhost:[*] = 내 컴퓨터의 아무 포트). 화면 포트가 5173이 아닐 때도 열리게
        registry.addMapping("/api/**").allowedOriginPatterns(origins).allowedMethods("GET", "POST");
    }
}
