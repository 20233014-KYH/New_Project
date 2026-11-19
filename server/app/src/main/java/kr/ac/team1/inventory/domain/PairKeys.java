package kr.ac.team1.inventory.domain;

/** 두 도구 아이디를 늘 같은 순서로 붙인다. (a,b)와 (b,a)가 같은 쌍이 되도록. */
public final class PairKeys {

    private PairKeys() {
    }

    public static String of(String a, String b) {
        return a.compareTo(b) <= 0 ? a + "|" + b : b + "|" + a;
    }
}
