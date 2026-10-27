package com.inventory;

import com.inventory.domain.PairKey;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PairKeyTest {

    @Test
    void sameRegardlessOfOrder() {
        PairKey ab = new PairKey("superpowers", "ecc");
        PairKey ba = new PairKey("ecc", "superpowers");
        assertEquals(ab, ba);
        assertEquals(ab.hashCode(), ba.hashCode());
    }
}
