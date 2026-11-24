package kr.ac.team1.inventory.service;

/** 잘못된 요청(도구 목록 없음, 너무 많음, 카탈로그에 없는 도구) → 400 */
public class BadRequestException extends RuntimeException {
    public BadRequestException(String message) {
        super(message);
    }
}
