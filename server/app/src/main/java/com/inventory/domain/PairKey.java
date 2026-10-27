package com.inventory.domain;

import java.util.Objects;

/** (a, b)를 항상 사전순 정렬로 저장해 방향 무관하게 같은 쌍을 찾는 값 객체 */
public final class PairKey {
    public final String first;
    public final String second;

    public PairKey(String x, String y) {
        if (x.compareTo(y) <= 0) {
            this.first = x;
            this.second = y;
        } else {
            this.first = y;
            this.second = x;
        }
    }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof PairKey pk)) return false;
        return first.equals(pk.first) && second.equals(pk.second);
    }

    @Override
    public int hashCode() {
        return Objects.hash(first, second);
    }
}
