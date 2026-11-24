package kr.ac.team1.inventory.web;

import java.util.Map;
import kr.ac.team1.inventory.service.BadRequestException;
import kr.ac.team1.inventory.service.NotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** 오류를 화면이 읽기 쉬운 한국어 메시지로 돌려준다 */
@RestControllerAdvice
public class ApiErrors {

    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<Map<String, String>> notFound(NotFoundException e) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("message", e.getMessage()));
    }

    @ExceptionHandler(kr.ac.team1.inventory.ai.AiDisabledException.class)
    public ResponseEntity<Map<String, String>> aiOff(kr.ac.team1.inventory.ai.AiDisabledException e) {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(Map.of("message", e.getMessage()));
    }

    @ExceptionHandler(BadRequestException.class)
    public ResponseEntity<Map<String, String>> badRequest(BadRequestException e) {
        return ResponseEntity.badRequest().body(Map.of("message", e.getMessage()));
    }
}
