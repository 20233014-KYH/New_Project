package kr.ac.team1.inventory.service;

/** 없는 도구·저장되지 않은 판정 → 404 */
public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) {
        super(message);
    }
}
