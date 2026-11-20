package kr.ac.team1.inventory.ai;

/** 서버 AI가 꺼져 있을 때(키 없음) */
public class AiDisabledException extends RuntimeException {
    public AiDisabledException(String message) {
        super(message);
    }
}
