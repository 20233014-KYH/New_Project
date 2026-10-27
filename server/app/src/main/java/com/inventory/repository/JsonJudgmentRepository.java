package com.inventory.repository;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.inventory.domain.Judgment;
import com.inventory.domain.PairKey;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Repository;

import java.io.File;
import java.util.*;

@Repository
public class JsonJudgmentRepository implements JudgmentRepository {

    @Value("${inventory.data-dir:../sample-data}")
    private String dataDir;

    private final Map<PairKey, Judgment> byPair = new HashMap<>();
    private final Map<String, List<Judgment>> byTool = new HashMap<>();

    @PostConstruct
    public void load() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        File file = new File(dataDir, "compat.json");
        JsonNode root = mapper.readTree(file);
        JsonNode pairs = root.get("pairs");
        for (JsonNode node : pairs) {
            Judgment j = mapper.treeToValue(node, Judgment.class);
            PairKey key = new PairKey(j.a, j.b);
            byPair.put(key, j);
            byTool.computeIfAbsent(j.a, k -> new ArrayList<>()).add(j);
            byTool.computeIfAbsent(j.b, k -> new ArrayList<>()).add(j);
        }
    }

    @Override
    public Optional<Judgment> findByPair(PairKey key) {
        return Optional.ofNullable(byPair.get(key));
    }

    @Override
    public List<Judgment> findByToolId(String toolId) {
        return byTool.getOrDefault(toolId, Collections.emptyList());
    }
}
