package com.inventory.repository;

import com.inventory.domain.Judgment;
import com.inventory.domain.PairKey;
import java.util.List;
import java.util.Optional;

public interface JudgmentRepository {
    Optional<Judgment> findByPair(PairKey key);
    List<Judgment> findByToolId(String toolId);
}
